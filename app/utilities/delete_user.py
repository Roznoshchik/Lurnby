from app import db

def delete_user(u):
    highlights=u.highlights.all()
    topics = u.topics.all()
    articles = u.articles.all()
    tags = u.tags.all()
    senders = u.approved_senders.all()
    comms = u.comms
    for h in highlights:
        db.session.execute(f'DELETE from highlights_topics where highlight_id={h.id}')
        db.session.delete(h)
    for t in topics:
        db.session.execute(f'DELETE from highlights_topics where topic_id={t.id}')
        db.session.delete(t)
    for t in tags:
        db.session.execute(f'DELETE from tags_articles where tag_id={t.id}')
        db.session.delete(t)
    for a in articles:
        db.session.execute(f'DELETE from tags_articles where article_id={a.id}')
        db.session.delete(a)
    for s in senders:
        db.session.delete(s)
    db.session.delete(comms)
    db.session.delete(u)
    db.session.commit()
