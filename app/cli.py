from datetime import datetime, timedelta

from app import db
from app.models import User, Event
from app.utilities.user_content import get_recent_highlights
from app.utilities.delete_user import check_for_delete

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
        get_recent_highlights()
 

    @app.cli.command()
    def delete_from_az():
        """ delete from amazon"""
        check_for_delete()
