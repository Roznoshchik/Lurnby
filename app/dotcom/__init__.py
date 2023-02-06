from flask import Blueprint

bp = Blueprint("dotcom", __name__)

from app.dotcom import routes  # noqa : E402, F401
