from app import db
from app.models import Highlight, User
import random

from flask import url_for, render_template

def get_recent_highlights(user):
    highlights = user.highlights.order_by(Highlight.created_date.desc()).all()
    recent = []
    for i in range(5):
        num = random.randint(0, len(highlights))
        recent.append(highlights[num])   
        highlights.remove(highlights[num])
    # print(recent)
    return recent

def highlights_urls(highlights):
    print(render_template('email/content/recent_highlights.html', highlights=highlights))