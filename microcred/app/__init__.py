from flask import Flask
from pathlib import Path
from .config import CONFIG_MAP, INSTANCE_DIR  # we'll export INSTANCE_DIR from config.py
from .extensions import db, migrate, login_manager, csrf

def create_app(env_name: str | None = None) -> Flask:
    """
    Application factory: sets a fixed absolute instance_path so
    the database and other instance files are always in <repo>/instance.
    """
    app = Flask(
        __name__,
        instance_path=str(INSTANCE_DIR),      # absolute path from config.py
        instance_relative_config=True
    )

    # Select config class from CONFIG_MAP based on env_name or Flask ENV
    config_class = CONFIG_MAP.get(env_name or app.config.get("ENV", "development"))
    app.config.from_object(config_class)

    # Ensure the instance folder exists (belt-and-braces)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # Initialise extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from .routes import auth, participants, issuers, admin, api, main
    app.register_blueprint(auth.bp)
    app.register_blueprint(participants.bp)
    app.register_blueprint(issuers.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(main.bp)

    return app
