from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from ..extensions import db
from ..models import User, Role
from ..config import Config
bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        print(f"{email}:{password}")
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("participants.my_awards"))
        flash("Invalid email or password", "danger")
    return render_template("login.html")

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        first = request.form.get("first_name") or ""
        last = request.form.get("last_name") or ""

        if not email or not password:
            flash("Email and password are required", "warning")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("That email is already registered", "warning")
            return redirect(url_for("auth.register"))

        u = User(email=email, first_name=first, last_name=last)

        if hasattr(u, "set_password"):
            u.set_password(password)  # type: ignore[attr-defined]
        else:
            u.password_hash = password  # fallback if you haven’t added hashing yet

        participant = Role.query.filter_by(name="participant").first()
        if participant:
            u.roles.append(participant)

        db.session.add(u)
        db.session.commit()
        login_user(u)
        return redirect(url_for("participants.my_awards"))
    return render_template("register.html")
