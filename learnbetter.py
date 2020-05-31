from app import app, db

from app.models import User, Article, Highlight, Topic, highlights_topics, Tag

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User':User, 'Article':Article, 'Highlight':Highlight, 'Topic':Topic, 'highlights_topics':highlights_topics, 'Tag':Tag}