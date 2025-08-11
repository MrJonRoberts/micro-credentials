"""
WSGI entrypoint for production (e.g. gunicorn or waitress).
Gunicorn example:
    gunicorn -w 4 -b 0.0.0.0:8000 microcred.app.wsgi:app
"""
import os
from . import create_app
from .config import CONFIG_MAP, Config

# Choose config class based on APP_ENV/FLASK_ENV; fall back to Config
env = os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "production"
config_cls = CONFIG_MAP.get(env, Config)

app = create_app()
# If you want to apply env-specific class at runtime, you could:
# app.config.from_object(config_cls)
# but create_app() already loads Config; adjust there if you prefer.
