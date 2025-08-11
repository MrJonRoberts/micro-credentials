from functools import wraps
from flask import abort
from flask_login import login_required, current_user

def roles_required(*role_names: str):
    """Require the current user to have at least one of the given roles."""
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if not getattr(current_user, "has_role", None) or not current_user.has_role(*role_names):
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
