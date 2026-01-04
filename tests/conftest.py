"""Shared pytest configuration for all tests"""

import os

# Set testing environment BEFORE any app imports
os.environ["FLASK_ENV"] = "testing"

import unittest  # noqa: E402
from app import create_app, db  # noqa: E402
from config import TestConfig  # noqa: E402

# Import tasks early to ensure its module-level app context is created
# BEFORE any test setUp runs (matches behavior when running all tests)
import app.tasks  # noqa: E402, F401


# Module-level app for reuse across tests (avoids repeated create_app overhead)
_app = None

# Safety: the main app database that must never be dropped by tests
APP_DATABASE_NAME = os.environ.get("APP_DATABASE_NAME", "lurnby")


def safe_drop_all():
    """Drop all tables only if NOT connected to the main app database."""
    db_name = db.engine.url.database
    if db_name == APP_DATABASE_NAME:
        raise RuntimeError(
            f"SAFETY: Refusing to drop the main app database '{db_name}'. " f"Tests must use a separate test database."
        )
    db.drop_all()


def get_test_app():
    """Get or create the test app (singleton per test session)"""
    global _app
    if _app is None:
        _app = create_app(TestConfig)
    return _app


class BaseTestCase(unittest.TestCase):
    """Base test case with database setup and teardown for full test isolation"""

    def setUp(self):
        """Set up test app and database before each test"""
        self.app = get_test_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        safe_drop_all()
        db.create_all()

    def tearDown(self):
        """Clean up database after each test"""
        db.session.rollback()
        db.session.remove()
        safe_drop_all()
        self.app_context.pop()
