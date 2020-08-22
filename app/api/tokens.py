from app import db
from app.api import bp
from app.api.auth import basic_auth, token_auth
from app.api.errors import bad_request
from app.models import User

from flask import jsonify, request, url_for

@bp.route('/tokens', methods = ['POST'])
@basic_auth.login_required

def get_token():
    token = basic_auth.current_user().get_token()
    db.session.commit()
    return jsonify({'token':token, 'id':basic_auth.current_user().id})


@bp.route('/tokens/goog', methods=['POST'])
def google_login():
    data = request.get_json() or {}
    if 'goog_id' not in data or  'email' not in data or 'first_name' not in data:
        return bad_request('must include goog_id, email, and first_name fields')
    
    user = User.query.filter_by(email=data['email']).first()
    if user:
        token = user.get_token()
        db.session.commit()
        response = jsonify({'token':token, 'id':user.id})
        return response
        
    user = User(goog_id=data['goog_id'], email=data['email'], firstname=data['first_name'])
    token = user.get_token()
    db.session.commit()
    response = jsonify({'token':token, 'id':user.id})
    response.status_code = 201
    response.headers['location'] = url_for('api.get_user_tags', id=user.id)
    return response




@bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    token_auth.current_user().revoke_token()
    db.session.commit()
    return '', 204
    
