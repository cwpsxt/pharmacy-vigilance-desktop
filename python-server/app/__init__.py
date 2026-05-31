import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from .db import db
from .auth import auth_bp, ensure_seed_admin
from .license import license_bp, license_manager


def get_app_root():
    """获取应用根目录（用于只读资源如 static/）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_user_data_dir():
    """获取可写的用户数据目录

    打包后不能用安装目录（C:\\Program Files\\... 普通用户无写权限），
    必须用 AppData/Local 这种用户专属目录。
    """
    if getattr(sys, 'frozen', False):
        # 打包后：Windows 用 LOCALAPPDATA，其他平台用 HOME
        if sys.platform == "win32":
            base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        elif sys.platform == "darwin":
            base = os.path.expanduser("~/Library/Application Support")
        else:
            base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        return os.path.join(base, "PharmacyVigilance")
    # 开发环境：仍用项目目录，方便调试
    return get_app_root()


def create_app() -> Flask:
    app_root = get_app_root()
    user_data_root = get_user_data_dir()
    static_folder = os.path.join(app_root, "static")

    app = Flask(__name__, static_folder=static_folder, static_url_path="/static")

    # 安全配置
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "adr-desktop-client-secret-key")

    # Session cookie 配置（支持跨域）
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    # SQLite 数据库放在可写的用户目录下
    data_dir = os.path.join(user_data_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    db_path = os.path.join(data_dir, "database.sqlite3")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # 上传目录同样放可写目录
    upload_dir = os.path.join(user_data_root, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_dir

    print(f"[INIT] Data dir: {data_dir}", flush=True)
    print(f"[INIT] Upload dir: {upload_dir}", flush=True)

    # 初始化扩展
    db.init_app(app)
    CORS(app, supports_credentials=True)

    # 注册蓝图
    app.register_blueprint(license_bp, url_prefix="/api/license")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from .data import data_bp
    app.register_blueprint(data_bp, url_prefix="/api/data")

    from .workload import workload_bp
    app.register_blueprint(workload_bp, url_prefix="/api/workload")

    from .drug_category import drug_category_bp
    app.register_blueprint(drug_category_bp, url_prefix="/api")

    from .ai import ai_bp
    app.register_blueprint(ai_bp, url_prefix="/api/ai")

    # 创建数据库表和种子数据
    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()
        ensure_seed_admin()

    # 健康检查接口（供 Electron 检测服务是否启动）
    @app.route("/api/health")
    def health_check():
        return jsonify({"status": "ok", "message": "服务运行正常"})

    @app.before_request
    def enforce_license():
        path = request.path or ""
        if not path.startswith("/api/"):
            return None
        if path == "/api/health" or path.startswith("/api/license/"):
            return None
        if not license_manager.is_valid():
            status = license_manager.get_status()
            return jsonify({
                "code": "LICENSE_REQUIRED",
                "message": "软件未授权或授权已过期，请先激活",
                "status": status,
            }), 403
        return None

    # 首页
    @app.route("/")
    def index():
        from flask import send_from_directory
        return send_from_directory(static_folder, "index.html")
    
    # 管理页面
    @app.route("/admin")
    def admin():
        from flask import send_from_directory
        return send_from_directory(static_folder, "admin.html")

    return app
