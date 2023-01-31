import json
import os

import unittest
from unittest.mock import patch

from app import create_app, db
from app.models import Article, User, Tag, Highlight
from config import Config


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

        # setup articles and tags
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

        # Setup highlights
        hlght1 = Highlight(article_id=art1.id, user_id=user.id, text="alabama")
        hlght2 = Highlight(article_id=art1.id, user_id=user.id, text="arkansas")
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

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch("app.models.User.check_token")
    def test_get_unarchived_highlights(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        # first check default which should return 9 unarchived highlights
        params = {}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 9)

    @patch("app.models.User.check_token")
    def test_get_archived_highlights(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        # return 1 archived highlight
        params = {"status": "archived"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 1)

    @patch("app.models.User.check_token")
    def test_get_all_tagged_highlights(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        # return 6 tagged highlights
        params = {"tag_status": "tagged"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 6)

    @patch("app.models.User.check_token")
    def test_get_untagged_highlights(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        # return 3 untagged highlights
        params = {"tag_status": "untagged"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 3)

    @patch("app.models.User.check_token")
    def test_get_highlights_with_specific_tags(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        # return 4 highlights tagged with pikachu
        params = {"tag_ids": "1"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 4)

        # return 6 highlights tagged with pikachu and bulbasaur
        params = {"tag_ids": "1,2"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 6)

    @patch("app.models.User.check_token")
    def test_get_highlights_with_search_phrase(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        # return 1 highlights with text with Arkansas
        params = {"q": "arkansas"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 1)

        # return 1 highlights with text with Arkansas
        params = {"q": "Arkansas"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 1)

    @patch("app.models.User.check_token")
    def test_get_highlights_with_sorting(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        # return 9 highlights in ascending order
        params = {"created_sort": "asc"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 9)
        self.assertEqual(data.get("highlights")[0]["text"], "alabama")
        self.assertEqual(data.get("highlights")[-1]["text"], "pa")

        # return 9 highlights in desc order
        params = {"created_sort": "desc"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 9)
        self.assertEqual(data.get("highlights")[0]["text"], "pa")
        self.assertEqual(data.get("highlights")[-1]["text"], "alabama")

    @patch("app.models.User.check_token")
    def test_get_highlights_with_pagination(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        # return 2 highlights with has_next being true
        params = {"per_page": "2"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 2)
        self.assertTrue(data["has_next"])

        # return 1 highlight with has_next being false
        params = {"per_page": "2", "page": "5"}
        res = self.client.get(
            "/api/highlights",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("highlights")), 1)
        self.assertFalse(data["has_next"])
