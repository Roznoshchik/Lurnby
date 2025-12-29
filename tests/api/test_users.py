import json
import os
from unittest.mock import patch
from app import db
from app.models import User
from tests.conftest import BaseTestCase


class UserApiTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        os.environ["testing"] = "1"

        # Create user (Comms and Event created automatically via after_insert hook)
        user = User(email="foo@baz.com")
        db.session.add(user)
        db.session.commit()

        self.user = user
        self.comms = user.comms  # Access auto-created Comms

    def tearDown(self):
        super().tearDown()

    def test_create_user_fails_without_data(self):
        res = self.client.post("/api/users", json={"a": "b"})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["message"], "must include username, email, and password fields")

    def test_create_user(self):
        res = self.client.post(
            "/api/users",
            json={
                "username": "test@test.com",
                "email": "test@test.com",
                "password": "foo",
            },
        )
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(True, "id" in data)
        self.assertEqual(True, "token" in data)

    @patch("app.models.User.check_token")
    def test_get_user(self, mock_check_token):
        mock_check_token.return_value = User.query.first()
        res = self.client.get("/api/users/1", headers={"Authorization": "Bearer abc123"})
        data = json.loads(res.data)
        self.assertEqual(data, self.user.to_dict())

    @patch("app.models.User.check_token")
    def test_update_user(self, mock_check_token):
        mock_check_token.return_value = User.query.first()
        res = self.client.patch(
            "/api/users/1",
            json={"email": "foo@bar.com"},
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(data["email"], "foo@bar.com")
        self.assertEqual(self.user.email, "foo@bar.com")

    @patch("app.models.User.check_token")
    def test_delete_user(self, mock_check_token):
        mock_check_token.return_value = User.query.first()
        res = self.client.delete(
            "/api/users/1",
            query_string={"export": False},
            headers={"Authorization": "Bearer abc123"},
        )
        self.assertEqual(res.status_code, 204)
        self.assertEqual("<User None>", str(User.query.first()))

    @patch("app.models.User.check_token")
    def test_enable_add_by_email(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        self.assertIsNone(self.user.add_by_email)

        res = self.client.get("/api/users/1/enable_email", headers={"Authorization": "Bearer abc123"})
        self.assertEqual(res.status_code, 200)
        self.assertIsNotNone(self.user.add_by_email)

    @patch("app.models.User.check_token")
    def test_approved_senders(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        self.assertIsNone(self.user.add_by_email)

        res = self.client.get("/api/users/1/senders", headers={"Authorization": "Bearer abc123"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([], self.user.approved_senders.all())
        res = self.client.get("/api/users/1/senders", headers={"Authorization": "Bearer abc123"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([], self.user.approved_senders.all())

        res = self.client.post(
            "api/users/1/senders",
            json={"email": "john@smith.com"},
            headers={"Authorization": "Bearer abc123"},
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(json.loads(res.data)["email"], "john@smith.com")

        res = self.client.get("/api/users/1/senders", headers={"Authorization": "Bearer abc123"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            ["john@smith.com"],
            [str(sender) for sender in self.user.approved_senders.all()],
        )

    @patch("app.models.User.check_token")
    def test_get_user_comms(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        res = self.client.get("/api/users/1/comms", headers={"Authorization": "Bearer abc123"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.data), self.comms.to_dict())

    @patch("app.models.User.check_token")
    def test_update_user_comms(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        self.assertEqual(self.comms.educational, True)
        res = self.client.patch(
            "/api/users/1/comms",
            json={"educational": False},
            headers={"Authorization": "Bearer abc123"},
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.comms.educational, False)
