from flask import Blueprint

bp = Blueprint("api", __name__)

from app.api import tokens, errors, users, articles  # noqa : E402, F401
