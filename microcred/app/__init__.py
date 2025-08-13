from flask import Flask
from flask_login import LoginManager, current_user
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

    # --- NEW: template helper ---
    @app.context_processor
    def inject_role_helpers():
        def has_role(*names: str) -> bool:
            if not getattr(current_user, "is_authenticated", False):
                return False
            user_roles = {r.name for r in getattr(current_user, "roles", [])}
            return any(name in user_roles for name in names)

        return {"has_role": has_role}

    # ----------------------------
    @app.template_filter('date_short')
    def date_short(value):
        if not value:
            return ''
        for fmt in ('%-d %b %Y', '%#d %b %Y', '%d %b %Y'):
            try:
                s = value.strftime(fmt)
                if fmt == '%d %b %Y':  # strip leading zero if we had to use %d
                    s = s.lstrip('0')
                return s
            except ValueError:
                continue
        return value.date().isoformat()

    #template global
    @app.template_global()
    def icon_url(category, filename):
        return f"/static/Icons/{category}/{filename}"

    # Create tables if they don't exist
    # with app.app_context():
    #     db.create_all()
    # Register blueprints
    from .routes import auth, participants, issuers, admin, api, main, icon_routes
    app.register_blueprint(auth.bp)
    app.register_blueprint(participants.bp)
    app.register_blueprint(issuers.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(icon_routes.icons_bp)

    return app
