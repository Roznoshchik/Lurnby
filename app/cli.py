from datetime import datetime
import os
import subprocess
import time

import click

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
    def build():
        """Build frontend assets with Vite."""
        client_dir = os.path.join(os.getcwd(), "client")
        print("Building assets with Vite...")
        try:
            subprocess.run(["npm", "run", "build"], cwd=client_dir, check=True)  # nosec
            print("Build complete!")
        except subprocess.CalledProcessError as e:
            print(f"Build failed with error: {e}")
            raise

    @app.cli.command()
    @click.option('--all', is_flag=True, help='Run both pytest and npm tests')
    def test(all):
        """Run frontend tests with Vitest. Use --all to run both Python and frontend tests."""
        client_dir = os.path.join(os.getcwd(), "client")

        if all:
            # Run pytest first
            print("Running Python tests with pytest...")
            try:
                subprocess.run(["pytest"], check=True)  # nosec
                print("Python tests complete!")
            except subprocess.CalledProcessError as e:
                print(f"Python tests failed with error: {e}")
                raise

        # Run npm tests
        print("Running frontend tests with Vitest...")
        try:
            subprocess.run(["npm", "run", "test:run"], cwd=client_dir, check=True)  # nosec
            print("Frontend tests complete!")
        except subprocess.CalledProcessError as e:
            print(f"Frontend tests failed with error: {e}")
            raise

    @app.cli.command()
    @click.option('--prod', is_flag=True, help='Run in production mode (use built assets, no Vite dev server)')
    def serve(prod):
        """Run Flask, Redis, RQ worker, and optionally Vite dev server concurrently."""
        processes = []

        try:
            # Start Redis server
            print("Starting Redis server...")
            redis_process = subprocess.Popen(["redis-server"])  # nosec
            processes.append(("Redis server", redis_process))

            # Wait for Redis to be ready
            print("Waiting for Redis to initialize...")
            time.sleep(2)

            # Start RQ worker
            print("Starting RQ worker for background tasks...")
            rq_process = subprocess.Popen(["rq", "worker", "lurnby-tasks"])  # nosec
            processes.append(("RQ worker", rq_process))

            # Start Vite dev server only if not in prod mode
            if not prod:
                client_dir = os.path.join(os.getcwd(), "client")
                print("Starting Vite dev server in client directory...")
                npm_process = subprocess.Popen(["npm", "start"], cwd=client_dir)  # nosec
                processes.append(("Vite dev server", npm_process))
            else:
                print("Running in production mode (using built assets)")
                # Build assets first
                client_dir = os.path.join(os.getcwd(), "client")
                print("Building assets with Vite...")
                subprocess.run(["npm", "run", "build"], cwd=client_dir, check=True)  # nosec
                print("Build complete!")
                # Set FLASK_DEBUG=0 for production mode
                os.environ["FLASK_DEBUG"] = "0"

            # Start Flask server
            print("Starting Flask server...")
            subprocess.run(["flask", "run"], check=True)  # nosec

        finally:
            print("Flask server has exited. Shutting down subprocesses...")
            for name, process in processes:
                print(f"Shutting down {name}...")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print(f"{name} did not terminate, killing...")
                    process.kill()
            print("All subprocesses shutdown complete.")
