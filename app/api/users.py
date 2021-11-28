from app import db
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request
from app.main.pulltext import pull_text
from app.models import Article, User, Tag, Comms

from datetime import datetime
from flask import jsonify, request, url_for


@bp.route('/users/<int:id>/tags', methods=['GET'])
@token_auth.login_required
def get_user_tags(id):
    return jsonify(User.query.get_or_404(id).to_dict())


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
    db.session.commit()
    
    response = jsonify({'token': token, 'id': user.id})
    response.status_code = 201
    response.headers['location'] = url_for('api.get_user_tags', id=user.id)
    return response


@bp.route('users/<int:id>/articles', methods=['POST'])
@token_auth.login_required
def add_article(id):
    data = request.get_json() or {}
    urltext = pull_text(data['url'])

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
        article.AddToTag(tag)

    db.session.commit()
    response = jsonify(article.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('main.article', id=article.id)
    return response
