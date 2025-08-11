from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from ..models import Award, Achievement

bp = Blueprint("participants", __name__, url_prefix="/me")

@bp.get("/awards")
@login_required
def my_awards():
    achs = (Achievement.query
            .filter_by(participant_id=current_user.id)
            .join(Award)
            .order_by(Achievement.issued_at.desc())
            .all())
    return render_template(
        "participant/awards_list.html",
        achievements=achs,
        img_base=current_app.config.get("AWARD_IMAGE_BASE", "/static/awards")
    )

@bp.get("/awards/<slug>")
@login_required
def my_award_detail(slug: str):
    ach = (Achievement.query
           .join(Award)
           .filter(Award.slug == slug, Achievement.participant_id == current_user.id)
           .first_or_404())
    return render_template(
        "participant/award_detail.html",
        ach=ach,
        img_base=current_app.config.get("AWARD_IMAGE_BASE", "/static/awards")
    )

@bp.get("/achievable")
@login_required
def achievable():
    have_ids = {a.award_id for a in current_user.achievements}  # type: ignore[attr-defined]
    awards = Award.query.filter(~Award.id.in_(have_ids)).order_by(Award.points.desc()).all()
    return render_template(
        "participant/awards_list.html",
        achievable=awards,
        img_base=current_app.config.get("AWARD_IMAGE_BASE", "/static/awards")
    )
