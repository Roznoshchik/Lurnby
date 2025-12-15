from datetime import datetime
import os
import subprocess

from app import db
from app.models import User
from app.helpers.user_content import get_recent_highlights
from app.helpers.delete_user import check_for_delete


def register(app):
    @app.cli.command()
    def scheduled():
        """Run scheduled job."""
        print("Running Scheduled Job...")
        print(datetime.utcnow())
        username = User.query.first().username
        print(User.query.first().username)
        User.query.first().username = "chiepa"
        db.session.commit
        print(User.query.first().username)
        User.query.first().username = username
        db.session.commit
        # time.sleep(5)
        print("Done!")
        print(datetime.utcnow())

    @app.cli.command()
    def recent_highlights():
        """get highlights."""
        get_recent_highlights()

    @app.cli.command()
    def delete_from_az():
        """delete from amazon"""
        check_for_delete()

    @app.cli.command()
    def serve():
        """Run Flask and Vite dev server concurrently."""
        client_dir = os.path.join(os.getcwd(), "client")

        print("Starting npm dev server in client directory...")
        npm_process = subprocess.Popen(["npm", "start"], cwd=client_dir)  # nosec

        try:
            print("Starting Flask server...")
            subprocess.run(["flask", "run"], check=True)  # nosec
        finally:
            print("Flask server has exited. Shutting down npm server...")
            npm_process.terminate()
            try:
                npm_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                npm_process.kill()
            print("npm server shutdown complete.")
