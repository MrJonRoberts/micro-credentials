from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user, login_required
from ..extensions import db
from ..models import Award, User, Achievement
from ._utils import roles_required

bp = Blueprint("issuers", __name__, url_prefix="/issuers")

@bp.get("/awardable")
@login_required
@roles_required("issuer", "admin")
def awardable_list():
    awards = Award.query.order_by(Award.points.desc(), Award.name.asc()).all()
    return render_template(
        "issuer/awardable_list.html",
        awards=awards,
        img_base=current_app.config.get("AWARD_IMAGE_BASE", "/static/awards")
    )

@bp.post("/award")
@login_required
@roles_required("issuer", "admin")
def award_post():
    try:
        participant_id = int(request.form["participant_id"])
        award_id = int(request.form["award_id"])
    except (KeyError, ValueError):
        flash("Participant and award are required", "warning")
        return redirect(url_for("issuers.awardable_list"))

    if Achievement.query.filter_by(participant_id=participant_id, award_id=award_id).first():
        flash("Participant already has this award", "info")
        return redirect(url_for("issuers.awardable_list"))

    ach = Achievement(
        participant_id=participant_id,
        award_id=award_id,
        issued_by_id=current_user.id,
        note=request.form.get("note", "")
    )
    db.session.add(ach)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash("Could not grant award, please try again", "danger")
        return redirect(url_for("issuers.awardable_list"))

    flash("Award granted", "success")
    return redirect(url_for("issuers.awardable_list"))

@bp.get("/issued")
@roles_required("issuer", "admin")
def issued_lists():
    achievements = (Achievement.query
                    .join(User, Achievement.participant_id == User.id)
                    .join(Award)
                    .order_by(Award.points.desc(), User.last_name.asc(), User.first_name.asc())
                    .all())
    return render_template(
        "issuer/issued_awards.html",
        achievements=achievements,
        img_base=current_app.config.get("AWARD_IMAGE_BASE", "/static/awards")
    )
