from app import db
from app.models import Article, Tag


def match_tags():
    articles = Article.query.all()
    for a in articles:
        tags = a.tags.all()
        for t in tags:
            if t.user_id != a.user_id:
                a.RemoveFromTag(t)
                tag = Tag.query.filter_by(name=t.name, user_id=a.user_id).first()
                if not tag:
                    tag = Tag(name=t.name, user_id=a.user_id)
                    db.session.add(tag)
                a.AddToTag(tag)
    db.session.commit()
