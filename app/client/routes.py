from flask import render_template

from app.client import bp


@bp.get("/login")
def login():
    """Public login page for Preact app"""
    return render_template("client/login.html")


@bp.get("/articles")
def articles():
    """Articles list page"""
    return render_template("client/articles.html")


@bp.get("/highlights")
def highlights():
    """Highlights list page"""
    return render_template("client/highlights.html")


@bp.get("/articles/<uuid>")
@bp.get("/review")
@bp.get("/settings")
def client_app(uuid=None):
    """Main app pages (auth handled client-side)"""
    return render_template("client/app.html")
