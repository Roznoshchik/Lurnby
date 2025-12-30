"""Shared pytest configuration for all tests"""

import os
import unittest
from app import create_app, db
from config import Config


class TestConfig(Config):
    """Test configuration using local PostgreSQL database"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "postgresql://localhost/lurnby-test")
    WTF_CSRF_ENABLED = False
    REDIS_URL = "redis://"


# Module-level app for reuse across tests (avoids repeated create_app overhead)
_app = None


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

        # Drop and recreate tables for clean state
        db.drop_all()
        db.create_all()

    def tearDown(self):
        """Clean up database after each test"""
        db.session.rollback()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
