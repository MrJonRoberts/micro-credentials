from flask import Flask, render_template, request, redirect, url_for, session, Blueprint

bp = Blueprint("main", __name__, url_prefix="/")

@bp.route('/')
def index():
    return render_template("home.html")