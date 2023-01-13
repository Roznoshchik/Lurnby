from app import db
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.main.pulltext import pull_text
from app.models import (Article, User, Tag, Comms, 
                        update_user_last_action, Approved_Sender,
                        Event )

from datetime import datetime
from flask import jsonify, request, url_for
from flask_login import login_user



""" ############################# """
""" ##     Create new user     ## """
""" ############################# """

@bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    if (
            'username' not in data or
            'email' not in data or
            'password' not in data
            ):
        return bad_request('must include username. \
                           email, and password fields')

    if User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')

    if User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')

    user = User()
    user.from_dict(data)
    token = user.get_token()
    db.session.add(user)
    db.session.commit()
    comms = Comms(user_id=user.id)
    db.session.add(comms)
    update_user_last_action('Created account')
    db.session.commit()

    response = jsonify({'token': token, 'id': user.id})
    response.status_code = 201
    response.headers['location'] = url_for('api.get_user_tags', id=user.id)
    return response

""" ########################### """
""" ##     Get user info     ## """
""" ########################### """

@bp.route('users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    user = User.query.get(id)
    if user and user.id == token_auth.current_user().id:
        response = jsonify(user.to_dict())
        response.status_code = 200
        return response
    else:
        return bad_request('Not found')

""" ############################## """
""" ##     Update user info     ## """
""" ############################## """

@bp.route('users/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):
    user = User.query.get(id)
    if user and user.id == token_auth.current_user().id:
        data = request.get_json() or {}

        if not data:
            return bad_request('empty payload')

        for key in data:
            # this should probably ensure that no protected values get updated, 
            # just not sure what those are
            if hasattr(user, key):
                setattr(user, key, data[key])

        update_user_last_action('Updated user info')
        db.session.commit()
        
        return ("", 200)
    else:
        return bad_request('Not found')


""" ######################### """
""" ##     Delete user     ## """
""" ######################### """

@bp.route('users/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_user(id):
    user = User.query.get(id)
    file_extension = request.args.get('fileExtension', "json")
    if user and user.id == token_auth.current_user().id:
        ev = Event.add('deleted account')
        db.session.add(ev)
        user.launch_task('account_export', 'exporting data...',
                          user.id, file_extension, delete=True)
        token_auth.current_user().revoke_token()
        db.session.commit()
        
        return ("", 204)
    else:
        return bad_request('Not found')


""" ######################### """
""" ##     Export data     ## """
""" ######################### """

@bp.route('users/<int:id>/export', methods=['GET'])
@token_auth.login_required
def export_data(id):
    user = User.query.get(id)
    file_extension = request.args.get('fileExtension', "json")
    if user and user.id == token_auth.current_user().id:
        ev = Event.add('exported all data')
        db.session.add(ev)
        user.launch_task('account_export', 'exporting data...',
                          user.id, file_extension, delete=False)
        db.session.commit()
        
        return ("", 200)
    else:
        return bad_request('Not found')


""" ################################# """
""" ##     Enable add by email     ## """
""" ################################# """

@bp.route('users/<int:id>/enable_email', methods=['GET'])
@token_auth.login_required
def enable_add_by_email(id):
    user = User.query.get(id)
    if user and user.id == token_auth.current_user().id:
        user.set_lurnby_email()
        db.session.commit()
        update_user_last_action()
        response = jsonify(email = user.add_by_email)
        response.status_code = 200
        return response
    else:
        return bad_request('Not found')

""" ################################## """
""" ##     Get approved senders     ## """
""" ################################## """

@bp.route('users/<int:id>/senders', methods=['GET'])
@token_auth.login_required
def get_approved_senders(id):
    user = User.query.get(id)
    if user and user.id == token_auth.current_user().id:        
        response = jsonify(senders=user.approved_senders.all())
        response.status_code = 200
        return response
    else:
        return bad_request('Not found')

""" ################################# """
""" ##     Add approved sender     ## """
""" ################################# """

@bp.route('users/<int:id>/senders', methods=['POST'])
@token_auth.login_required
def add_approved_senders(id):
    user = User.query.get(id)
    if user and user.id == token_auth.current_user().id:
        data = request.get_json() or {}
        email = data.get('email')
        if email:
            email = email.lower()
            update_user_last_action('added approved sender')
            sender = Approved_Sender(user_id=user.id, email=email)
            event = Event.add('added aproved sender')
            db.session.add(sender)
            db.session.add(event)
            db.session.commit()
            response = jsonify( email=email)
            response.status_code = 201
            return response
        else:
            return bad_request('missing email')
    else:
        return bad_request('Not found')


""" ############################ """
""" ##     Get user comms     ## """
""" ############################ """

@bp.route('users/<int:id>/comms', methods=['GET'])
@token_auth.login_required
def get_user_comms(id):
    user = User.query.get(id)
    if user and user.id == token_auth.current_user().id:        
        response = jsonify(user.comms.to_dict())
        response.status_code = 200
        return response
    else:
        return bad_request('Not found')


""" ############################### """
""" ##     Update user comms     ## """
""" ############################### """

@bp.route('users/<int:id>/comms', methods=['PUT'])
@token_auth.login_required
def update_user_comms(id):
    user = User.query.get(id)
    data = request.get_json() or {}
    VALID_KEYS = ["informational", "educational", "promotional", "highlights", "reminders"]
    
    if user and user.id == token_auth.current_user().id:   
        if data and data['user_id'] == user.id:
            comms = user.comms
            for key in VALID_KEYS:
                if key in data:
                    setattr(comms, key, data[key])  
        db.session.commit() 
        response = jsonify(user.comms.to_dict())
        response.status_code = 200
        return response
    else:
        return bad_request('Not found')



""" ############################################### """
""" ##     LEGACY Extension, add new article     ## """
""" ############################################### """


@bp.route('users/<int:id>/articles', methods=['POST'])
@token_auth.login_required
def add_article(id):
    data = request.get_json() or {}
    urltext = pull_text(data['url'])
    user = User.query.filter_by(id=id).first()
    login_user(user)
    for tag_name in data['tags']:
        if Tag.query.filter_by(name=tag_name).first():
            continue
        else:
            tag = Tag(name=tag_name, user_id=id, archived=False)
            db.session.add(tag)

    article = Article(user_id=id, unread=True, archived=False,
                      source_url=data['url'], filetype='url',
                      title=data['title'], content=urltext['content'])
    db.session.add(article)
    article.date_read_date = datetime.utcnow().date()
    article.estimated_reading()

    for tag_name in data['tags']:
        tag = Tag.query.filter_by(name=tag_name).first()
        if tag.archived:
            tag.archived = False
        article.AddToTag(tag)

    db.session.commit()
    response = jsonify(article.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('main.article', uuid=article.uuid)

    # why did I want to log users out? this is logging me out every time I add new code.
    # logout_user()
    return response

""" ############################################# """
""" ##     LEGACY Extension, get user tags     ## """
""" ############################################# """

@bp.route('/users/<int:id>/tags', methods=['GET'])
@token_auth.login_required
def get_user_tags(id):
    return jsonify(User.query.get_or_404(id).get_tags_dict())
