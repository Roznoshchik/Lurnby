from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from uuid import uuid4, UUID
from pprint import pprint, PrettyPrinter
import unittest
from unittest.mock import patch

from app import create_app, db
from app.models import Article, User, Tag, Highlight
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
        user = User.query.first()
        mock_check_token.return_value = user

        art1 = Article(user_id=user.id, title="Article 1")
        art2 = Article(user_id=user.id, title="Article 2")
        art3 = Article(user_id=user.id, title="Article 2")

        tag1 = Tag(user_id=user.id, name="Pikachu")
        tag2 = Tag(user_id=user.id, name="Bulbasaur")

        db.session.add_all(
            [
                art1,
                art2,
                art3,
                tag1,
                tag2,
            ]
        )
        db.session.commit()

        hlght1 = Highlight(article_id=art1.id, user_id=user.id, text="alabama")
        hlght2 = Highlight(article_id=art1.id, user_id=user.id, text="arkansaw")
        hlght3 = Highlight(article_id=art1.id, user_id=user.id, text="I")
        hlght4 = Highlight(article_id=art1.id, user_id=user.id, text="do")
        hlght5 = Highlight(article_id=art2.id, user_id=user.id, text="love")
        hlght6 = Highlight(article_id=art2.id, user_id=user.id, text="my")
        hlght7 = Highlight(article_id=art2.id, user_id=user.id, text="ma")
        hlght8 = Highlight(article_id=art2.id, user_id=user.id, text="and")
        hlght9 = Highlight(article_id=art3.id, user_id=user.id, text="pa")
        hlght10 = Highlight(
            article_id=art3.id, user_id=user.id, archived=True, text="Not the way"
        )

        db.session.add_all(
            [
                hlght1,
                hlght2,
                hlght3,
                hlght4,
                hlght5,
                hlght6,
                hlght7,
                hlght8,
                hlght9,
                hlght10,
            ]
        )

        hlght1.add_tag(tag1)
        hlght2.add_tag(tag1)
        hlght3.add_tag(tag1)
        hlght4.add_tag(tag1)
        hlght5.add_tag(tag2)
        hlght6.add_tag(tag2)

        db.session.commit()

        # first check default which should return 9 unarchived highlights
        params = {}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 9)

        # return 1 archived highlight
        params = {"status": "archived"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 1)

        # return 6 tagged highlights
        params = {"tag_status": "tagged"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 6)

        # return 3 untagged highlights
        params = {"tag_status": "untagged"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 3)
        
        # return 4 highlights tagged with pikachu
        params = {"tag_ids": f"{tag1.id}"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 4)
        
        # return 6 highlights tagged with pikachu and bulbasaur
        params = {"tag_ids": f"{tag1.id}, {tag2.id}"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 6)
