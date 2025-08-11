from flask import Blueprint, render_template
from ._utils import roles_required
from ..models import User, Award, Achievement

bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.get("/")
@roles_required("admin")
def dashboard():
    return render_template(
        "admin/dashboard.html",
        users_count=User.query.count(),
        awards_count=Award.query.count(),
        achievements_count=Achievement.query.count(),
    )
