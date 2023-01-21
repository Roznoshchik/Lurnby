from app import db
from app.email import send_email
from app.models import Highlight, User, Message, Comms
import random
from datetime import datetime, timedelta

from flask import render_template, current_app


def get_recent_highlights():
    print("checking if highlights email needs to be sent out.")
    users = (
        User.query.join(Comms, (Comms.user_id == User.id))
        .filter(
            Comms.highlights == True, User.deleted == False, User.test_account == False
        )
        .all()
    )
    today = datetime.utcnow()
    last_week = today - timedelta(days=7)

    for u in users:

        msg = u.messages.filter(
            Message.name == "recent highlights", Message.date > last_week
        ).first()
        if not msg:
            highlights = (
                u.highlights.order_by(Highlight.created_date.desc())
                .filter(
                    Highlight.review_date < last_week,
                    Highlight.archived == False,
                    Highlight.do_not_review == False,
                )
                .all()
            )
            recent = []
            if len(highlights) > 1:
                if len(highlights) < 6:
                    for h in highlights:
                        recent.append(h)
                        h.review_date = today
                else:
                    for i in range(5):
                        num = random.randint(0, len(highlights) - 1)
                        recent.append(highlights[num])
                        highlights[num].review_date = today
                        highlights.remove(highlights[num])

                send_email(
                    "[Lurnby] Your recent highlights",
                    sender=current_app.config["ADMINS"][0],
                    recipients=[u.email],
                    text_body=render_template(
                        "email/content/recent_highlights.txt", highlights=recent
                    ),
                    html_body=render_template(
                        "email/content/recent_highlights.html", highlights=recent
                    ),
                    sync=True,
                )
                msg = Message.add("recent highlights", u)
                db.session.add(msg)
                db.session.commit()
                print(f"sent recent highlights to user {u.id}")
            else:
                print("no highlights qualified")


def highlights_urls(highlights):
    print(
        render_template("email/content/recent_highlights.html", highlights=highlights)
    )
