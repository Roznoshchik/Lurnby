import os
from datetime import datetime, timedelta

import boto3

from sqlalchemy import text

from app import db, bucket, CustomLogger
from app.models import Event


logger = CustomLogger("Helpers")


def delete_user(u):
    highlights = u.highlights.all()
    topics = u.topics.all()
    articles = u.articles.all()
    tags = u.tags.all()
    senders = u.approved_senders.all()
    comms = u.comms
    for h in highlights:
        db.session.execute(text("DELETE from highlights_topics where highlight_id=:id"), {"id": h.id})
        db.session.execute(text("DELETE from tags_highlights where highlight_id=:id"), {"id": h.id})
        db.session.delete(h)
    for t in topics:
        db.session.execute(text("DELETE from highlights_topics where topic_id=:id"), {"id": t.id})
        db.session.execute(text("DELETE from tags_topics where topic_id=:id"), {"id": t.id})
        db.session.delete(t)
    for t in tags:
        db.session.execute(text("DELETE from tags_articles where tag_id=:id"), {"id": t.id})
        db.session.execute(text("DELETE from tags_highlights where tag_id=:id"), {"id": t.id})
        db.session.execute(text("DELETE from tags_topics where tag_id=:id"), {"id": t.id})
        db.session.delete(t)
    for a in articles:
        db.session.execute(text("DELETE from tags_articles where article_id=:id"), {"id": a.id})
        db.session.delete(a)
    for s in senders:
        db.session.delete(s)
    db.session.delete(comms)
    db.session.delete(u)
    db.session.commit()


def check_for_delete():
    logger.info("Checking if anything needs deleting from Amazon.")
    today = datetime.utcnow()
    last_week = today - timedelta(days=8)
    evs = Event.query.filter(Event.name == "deleted account", Event.date <= last_week).all()
    if evs:
        for ev in evs:
            if ev.user:
                logger.info(f"deleting files for user {ev.user.id}")
                delete_az(ev.user)
            else:
                logger.info("NoneType User")
    else:
        logger.info("nothing needs deletion")


def delete_az(user):
    if os.environ.get("DEV"):
        az_path_base = f"staging/{user.id}/"
    else:
        az_path_base = f"{user.id}/"

    az = boto3.resource("s3")
    buck = az.Bucket(bucket)
    buck.objects.filter(Prefix=az_path_base).delete()
