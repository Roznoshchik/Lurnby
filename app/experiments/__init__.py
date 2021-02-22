from flask import Blueprint

bp = Blueprint('experiments', __name__)

from app.experiments import routes # noqa E402, F401