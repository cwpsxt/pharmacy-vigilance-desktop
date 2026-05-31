"""软件授权：机器码、激活码验签、本地 license.dat 持久化。"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import date, datetime, timezone
from typing import Any, Optional

from cryptography.fernet import Fernet
from flask import Blueprint, jsonify, request

from .license_crypto import (
    get_machine_id,
    normalize_activation_code,
    verify_license_code,
)

license_bp = Blueprint("license", __name__)

LICENSE_FILENAME = "license.dat"
LICENSE_FILE_SECRET = "pharmacy-vigilance-license-v1"


def _license_skip_enabled() -> bool:
    return os.environ.get("SKIP_LICENSE", "").strip() in {"1", "true", "yes"}


def _license_file_path() -> str:
    from . import get_user_data_dir

    data_dir = os.path.join(get_user_data_dir(), "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, LICENSE_FILENAME)


def _fernet_key() -> bytes:
    raw = f"{LICENSE_FILE_SECRET}:{get_machine_id()}".encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return base64.urlsafe_b64encode(digest)


def _encrypt_record(record: dict) -> bytes:
    return Fernet(_fernet_key()).encrypt(json.dumps(record, ensure_ascii=False).encode("utf-8"))


def _decrypt_record(data: bytes) -> dict:
    return json.loads(Fernet(_fernet_key()).decrypt(data).decode("utf-8"))


class LicenseManager:
    """授权状态管理。"""

    def load_record(self) -> Optional[dict]:
        path = _license_file_path()
        if not os.path.exists(path):
            return None
        try:
            with open(path, "rb") as fp:
                return _decrypt_record(fp.read())
        except Exception:
            return None

    def save_record(self, record: dict) -> None:
        path = _license_file_path()
        tmp_path = f"{path}.tmp"
        with open(tmp_path, "wb") as fp:
            fp.write(_encrypt_record(record))
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(tmp_path, path)

    def clear_record(self) -> None:
        path = _license_file_path()
        if os.path.exists(path):
            os.remove(path)

    def activate(self, code: str) -> tuple[bool, str, Optional[dict]]:
        machine_id = get_machine_id()
        normalized = normalize_activation_code(code)
        ok, payload, message = verify_license_code(normalized, machine_id, check_expiry=True)
        if not ok or not payload:
            return False, message or "激活失败", None

        now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
        record = {
            "machine_id": machine_id,
            "expire_at": payload["exp"],
            "activated_at": now,
            "license_code": normalized,
            "last_check_at": now,
        }
        self.save_record(record)
        return True, "激活成功", payload

    def get_status(self) -> dict[str, Any]:
        if _license_skip_enabled():
            return {
                "activated": True,
                "valid": True,
                "machine_id": get_machine_id(),
                "expire_at": None,
                "days_left": None,
                "reason": "development_skip",
                "skipped": True,
            }

        machine_id = get_machine_id()
        record = self.load_record()
        if not record:
            return {
                "activated": False,
                "valid": False,
                "machine_id": machine_id,
                "expire_at": None,
                "days_left": None,
                "reason": "not_activated",
            }

        if record.get("machine_id") != machine_id:
            return {
                "activated": True,
                "valid": False,
                "machine_id": machine_id,
                "expire_at": record.get("expire_at"),
                "days_left": None,
                "reason": "machine_mismatch",
            }

        stored_code = record.get("license_code", "")
        ok, payload, message = verify_license_code(stored_code, machine_id, check_expiry=True)
        if not ok:
            return {
                "activated": True,
                "valid": False,
                "machine_id": machine_id,
                "expire_at": payload.get("exp") if payload else record.get("expire_at"),
                "days_left": 0,
                "reason": "expired" if message == "激活码已过期" else "invalid",
                "message": message,
            }

        expire_at = payload["exp"]
        days_left = (date.fromisoformat(expire_at) - date.today()).days

        now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
        last_check = record.get("last_check_at")
        if last_check and now < last_check:
            return {
                "activated": True,
                "valid": False,
                "machine_id": machine_id,
                "expire_at": expire_at,
                "days_left": days_left,
                "reason": "clock_rollback",
            }

        record["last_check_at"] = now
        record["expire_at"] = expire_at
        self.save_record(record)

        return {
            "activated": True,
            "valid": True,
            "machine_id": machine_id,
            "expire_at": expire_at,
            "days_left": days_left,
            "reason": "ok",
        }

    def is_valid(self) -> bool:
        return bool(self.get_status().get("valid"))


license_manager = LicenseManager()


@license_bp.route("/machine-id", methods=["GET"])
def machine_id():
    return jsonify({"machine_id": get_machine_id()})


@license_bp.route("/status", methods=["GET"])
def status():
    return jsonify(license_manager.get_status())


@license_bp.route("/activate", methods=["POST"])
def activate():
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    if not code:
        return jsonify({"message": "请输入激活码"}), 400

    ok, message, payload = license_manager.activate(code)
    if not ok:
        return jsonify({"message": message}), 400

    status_data = license_manager.get_status()
    return jsonify({
        "message": message,
        "expire_at": payload.get("exp") if payload else status_data.get("expire_at"),
        "status": status_data,
    })
