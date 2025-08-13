# run.py
import os
from microcred.app import create_app
from microcred.app.config import CONFIG_MAP  # for DEBUG default per env

def _to_bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.lower() in {"1", "true", "yes", "on"}

def build_app():
    env_name = os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "development"
    app = create_app(env_name)

    # Show where things are, to avoid SQLite path surprises
    print(f"ENV: {env_name}")
    print(f"Instance path: {app.instance_path}")
    print(f"DB URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")


    return app, env_name

if __name__ == "__main__":
    app, env_name = build_app()

    # Host/port/debug from env, with per-env DEBUG as fallback
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))

    # If FLASK_DEBUG is set, it wins; otherwise use the config class default
    cfg_cls = CONFIG_MAP.get(env_name, CONFIG_MAP["development"])
    debug = _to_bool(os.getenv("FLASK_DEBUG"), getattr(cfg_cls, "DEBUG", False))

    # In debug, enable the reloader; otherwise keep it off
    app.run(host=host, port=port, debug=debug, use_reloader=debug)
