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


@bp.get("/tags")
def tags():
    """Tags management page"""
    return render_template("client/tags.html")


@bp.get("/articles/<uuid>")
def reader(uuid):
    """Article reader page"""
    return render_template("client/reader.html")


@bp.get("/review")
@bp.get("/settings")
def client_app():
    """Main app pages (auth handled client-side)"""
    return render_template("client/app.html")
