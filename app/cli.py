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
    @click.option("--python-only", is_flag=True, help="Format only Python files")
    @click.option("--client-only", is_flag=True, help="Format only client files")
    def format(python_only, client_only):
        """Format code with black (Python) and biome (client)."""
        client_dir = os.path.join(os.getcwd(), "client")

        if client_only or not python_only:
            print("Running biome formatter on client files...")
            try:
                subprocess.run(["npm", "run", "format"], cwd=client_dir, check=True)  # nosec
                print("Client formatting complete!")
            except subprocess.CalledProcessError as e:
                print(f"Client formatting failed with error: {e}")
                raise

        if python_only or not client_only:
            print("Running black formatter on Python files...")
            try:
                subprocess.run(["black", "."], check=True)  # nosec
                print("Python formatting complete!")
            except subprocess.CalledProcessError as e:
                print(f"Python formatting failed with error: {e}")
                raise

    @app.cli.command()
    @click.option("--python-only", is_flag=True, help="Lint only Python files")
    @click.option("--client-only", is_flag=True, help="Lint only client files")
    def lint(python_only, client_only):
        """Check code with flake8 (Python) and biome (client)."""
        client_dir = os.path.join(os.getcwd(), "client")
        has_errors = False

        if client_only or not python_only:
            print("Running biome linter on client files...")
            try:
                subprocess.run(["npm", "run", "lint"], cwd=client_dir, check=True)  # nosec
                print("Client linting complete - no issues found!")
            except subprocess.CalledProcessError:
                print("Client linting found issues")
                has_errors = True

        if python_only or not client_only:
            print("\nRunning flake8 linter on Python files...")
            # First, check for serious errors only (following pre-commit pattern)
            try:
                subprocess.run(
                    ["flake8", "--count", "--select=E9,F63,F7,F82", "--show-source", "--statistics"],
                    check=True,
                )  # nosec
            except subprocess.CalledProcessError:
                print("Python linting found SERIOUS ERRORS (see output above)")
                has_errors = True

            # Then, show all warnings without failing (following pre-commit pattern)
            print("Checking for style warnings...")
            subprocess.run(["flake8", "--exit-zero"], check=False)  # nosec

            if not has_errors:
                print("Python linting complete - no serious errors found!")

        if has_errors:
            raise subprocess.CalledProcessError(1, "lint")

    @app.cli.command()
    @click.option("--python-only", is_flag=True, help="Run only Python tests")
    @click.option("--client-only", is_flag=True, help="Run only client tests")
    def test(python_only, client_only):
        """Run all tests. Use --python-only or --client-only to run specific tests."""
        client_dir = os.path.join(os.getcwd(), "client")

        if python_only or not client_only:
            print("Running Python tests with pytest...")
            try:
                subprocess.run(
                    ["pytest", "--durations=0", "--durations-min=0.29"],
                    check=True,
                )  # nosec
                print("Python tests complete!")
            except subprocess.CalledProcessError as e:
                print(f"Python tests failed with error: {e}")
                raise

        if client_only or not python_only:
            print("Running frontend tests with Vitest...")
            try:
                subprocess.run(["npm", "run", "test:run"], cwd=client_dir, check=True)  # nosec
                print("Frontend tests complete!")
            except subprocess.CalledProcessError as e:
                print(f"Frontend tests failed with error: {e}")
                raise

    @app.cli.command()
    @click.option("--prod", is_flag=True, help="Run in production mode (use built assets, no Vite dev server)")
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
