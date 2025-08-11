from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect

# Initialise extensions (app binds in create_app())
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# Optional: basic login manager defaults
login_manager.login_view = "auth.login"
login_manager.session_protection = "strong"
