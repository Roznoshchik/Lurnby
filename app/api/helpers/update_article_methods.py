from app import db
from app.models import Tag


def update_tags(tags, article, user):
    article_tags = article.tag_list
    for tag_name in article_tags:
        if tag_name not in tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if tag:
                article.remove_from_tag(tag)

    for tag_name in tags:
        if tag_name not in article_tags:
            tag = Tag.query.filter_by(name=tag_name, user_id=user.id).first()
            if not tag:
                tag = Tag(name=tag_name, user_id=user.id)
                db.session.add(tag)
            article.add_to_tag(tag)

    return article
