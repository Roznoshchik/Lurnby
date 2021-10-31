from flask import Blueprint

bp = Blueprint('content', __name__)

from app.content import routes # noqa : E402, F401
