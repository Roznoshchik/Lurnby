from flask import Blueprint

bp = Blueprint("api", __name__)

from app.api import auth_routes, tokens, errors, users, articles, tasks, highlights, tags
