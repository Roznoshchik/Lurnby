from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from uuid import uuid4, UUID
import unittest
from unittest.mock import patch

from app import create_app, db
from app.models import Article, User, Tag
from config import Config

from tests.mocks.mocks import mock_articles, mock_tags


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


class MockResponse:
    def __init__(self, text) -> None:
        self.text = text



class GetHighlightsApiTests(unittest.TestCase):
    def setUp(self):
        os.environ["testing"] = "1"
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

        # setup user
        user = User(email="test@test.com")
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch("app.models.User.check_token")
    def test_get_highlights(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        # first check default which should return 4 unarchived articles
        params = {}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        # self.assertEqual(4, len(data["articles"]))
