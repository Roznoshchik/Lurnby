"""Shared pytest configuration for all tests"""
import os
import unittest
from app import create_app, db
from config import Config


class TestConfig(Config):
    """Test configuration using local postgres database"""
    TESTING = True
    # Use TEST_DATABASE_URL from environment (for CI) or default to local test db
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", "postgresql://localhost/lurnby-test"
    )
    WTF_CSRF_ENABLED = False
    REDIS_URL = "redis://"


class BaseTestCase(unittest.TestCase):
    """Base test case with database setup and teardown for full test isolation"""

    def setUp(self):
        """Set up test app and database before each test"""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        # Drop all tables first to ensure clean state
        db.drop_all()
        # Create all tables fresh
        db.create_all()

    def tearDown(self):
        """Clean up database after each test for full isolation"""
        # Rollback any uncommitted transactions
        db.session.rollback()
        # Remove session
        db.session.remove()
        # Drop all tables to ensure no data persists
        db.drop_all()
        self.app_context.pop()
