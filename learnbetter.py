from app import create_app, db

from app.models import (User, Article, Highlight, Topic, highlights_topics,
                        Tag, tags_articles, tags_highlights, Approved_Sender,
                        Task, Notification, Suggestion)

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Article': Article, 'Highlight': Highlight,
            'Topic': Topic, 'highlights_topics': highlights_topics, 'Tag': Tag,
            'tags_articles': tags_articles, 'tags_highlights': tags_highlights,
            'Task': Task, 'Notification':Notification,
            'Approved_Sender':Approved_Sender, 'Suggestion': Suggestion}
