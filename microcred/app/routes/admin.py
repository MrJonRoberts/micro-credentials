
from ..models import User, Award, Achievement
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import Award
from ._utils import roles_required
from .forms import AwardForm, slugify

from .forms import AwardEditForm, slugify
from ..services.storage_services import (
    save_award_icon, delete_award_icon, award_img_url, rename_icon_if_slug_changed )

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

@bp.route("/awards/new", methods=["GET", "POST"])
@login_required
@roles_required("admin", "issuer")
def award_create():
    form = AwardForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        slug = (form.slug.data or slugify(name)).strip()
        if Award.query.filter_by(slug=slug).first():
            flash("That slug is already in use.", "warning")
            return render_template("admin/award_form.html", form=form)

        award = Award(
            name=name,
            slug=slug,
            description=(form.description.data or "").strip(),
            points=form.points.data or 0,
        )

        if form.icon.data:
            try:
                fn = save_award_icon(form.icon.data, slug, max_size=(256, 256))
                award.icon_filename = fn
            except Exception as e:
                flash("Could not process icon image.", "danger")
                return render_template("admin/award_form.html", form=form)

        db.session.add(award)
        db.session.commit()
        flash("Award created.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/award_form.html", form=form)


@bp.get("/awards")
@login_required
@roles_required("admin", "issuer")
def award_list():
    awards = Award.query.order_by(Award.points.desc(), Award.name.asc()).all()
    return render_template("admin/award_list.html", awards=awards,
                           img_base=current_app.config.get("AWARD_IMAGE_BASE", "/static/awards"))

@bp.route("/awards/<int:award_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "issuer")
def award_edit(award_id: int):
    award = Award.query.get_or_404(award_id)
    old_slug = award.slug or ""

    form = AwardEditForm(obj=award)
    if form.validate_on_submit():
        # update core fields
        award.name = form.name.data.strip()
        award.slug = (form.slug.data or slugify(award.name)).strip()
        award.description = (form.description.data or "").strip()
        award.points = form.points.data or 0

        # icon removal
        if form.remove_icon.data:
            delete_award_icon(award.image_filename)
            award.image_filename = None

        # icon replacement
        file = form.icon.data
        if file:
            # new upload replaces existing file
            filename = save_award_icon(file, award.slug, max_size=(256, 256))
            # if replacing and old existed and filename changed, optionally delete old
            if award.image_filename and award.image_filename != filename:
                delete_award_icon(award.image_filename)
            award.image_filename = filename
        else:
            # no new upload; if slug changed, try to rename the old file to match
            if award.image_filename:
                award.image_filename = rename_icon_if_slug_changed(
                    award.image_filename, old_slug, award.slug
                )

        db.session.commit()
        flash("Award updated.", "success")
        return redirect(url_for("admin.award_list"))

    # Prepopulate slug if empty so the user sees what will be used
    if request.method == "GET" and not form.slug.data:
        form.slug.data = award.slug or slugify(award.name)

    icon_url = award_img_url(award.image_filename)
    return render_template("admin/award_edit.html", form=form, award=award, icon_url=icon_url)

# --- USERS ---

@bp.get("/users")
@roles_required("admin")
def user_list():
    q = request.args.get("q", "").strip()
    users = User.query
    if q:
        like = f"%{q}%"
        users = users.filter(db.or_(User.email.ilike(like),
                                    User.first_name.ilike(like),
                                    User.last_name.ilike(like)))
    users = users.order_by(User.first_name.asc(), User.last_name.asc(), User.email.asc()).all()
    return render_template("admin/user_list.html", users=users)

@bp.route("/users/<int:user_id>", methods=["GET", "POST"])
@roles_required("admin")
def user_detail(user_id: int):
    user = User.query.get_or_404(user_id)

    # Save basic fields + roles
    if request.method == "POST" and request.form.get("action") == "save_user":
        user.first_name = (request.form.get("first_name") or "").strip()
        user.last_name = (request.form.get("last_name") or "").strip()
        new_email = (request.form.get("email") or "").strip()
        if new_email and new_email != user.email:
            if User.query.filter_by(email=new_email).first():
                flash("That email is already in use.", "warning")
                return redirect(url_for("admin.user_detail", user_id=user.id))
            user.email = new_email

        # roles checkboxes
        role_names = {r.name for r in Role.query.all()}
        selected = {name for name in request.form.getlist("roles") if name in role_names}
        user.roles = [Role.query.filter_by(name=name).first() for name in sorted(selected)]
        db.session.commit()
        flash("User saved.", "success")
        return redirect(url_for("admin.user_detail", user_id=user.id))

    # Grant an award
    if request.method == "POST" and request.form.get("action") == "grant_award":
        award_id = request.form.get("award_id", type=int)
        award = Award.query.get_or_404(award_id)
        ach = Achievement(
            participant_id=user.id,
            award_id=award.id,
            issued_by_id=current_user.id,
            note=(request.form.get("note") or "").strip()
        )
        db.session.add(ach)
        try:
            db.session.commit()
            flash(f"Award “{award.name}” granted.", "success")
        except IntegrityError:
            db.session.rollback()
            flash("That user already has this award.", "warning")
        return redirect(url_for("admin.user_detail", user_id=user.id))

    # Revoke an award
    if request.method == "POST" and request.form.get("action") == "revoke_award":
        achievement_id = request.form.get("achievement_id", type=int)
        ach = Achievement.query.get_or_404(achievement_id)
        if ach.participant_id != user.id:
            flash("Invalid achievement.", "danger")
            return redirect(url_for("admin.user_detail", user_id=user.id))
        db.session.delete(ach)
        db.session.commit()
        flash("Award revoked.", "success")
        return redirect(url_for("admin.user_detail", user_id=user.id))

    awards_all = Award.query.order_by(Award.points.desc(), Award.name.asc()).all()
    achievements = (user.achievements
                        .order_by(Achievement.issued_at.desc())
                        .all())
    return render_template("admin/user_detail.html",
                           user=user, awards_all=awards_all, achievements=achievements)

