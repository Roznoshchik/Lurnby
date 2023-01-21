import json
import os
import unittest
from unittest.mock import patch
from app import create_app, db
from app.models import Article, Tag, User
from config import Config
from tests.mocks.mocks import mock_articles, mock_tags


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


class MockResponse:
    def __init__(self, text) -> None:
        self.text = text


class UserApiTests(unittest.TestCase):
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

        # initialize tags
        for tag in mock_tags:
            t = Tag(name=tag, user_id=1)
            db.session.add(t)

        db.session.commit()

        # initialize articles
        for article in mock_articles:
            a = Article()
            for key in article:
                if key != "tags":
                    setattr(a, key, article[key])

            for tag in article["tags"]:
                t = Tag.query.filter_by(name=tag).first()
            db.session.add(a)
            a.AddToTag(t)

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch("app.models.User.check_token")
    def test_get_articles(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        # first check default which should return 4 unarchived articles
        params = {}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(4, len(data["articles"]))

        # then check for archived articles
        params = {"status": "archived"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(1, len(data["articles"]))

        # then check for unread articles
        params = {"status": "unread"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(1, len(data["articles"]))

        # then check for read articles
        params = {"status": "read"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(1, len(data["articles"]))

        # then check for in_progress articles
        params = {"status": "in_progress"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(2, len(data["articles"]))

        # then check search title
        params = {"q": "baz"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(1, len(data["articles"]))

        # then check search content
        params = {"q": "love"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(2, len(data["articles"]))

        # then check filter by tags
        params = {"tag_ids": "1,3"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(3, len(data["articles"]))

        # then check sorting by title ascending
        params = {"title_sort": "ASC"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual("baba", data["articles"][0]["title"])
        self.assertEqual("bar", data["articles"][1]["title"])
        self.assertEqual("baz", data["articles"][2]["title"])
        self.assertEqual("foo", data["articles"][3]["title"])

        # then check sorting by title descending
        params = {"title_sort": "desc"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual("foo", data["articles"][0]["title"])
        self.assertEqual("baz", data["articles"][1]["title"])
        self.assertEqual("bar", data["articles"][2]["title"])
        self.assertEqual("baba", data["articles"][3]["title"])

        # then check sorting by date_read descending
        params = {"opened_sort": "DESC"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual("baba", data["articles"][0]["title"])
        self.assertEqual("baz", data["articles"][1]["title"])
        self.assertEqual("bar", data["articles"][2]["title"])
        self.assertEqual("foo", data["articles"][3]["title"])

        # then check sorting by date_read ascending
        params = {"opened_sort": "asc"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual("foo", data["articles"][0]["title"])
        self.assertEqual("bar", data["articles"][1]["title"])
        self.assertEqual("baz", data["articles"][2]["title"])
        self.assertEqual("baba", data["articles"][3]["title"])

        # then check that pagination returns 1 and has_next
        params = {"per_page": "1"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(1, len(data["articles"]))
        self.assertIsNotNone(data["has_next"])

        # then check that pagination returns 4 and has_next is empty
        params = {"per_page": "4"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(4, len(data["articles"]))
        self.assertIsNone(data["has_next"])

        # then check that pagination returns all and has_next is empty
        params = {"per_page": "all"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(4, len(data["articles"]))
        self.assertIsNone(data["has_next"])

        # then check that we can get the last page
        params = {"per_page": "1", "page": "4"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(1, len(data["articles"]))
        self.assertIsNone(data["has_next"])

        # then check that we can get the 2nd page and has_next is not empty
        params = {"per_page": "1", "page": "2"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(1, len(data["articles"]))
        self.assertIsNotNone(data["has_next"])
