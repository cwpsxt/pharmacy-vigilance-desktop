#!/usr/bin/env python3
"""激活码生成 Web 小应用（厂商本地使用，勿对外公开部署）。"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session

TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parent
sys.path.insert(0, str(ROOT / "python-server"))
sys.path.insert(0, str(TOOLS_DIR))

from license_generator import PrivateKeyNotFoundError, generate_activation  # noqa: E402

app = Flask(
    __name__,
    template_folder=str(TOOLS_DIR / "license_admin_templates"),
    static_folder=str(TOOLS_DIR / "license_admin_static"),
)
app.secret_key = os.environ.get("LICENSE_ADMIN_SECRET", "license-admin-local-secret")


def _admin_password() -> str:
    return os.environ.get("LICENSE_ADMIN_PASSWORD", "").strip()


def require_admin(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        password = _admin_password()
        if password and not session.get("authenticated"):
            return jsonify({"message": "请先登录"}), 401
        return f(*args, **kwargs)

    return wrapped


@app.route("/")
def index():
    default_expire = (date.today() + timedelta(days=365)).isoformat()
    return render_template(
        "index.html",
        require_login=bool(_admin_password()),
        authenticated=session.get("authenticated", False),
        default_expire=default_expire,
        product_id="pharmacy-vigilance",
    )


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    password = (data.get("password") or "").strip()
    expected = _admin_password()
    if not expected:
        session["authenticated"] = True
        return jsonify({"message": "无需登录"})
    if password != expected:
        return jsonify({"message": "密码错误"}), 401
    session["authenticated"] = True
    return jsonify({"message": "登录成功"})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "已退出"})


@app.route("/api/generate", methods=["POST"])
@require_admin
def generate():
    data = request.get_json(silent=True) or {}
    machine_id = (data.get("machine_id") or "").strip().upper()
    expire = (data.get("expire") or "").strip()

    if not machine_id:
        return jsonify({"message": "请输入机器码"}), 400
    if len(machine_id) != 32 or not all(c in "0123456789ABCDEF" for c in machine_id):
        return jsonify({"message": "机器码应为 32 位十六进制字符"}), 400
    if not expire:
        return jsonify({"message": "请选择到期日"}), 400

    try:
        date.fromisoformat(expire)
    except ValueError:
        return jsonify({"message": "到期日格式无效，请使用 YYYY-MM-DD"}), 400

    try:
        result = generate_activation(machine_id, expire)
    except PrivateKeyNotFoundError as exc:
        return jsonify({"message": str(exc)}), 500
    except Exception as exc:
        return jsonify({"message": f"生成失败: {exc}"}), 500

    return jsonify({
        "message": "激活码生成成功",
        "machine_id": result["machine_id"],
        "expire": result["expire"],
        "code": result["code"],
    })


@app.route("/api/health")
def health():
    key_exists = (TOOLS_DIR / "private_key.pem").exists()
    return jsonify({
        "status": "ok",
        "private_key_ready": key_exists,
        "require_login": bool(_admin_password()),
    })


def main() -> None:
    host = os.environ.get("LICENSE_ADMIN_HOST", "127.0.0.1")
    port = int(os.environ.get("LICENSE_ADMIN_PORT", "5050"))
    print("=" * 50)
    print("激活码生成 Web 工具（厂商专用）")
    print(f"访问地址: http://{host}:{port}")
    if host != "127.0.0.1":
        print("警告: 当前非本机绑定，请确保仅在内网可信环境使用")
    if not (TOOLS_DIR / "private_key.pem").exists():
        print("未找到 private_key.pem，请先运行: python tools/generate_keypair.py")
    print("=" * 50)
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
