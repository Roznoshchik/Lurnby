from app import db
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.main.pulltext import pull_text
from app.models import (Article, User, Tag, Comms,
                        Approved_Sender, Event)

from datetime import datetime
from flask import jsonify, request, url_for
from flask_login import login_user


""" ############################# """
""" ##     Create new user     ## """
""" ############################# """


@bp.route('/articles', methods=['GET'])
@token_auth.login_required
def get_articles():
    user = token_auth.current_user()
    params = request.args
    
    response = jsonify({})
    response.status_code = 200
    return response
