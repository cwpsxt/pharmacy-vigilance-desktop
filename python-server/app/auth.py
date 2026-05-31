import os
import secrets
from typing import Optional
from flask import Blueprint, request, jsonify, session, g
import bcrypt
from .db import db
from .models import User

auth_bp = Blueprint("auth", __name__)

# 简单的 token 存储（生产环境应使用 Redis）
_tokens = {}


def _get_env_admin_credentials() -> tuple[str, str]:
    username = os.environ.get("ADMIN_USERNAME", "admin")
    password = os.environ.get("ADMIN_PASSWORD", "admin")
    return username, password


def ensure_seed_admin() -> None:
    username, password = _get_env_admin_credentials()
    existing: Optional[User] = User.query.filter_by(username=username).first()
    if existing is None:
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user = User(username=username, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()


def get_current_user() -> Optional[User]:
    """获取当前用户（支持 session、header token 和 URL token 三种方式）"""
    # 1. 先检查 Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        user_id = _tokens.get(token)
        if user_id:
            return db.session.get(User, user_id)
    
    # 2. 检查 URL 参数中的 token
    url_token = request.args.get('token', '')
    if url_token:
        user_id = _tokens.get(url_token)
        if user_id:
            return db.session.get(User, user_id)
    
    # 3. 最后检查 session
    user_id = session.get("user_id")
    if user_id:
        return db.session.get(User, user_id)
    
    return None


def require_auth(f):
    """认证装饰器"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"code": 401, "message": "未授权，请先登录"}), 401
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "")
    if not username or not password:
        return jsonify({"message": "用户名和密码不能为空"}), 400

    user: Optional[User] = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "用户不存在或密码错误"}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash):
        return jsonify({"message": "用户不存在或密码错误"}), 401

    # 生成 token
    token = secrets.token_hex(32)
    _tokens[token] = user.id
    
    # 同时设置 session（兼容）
    session["user_id"] = user.id
    
    return jsonify({
        "message": "登录成功", 
        "user": user.to_safe_dict(),
        "token": token
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "已退出登录"})


@auth_bp.route("/me", methods=["GET"])
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False}), 200
    user: Optional[User] = db.session.get(User, user_id)
    if not user:
        return jsonify({"authenticated": False}), 200
    return jsonify({"authenticated": True, "user": user.to_safe_dict()})


@auth_bp.route("/change-password", methods=["POST"])
def change_password():
    """修改用户密码"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "用户未登录"}), 401
    
    user: Optional[User] = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "用户不存在"}), 404
    
    data = request.get_json(silent=True) or {}
    current_password = (data.get("currentPassword") or "")
    new_password = (data.get("newPassword") or "")
    
    if not current_password or not new_password:
        return jsonify({"message": "当前密码和新密码不能为空"}), 400
    
    # 验证当前密码
    if not bcrypt.checkpw(current_password.encode("utf-8"), user.password_hash):
        return jsonify({"message": "当前密码不正确"}), 400
    
    # 验证新密码长度
    if len(new_password) < 6:
        return jsonify({"message": "新密码长度不能少于6位"}), 400
    
    # 检查新密码是否与当前密码相同
    if bcrypt.checkpw(new_password.encode("utf-8"), user.password_hash):
        return jsonify({"message": "新密码不能与当前密码相同"}), 400
    
    try:
        # 更新密码
        new_password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
        user.password_hash = new_password_hash
        db.session.commit()
        
        return jsonify({"message": "密码修改成功"})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"密码修改失败: {str(e)}"}), 500
