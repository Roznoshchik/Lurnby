import json
import unittest
from unittest.mock import patch

from app import create_app, db
from app.models import Article, User, Task
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


class TasksApiTests(unittest.TestCase):
    def setUp(self):
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

    @patch("app.api.tasks.poll_for_completion")
    @patch("app.models.User.check_token")
    def test_task_status_returns_processing_when_incomplete(
        self,
        mock_check_token,
        mock_poll,
    ):
        mock_poll.return_value = False  # Task still processing
        mock_check_token.return_value = User.query.first()

        user = User.query.first()
        article = Article(user_id=user.id)
        db.session.add(article)
        db.session.commit()
        article_uuid = str(article.uuid)

        task = Task(id="test-task-id", name="bg_add_article", user=user)
        db.session.add(task)
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
        self.assertNotIn("location", data)

    @patch("app.api.tasks.poll_for_completion")
    @patch("app.models.User.check_token")
    def test_task_status_returns_complete_with_location(
        self,
        mock_check_token,
        mock_poll,
    ):
        mock_poll.return_value = True  # Task complete
        mock_check_token.return_value = User.query.first()

        user = User.query.first()
        article = Article(user_id=user.id)
        db.session.add(article)
        db.session.commit()
        article_uuid = str(article.uuid)

        task = Task(id="test-task-id", name="bg_add_article", user=user, complete=True)
        db.session.add(task)
        db.session.commit()

        args = {"article_id": article_uuid}
        res = self.client.get(
            f"/api/tasks/{task.id}",
            query_string=args,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertFalse(data["processing"])
        self.assertIn("location", data)
