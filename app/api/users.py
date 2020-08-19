from app import db
from app.api import bp
from app.main.pulltext import pull_text
from app.models import Article, User, Tag

from flask import jsonify, request, url_for


@bp.route('/users/<int:id>/tags', methods=['GET'])
def get_user_tags(id):
    return jsonify(User.query.get_or_404(id).to_dict())


@bp.route('/users', methods=['POST'])
def create_user():
    pass

@bp.route('users/<int:id>/articles', methods=['POST'])
def add_article(id):
    data = request.get_json() or {}
    urltext = pull_text(data['url'])

    for tag_name in data['tags']:
        if Tag.query.filter_by(name=tag_name).first():
            continue
        else: 
            tag = Tag(name=tag_name, user_id=id)
            db.session.add(tag)

    article = Article(user_id=id, unread=True, archived=False, source_url=data['url'], filetype='url', title=urltext['title'], content=urltext['content'])
    db.session.add(article)
    
    for tag_name in data['tags']:
        tag = Tag.query.filter_by(name=tag_name).first()
        article.AddToTag(tag)
    
    db.session.commit()
    response = jsonify(article.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('main.article', id=article.id) 
    return response

