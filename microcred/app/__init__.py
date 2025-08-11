# microcred/app/__init__.py
import os
from pathlib import Path
from flask import Flask

try:
    from .extensions import db, migrate, login_manager, csrf
except Exception as e:
    raise RuntimeError("extensions.py must define db, migrate, login_manager, csrf") from e

try:
    from .config import Config  # type: ignore
except Exception:
    class Config:
        SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///microcred/instance/app.db")
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        AWARD_IMAGE_BASE = os.getenv("AWARD_IMAGE_BASE", "/static/awards")
        WTF_CSRF_ENABLED = True

def create_app() -> Flask:
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="static",
        template_folder="templates",
    )
    app.config.from_object(Config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    csrf.init_app(app)  # <-- CSRF enabled globally (protects all POST/PUT/PATCH/DELETE)

    # Make csrf_token() available in Jinja (for plain HTML forms)
    from flask_wtf.csrf import generate_csrf
    @app.context_processor
    def inject_csrf():
        return {"csrf_token": lambda: generate_csrf()}

    # Register blueprints if present
    def _register(module_path: str):
        try:
            mod = __import__(module_path, fromlist=["bp"])
            bp = getattr(mod, "bp", None)
            if bp is not None:
                app.register_blueprint(bp)
        except Exception:
            pass

    _register("microcred.app.routes.auth")
    _register("microcred.app.routes.participants")
    _register("microcred.app.routes.issuers")
    _register("microcred.app.routes.admin")
    _register("microcred.app.routes.api")

    @app.get("/")
    def health():
        return {"status": "ok", "app": "microcred"}

    return app
