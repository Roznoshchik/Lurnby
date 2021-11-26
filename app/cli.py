from datetime import datetime

from app import db
from app.models import User
from app.utilities.user_content import get_recent_highlights, highlights_urls

def register(app):

    @app.cli.command()
    def scheduled():
        """Run scheduled job."""
        print('Running Scheduled Job...')
        print(datetime.utcnow())
        username = User.query.first().username
        print(User.query.first().username)
        User.query.first().username='chiepa'
        db.session.commit
        print(User.query.first().username)
        User.query.first().username=username
        db.session.commit
        # time.sleep(5)
        print('Done!')
        print(datetime.utcnow())

    @app.cli.command()
    def recent_highlights():
        """get highlights."""
        u = User.query.filter_by(email="roznoshchik@gmail.com").first()

        highlights_urls(get_recent_highlights(u))
