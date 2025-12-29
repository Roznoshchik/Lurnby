import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from app import create_app, db
from app.models import Article, User
from config import Config

from tests.mocks.mock_redis import MockRedis


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


class MockResponse:
    def __init__(self, text) -> None:
        self.text = text


class TasksApiTests(unittest.TestCase):
    def setUp(self):
        # os.environ["testing"] = "1"
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

    @patch("app.tasks.get_epub_title")
    @patch("app.tasks.convert_epub")
    @patch("app.tasks.s3.download_file")
    @patch("app.api.tasks.current_app.redis")
    @patch("app.models.User.check_token")
    def test_article_uploaded_returns_error_without_query_args(
        self,
        mock_check_token,
        mock_redis,
        mock_s3,
        mock_epub_converted,
        mock_epub_title,
    ):
        mock_redis.mock_implementation = MockRedis()
        mock_check_token.return_value = User.query.first()
        mock_epub_title.return_value = "FooBar"
        mock_epub_converted.return_value = "Hello Old Friend"

        epub = open(f"{Path(os.path.dirname(__file__)).parent}/mocks/mock.epub", "rb")

        def mock_download_file(bucket, article_uuid, file):
            with open(file, "wb") as file:
                file.write(epub.read())

        mock_s3.side_effect = mock_download_file
        article = Article(user_id=User.query.first().id)
        db.session.add(article)
        db.session.commit()
        article_uuid = str(article.uuid)

        task = User.query.first().launch_task("bg_add_article", article_uuid=article_uuid, file_ext=".eoub", file=None)

        db.session.commit()

        args = {"article_id": article_uuid}
        res = self.client.get(
            f"/api/tasks/{task.id}",
            query_string=args,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["processing"])
        self.assertTrue("progress" in data)
        self.assertTrue("task_id" in data)
        self.assertTrue("location" not in data)

        task.complete = True
        db.session.commit()

        res = self.client.get(
            f"/api/tasks/{task.id}",
            query_string=args,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(data["processing"])
        self.assertTrue("location" in data)
