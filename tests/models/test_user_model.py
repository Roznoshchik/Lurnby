import base64
from datetime import datetime, timedelta
import os
from unittest import mock
from app import db
from app.models import (
    User,
    Article,
    Highlight,
    Approved_Sender,
    Topic,
    Tag,
    Task,
    Notification,
)
from tests.conftest import BaseTestCase


class UserTest(BaseTestCase):

    def test_relationships(self):
        user = User(username="testuser", email="testuser@example.com")
        article = Article(user=user)
        highlight = Highlight(user=user)
        approved_sender = Approved_Sender(user=user)
        topic = Topic(user=user)
        tag = Tag(user=user)
        task = Task(user=user, id="foo")
        notification = Notification(user=user)
        # Comms and Event are created automatically via after_insert hook

        db.session.add_all(
            [
                user,
                article,
                highlight,
                approved_sender,
                topic,
                tag,
                task,
                notification,
            ]
        )
        db.session.commit()

        self.assertEqual(user.articles.count(), 1)
        self.assertEqual(user.highlights.count(), 1)
        self.assertEqual(user.events.count(), 1)  # Created automatically
        self.assertEqual(user.approved_senders.count(), 1)
        self.assertEqual(user.topics.count(), 1)
        self.assertEqual(user.tags.count(), 1)
        self.assertEqual(user.tasks.count(), 1)
        self.assertEqual(user.notifications.count(), 1)
        self.assertEqual(user.comms.user_id, user.id)  # Created automatically

    def test_create_user(self):
        user = User(
            goog_id="1234567890",
            firstname="John",
            username="johndoe",
            email="johndoe@example.com",
            admin=False,
            test_account=False,
            deleted=False,
            account_created_date=datetime.utcnow(),
            last_active=datetime.utcnow(),
            last_action="created account",
            tos=True,
            preferences="some preferences",
        )
        db.session.add(user)
        db.session.commit()
        self.assertIsNotNone(user.id)
        self.assertEqual(user.goog_id, "1234567890")
        self.assertEqual(user.firstname, "John")
        self.assertEqual(user.username, "johndoe")
        self.assertEqual(user.email, "johndoe@example.com")
        self.assertFalse(user.admin)
        self.assertFalse(user.test_account)
        self.assertFalse(user.deleted)
        self.assertIsNotNone(user.account_created_date)
        self.assertIsNotNone(user.last_active)
        self.assertEqual(user.last_action, "created account")
        self.assertTrue(user.tos)
        self.assertEqual(user.preferences, "some preferences")

    def test_create_lurnby_email(self):
        user = User(email="johndoe@example.com")
        email = user.create_lurnby_email()
        self.assertIsInstance(email, str)
        self.assertTrue(email.startswith("johndoe-"))
        self.assertTrue(email.endswith("@add-article.lurnby.com") or email.endswith("@add-article-staging.lurnby.com"))

    def test_set_lurnby_email(self):
        user = User(email="johndoe@example.com")
        user.set_lurnby_email()
        self.assertIsNotNone(user.add_by_email)
        self.assertIsInstance(user.add_by_email, str)
        self.assertTrue(
            user.add_by_email.endswith("@add-article.lurnby.com")
            or user.add_by_email.endswith("@add-article-staging.lurnby.com")
        )

    def test_get_tags_dict(self):
        user = User(
            id=1,
            username="johndoe",
            email="johndoe@example.com",
            firstname="John",
            admin=False,
        )
        tag1 = Tag(name="tag1", user=user, archived=False)
        tag2 = Tag(name="tag2", user=user, archived=False)
        tag3 = Tag(name="tag3", user=user, archived=True)
        db.session.add_all([user, tag1, tag2, tag3])
        db.session.commit()

        with mock.patch("app.models.user.url_for") as mock_url_for:
            mock_url_for.return_value = "http://example.com"
            data = user.get_tags_dict()
            self.assertIsInstance(data, dict)
            self.assertEqual(data["id"], user.id)
            self.assertListEqual(data["tags"], ["tag1", "tag2"])
            self.assertIn("_links", data)
            self.assertIn("self", data["_links"])
            self.assertIn("articles", data["_links"])

    def test_to_dict(self):
        user = User(
            id=1,
            username="johndoe",
            email="johndoe@example.com",
            firstname="John",
            admin=False,
            review_count=5,
            add_by_email="johndoe@example.com",
            preferences="preferences",
            tos=True,
        )

        data = user.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["id"], user.id)
        self.assertEqual(data["username"], user.username)
        self.assertEqual(data["email"], user.email)
        self.assertEqual(data["firstname"], user.firstname)
        self.assertEqual(data["articles_count"], user.articles.count())
        self.assertEqual(data["highlights_count"], user.highlights.count())
        self.assertEqual(data["admin"], user.admin)
        self.assertEqual(data["review_count"], user.review_count)
        self.assertEqual(data["add_by_email"], user.add_by_email)
        self.assertEqual(data["preferences"], user.preferences)
        self.assertEqual(data["tos"], user.tos)

    @mock.patch("app.models.user.check_password_hash", return_value=True)
    @mock.patch("app.models.user.generate_password_hash", return_value="hashed")
    def test_from_dict(self, mock_hash, mock_check):
        user = User(
            id=1,
            username="johndoe",
            email="johndoe@example.com",
            firstname="John",
            admin=False,
        )
        data = {
            "username": "johndoe2",
            "email": "johndoe2@example.com",
            "password": "password",
        }
        user.from_dict(data)
        self.assertEqual(user.username, data["username"])
        self.assertEqual(user.email, data["email"])
        mock_hash.assert_called_once_with("password")
        self.assertTrue(user.check_password(data["password"]))

    def test_get_token(self):
        user = User(
            id=1,
            username="johndoe",
            email="johndoe@example.com",
            firstname="John",
            admin=False,
        )
        db.session.add(user)
        db.session.commit()

        with mock.patch.object(os, "urandom", return_value=b"abcdefghijklmnopqrstuv") as mock_urandom:  # 24 bytes
            token = user.get_api_token(expires_in=180)
            self.assertEqual(token, "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dg==")  # 32 chars
            self.assertEqual(user.api_token, token)
            self.assertGreaterEqual(user.api_token_expiration, datetime.utcnow() + timedelta(seconds=60))

            # Test that the token is not regenerated before it expires
            token2 = user.get_api_token(expires_in=60)
            self.assertEqual(token2, "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dg==")
            self.assertEqual(user.api_token, token2)
            self.assertLessEqual(user.api_token_expiration, datetime.utcnow() + timedelta(seconds=180))
            mock_urandom.assert_called_once_with(24)

    def test_revoke_token(self):
        user = User(
            id=1,
            username="johndoe",
            email="johndoe@example.com",
            firstname="John",
            admin=False,
        )
        db.session.add(user)
        db.session.commit()

        user.api_token_expiration = datetime.utcnow() + timedelta(seconds=60)
        user.revoke_api_token()
        self.assertTrue(user.api_token_expiration < datetime.utcnow())

    def test_check_token(self):
        user = User(
            username="johndoe",
            email="johndoe@example.com",
            firstname="John",
            admin=False,
        )
        db.session.add(user)
        db.session.commit()

        # Test a valid API token (24 bytes encodes to 32 base64 chars)
        user.api_token = base64.b64encode(b"abcdefghijklmnopqrstuv").decode("utf-8")
        user.api_token_expiration = datetime.utcnow() + timedelta(seconds=60)
        db.session.commit()

        user2 = User.check_token(user.api_token)
        self.assertEqual(user2, user)

        # Test an expired API token
        user.api_token = base64.b64encode(b"abcdefghijklmnopqrstuv").decode("utf-8")
        user.api_token_expiration = datetime.utcnow() - timedelta(seconds=60)
        db.session.commit()

        user = User.check_token(user.api_token)
        self.assertEqual(user, None)

        # Test a non-existent token
        user = User.check_token("nonexistenttoken")
        self.assertEqual(user, None)
