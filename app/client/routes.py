from flask import render_template

from app.client import bp


@bp.get("/login")
def login():
    """Public login page for Preact app"""
    return render_template("client/login.html")


@bp.get("/articles")
@bp.get("/articles/<uuid>")
@bp.get("/highlights")
@bp.get("/review")
@bp.get("/settings")
def client_app(uuid=None):
    """Main app pages (auth handled client-side)"""
    return render_template("client/app.html")
