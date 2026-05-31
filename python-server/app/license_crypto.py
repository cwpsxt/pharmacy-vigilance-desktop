"""离线激活码加解密与验签（Ed25519 + Base32）。"""

from __future__ import annotations

import base64
import hashlib
import json
import platform
import uuid
from datetime import date
from typing import Optional, Tuple

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

PRODUCT_ID = "pharmacy-vigilance"

# 由 tools/generate_keypair.py 生成后写入；客户端仅含公钥
PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAg8v2ufd9aYqqWibND21+vNJJqkKXnlUcnJ6RvPIdDZQ=
-----END PUBLIC KEY-----
"""


def get_machine_id() -> str:
    """基于稳定硬件特征生成本机机器码。"""
    parts = [
        platform.node(),
        str(uuid.getnode()),
        platform.system(),
        platform.machine(),
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:32].upper()


def _b32_encode(data: bytes) -> str:
    return base64.b32encode(data).decode("ascii").rstrip("=")


def _b32_decode(value: str) -> bytes:
    clean = value.replace("-", "").replace(" ", "").upper()
    padding = (8 - len(clean) % 8) % 8
    return base64.b32decode(clean + ("=" * padding))


def format_activation_code(raw: str) -> str:
    """将原始码格式化为 XXXX-XXXX-...，保留分段点号。"""
    segments = raw.split(".")
    formatted = []
    for segment in segments:
        clean = segment.replace("-", "").upper()
        formatted.append("-".join(clean[i : i + 4] for i in range(0, len(clean), 4)))
    return ".".join(formatted)


def normalize_activation_code(code: str) -> str:
    code = code.strip().upper()
    parts = code.replace(" ", "").split(".")
    return ".".join(part.replace("-", "") for part in parts)


def build_payload(machine_id: str, expire_date: str, issued_at: Optional[str] = None) -> dict:
    return {
        "pid": PRODUCT_ID,
        "mid": machine_id.upper(),
        "exp": expire_date,
        "iat": issued_at or date.today().isoformat(),
    }


def create_license_code(private_key_pem: bytes, machine_id: str, expire_date: str) -> str:
    payload = build_payload(machine_id, expire_date)
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    if not isinstance(private_key, Ed25519PrivateKey):
        raise ValueError("私钥必须是 Ed25519 格式")

    signature = private_key.sign(payload_bytes)
    raw = f"{_b32_encode(payload_bytes)}.{_b32_encode(signature)}"
    return format_activation_code(raw)


def verify_license_code(
    code: str,
    machine_id: str,
    public_key_pem: bytes = PUBLIC_KEY_PEM,
    *,
    check_expiry: bool = True,
) -> Tuple[bool, Optional[dict], str]:
    try:
        normalized = normalize_activation_code(code)
        if "." not in normalized:
            return False, None, "激活码格式无效"

        payload_part, sig_part = normalized.split(".", 1)
        payload_bytes = _b32_decode(payload_part)
        signature = _b32_decode(sig_part)

        public_key = serialization.load_pem_public_key(public_key_pem)
        public_key.verify(signature, payload_bytes)

        payload = json.loads(payload_bytes.decode("utf-8"))

        if payload.get("pid") != PRODUCT_ID:
            return False, None, "激活码产品不匹配"

        if payload.get("mid") != machine_id.upper():
            return False, None, "激活码与本机不匹配"

        if check_expiry:
            exp_str = payload.get("exp", "")
            exp_date = date.fromisoformat(exp_str)
            if date.today() > exp_date:
                return False, payload, "激活码已过期"

        return True, payload, ""
    except Exception as exc:
        return False, None, f"激活码验证失败: {exc}"
