import os
from pathlib import Path
from typing import Final

# <repo root>/instance
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
INSTANCE_DIR: Final[Path] = PROJECT_ROOT / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}

def _normalise_sqlite_uri(uri: str) -> str:
    """
    If uri is a relative sqlite URL like sqlite:///instance/app.db,
    rewrite it to an absolute path under PROJECT_ROOT.
    Works on Windows and POSIX.
    """
    prefix = "sqlite:///"
    if not uri.startswith(prefix):
        return uri

    raw = uri[len(prefix):].replace("\\", "/")  # normalise slashes
    # Windows absolute if it looks like C:/... ; POSIX absolute if startswith '/'
    is_abs = raw.startswith("/") or (len(raw) >= 2 and raw[1] == ":")

    if is_abs:
        abs_path = Path(raw)
    else:
        abs_path = (PROJECT_ROOT / raw).resolve()

    abs_path.parent.mkdir(parents=True, exist_ok=True)
    return f"{prefix}{abs_path.as_posix()}"

DEFAULT_SQLITE = f"sqlite:///{(INSTANCE_DIR / 'app.db').as_posix()}"

class Config:
    # Core
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")

    # Pull env first, then normalise if needed
    _raw_db = os.getenv("DATABASE_URL", DEFAULT_SQLITE)
    SQLALCHEMY_DATABASE_URI = _normalise_sqlite_uri(_raw_db)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # App-specific
    AWARD_IMAGE_BASE = os.getenv("AWARD_IMAGE_BASE", "/static/awards")

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", False)

    # CSRF
    WTF_CSRF_ENABLED = _bool("WTF_CSRF_ENABLED", True)

class DevConfig(Config):
    DEBUG = True

class ProdConfig(Config):
    DEBUG = False

CONFIG_MAP = {
    "development": DevConfig,
    "production": ProdConfig,
}

# Re-export for app factory
INSTANCE_PATH = str(INSTANCE_DIR)
