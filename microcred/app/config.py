import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE = f"sqlite:///{BASE_DIR / 'instance' / 'app.db'}"

class Config:
    # Core
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", DEFAULT_SQLITE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # App-specific
    AWARD_IMAGE_BASE = os.getenv("AWARD_IMAGE_BASE", "/static/awards")

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") in {"1", "true", "True"}

    # CSRF (enable if you’re using Flask‑WTF forms)
    WTF_CSRF_ENABLED = os.getenv("WTF_CSRF_ENABLED", "1") in {"1", "true", "True"}

class DevConfig(Config):
    DEBUG = True

class ProdConfig(Config):
    DEBUG = False

# Optional helper so you can point FLASK_ENV or APP_ENV at a config
CONFIG_MAP = {
    "development": DevConfig,
    "production": ProdConfig,
}
