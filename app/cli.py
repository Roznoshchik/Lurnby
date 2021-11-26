import os
import click
import time
from datetime import datetime

from app import db
from app.models import User

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


