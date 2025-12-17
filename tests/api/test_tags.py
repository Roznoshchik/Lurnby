import json
import os
from unittest.mock import patch
from app import db
from app.models import User, Tag
from tests.conftest import BaseTestCase


class MockResponse:
    def __init__(self, text) -> None:
        self.text = text


class GetTagsApiTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        os.environ["testing"] = "1"

        # setup user
        user = User(email="test@test.com")
        db.session.add(user)
        db.session.commit()

        # setup tags
        t1 = Tag(user_id=user.id, name="pikachu")
        t2 = Tag(user_id=user.id, name="bulbasaur")
        t3 = Tag(user_id=user.id, name="charmander")
        t4 = Tag(user_id=user.id, name="squirtle", archived=True)

        db.session.add_all([t1, t2, t3, t4])
        db.session.commit()

    def tearDown(self):
        super().tearDown()

    @patch("app.models.User.check_token")
    def test_get_unarchived_tags(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        # first check default which should return 9 unarchived highlights
        params = {}
        res = self.client.get(
            "/api/tags",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("tags")), 3)

    @patch("app.models.User.check_token")
    def test_get_archived_tags(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        # return 1 archived highlight
        params = {"status": "archived"}
        res = self.client.get(
            "/api/tags",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("tags")), 1)

    @patch("app.models.User.check_token")
    def test_get_all_tags(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        # return 1 archived highlight
        params = {"status": "all"}
        res = self.client.get(
            "/api/tags",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("tags")), 4)

    @patch("app.models.User.check_token")
    def test_pagination(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        # return 1 archived highlight
        params = {"per_page": "1"}
        res = self.client.get(
            "/api/tags",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("tags")), 1)
        self.assertTrue(data.get("has_next"))

        params = {"page": "3", "per_page": "1"}
        res = self.client.get(
            "/api/tags",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(len(data.get("tags")), 1)
        self.assertFalse(data.get("has_next"))


class AddTagApiTests(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        os.environ["testing"] = "1"

        # setup user
        user = User(email="test@test.com")
        db.session.add(user)
        db.session.commit()

    def tearDown(self) -> None:
        super().tearDown()

    @patch("app.models.User.check_token")
    def test_add_new_highlight(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        body = {
            "name": "foo",
        }

        res = self.client.post(
            "/api/tags",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        tag = data.get("tag")

        self.assertEqual(tag.get("name"), body.get("name"))
        self.assertEqual(tag.get("highlight_count"), 0)
        self.assertEqual(tag.get("article_count"), 0)

    @patch("app.models.User.check_token")
    def test_add_new_tag_with_passed_uuid(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        body = {
            "name": "Foo",
            "uuid": "abc123",
        }

        res = self.client.post(
            "/api/tags",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        tag = data.get("tag")

        self.assertEqual(tag.get("uuid"), body.get("uuid"))
        self.assertEqual(tag.get("name"), body.get("name"))


class GetTagApiTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        os.environ["testing"] = "1"

        # setup user
        user = User(email="test@test.com")
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        super().tearDown()

    @patch("app.models.User.check_token")
    def test_no_tag_returns_error(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        body = {}
        res = self.client.get(
            "/api/tags/random",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(404, res.status_code)
        self.assertEqual("Resource not found", data["message"])

    @patch("app.models.User.check_token")
    def test_tag_returns(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        tag = Tag(user_id=User.query.first().id, name="Hello World")
        db.session.add(tag)
        db.session.commit()

        uuid = tag.uuid
        res = self.client.get(
            "/api/tags/" + uuid, headers={"Authorization": "Bearer abc123"}
        )
        data = json.loads(res.data)
        returned_tag = data.get("tag")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(tag.name, returned_tag.get("name"))


class UpdateTagApiTests(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        os.environ["testing"] = "1"

        # setup user
        user = User(email="test@test.com")
        db.session.add(user)
        db.session.commit()

    def tearDown(self) -> None:
        super().tearDown()

    @patch("app.models.User.check_token")
    def test_update_tag(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        tag = Tag(user_id=user.id, name="Foo")

        db.session.add(tag)
        db.session.commit()

        body = {
            "name": "pikachu",
            "archived": True,
        }

        res = self.client.patch(
            f"/api/tags/{tag.uuid}",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        tag = data.get("tag")
        self.assertEqual(tag.get("name"), body.get("name"))
        self.assertTrue(tag.get("archived"))

    @patch("app.models.User.check_token")
    def test_update_tag_ignores_fields(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        tag = Tag(user_id=user.id, name="Foo")

        db.session.add(tag)
        db.session.commit()

        body = {
            "uuid": "12345abc",
            "id": "55",
            "name": "hello old friend",
        }

        self.client.patch(
            f"/api/tags/{tag.uuid}",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )

        self.assertNotEqual(tag.uuid, body.get("uuid"))
        self.assertNotEqual(tag.id, body.get("id"))
        self.assertEqual(tag.name, body.get("name"))

    @patch("app.models.User.check_token")
    def test_update_tag_errors(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        tag = Tag(user_id=user.id, name="Foo")

        db.session.add(tag)
        db.session.commit()

        # json error
        body = None

        res = self.client.patch(
            f"/api/highlights/{tag.uuid}",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(data.get("message"), "Check data")

        # nonexistent article
        body = {"text": "foo"}

        res = self.client.patch(
            "/api/highlights/random",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(data.get("message"), "Resource not found")

        tag2 = Tag(user_id=2)
        db.session.add(tag2)
        db.session.commit()

        # wrong user
        body = {"text": "foo"}

        res = self.client.patch(
            f"/api/highlights/{tag2.uuid}",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(data.get("message"), "Resource not found")


class DeleteTagApiTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        os.environ["testing"] = "1"

        # setup user
        user = User(email="test@test.com")
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        super().tearDown()

    @patch("app.models.User.check_token")
    def test_no_tag_returns_error(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        body = {}
        res = self.client.delete(
            "/api/tags/random",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(404, res.status_code)
        self.assertEqual("Resource not found", data["message"])

    @patch("app.models.User.check_token")
    def test_tag_deletes(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        tag = Tag(user_id=User.query.first().id, name="Hello World")
        db.session.add(tag)
        db.session.commit()

        uuid = tag.uuid
        res = self.client.delete(
            "/api/tags/" + uuid, headers={"Authorization": "Bearer abc123"}
        )
        self.assertEqual(res.status_code, 200)

        tag = Tag.query.filter_by(uuid=uuid).first()
        self.assertIsNone(tag)
