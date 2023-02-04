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


class AddHighlightApiTests(unittest.TestCase):
    def setUp(self) -> None:
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
        return super().setUp()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        return super().tearDown()

    @patch("app.models.User.check_token")
    def test_add_new_highlight(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        body = {
            "text": "hello old friend",
            "note": "this is super fun",
            "source": "my favorite friend!",
        }

        res = self.client.post(
            "/api/highlights",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        highlight = data.get("highlight")
        self.assertEqual(highlight.get("text"), body.get("text"))
        self.assertEqual(highlight.get("note"), body.get("note"))
        self.assertEqual(highlight.get("source"), body.get("source"))
        self.assertIsNotNone(highlight.get("prompt"))
        self.assertIsNotNone(highlight.get("uuid"))
        self.assertIsNotNone(highlight.get("id"))
        self.assertTrue(highlight.get("untagged"))
        self.assertFalse(highlight.get("archived"))

    @patch("app.models.User.check_token")
    def test_add_new_highlight_with_passed_uuid(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        body = {
            "text": "hello old friend",
            "note": "this is super fun",
            "source": "my favorite friend!",
            "uuid": "abc123",
            "id": 4,
        }

        res = self.client.post(
            "/api/highlights",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        highlight = data.get("highlight")

        self.assertEqual(highlight.get("uuid"), body.get("uuid"))
        self.assertNotEqual(highlight.get("id"), body.get("id"))
        self.assertEqual(highlight.get("text"), body.get("text"))
        self.assertEqual(highlight.get("note"), body.get("note"))
        self.assertEqual(highlight.get("source"), body.get("source"))

    @patch("app.models.User.check_token")
    def test_add_new_highlight_attributes_source(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        article = Article(title="A tree grows in Brooklyn", user_id=user.id)
        db.session.add(article)
        db.session.commit()

        body = {
            "text": "hello old friend",
            "source": "my favorite friend!",
            "article_id": str(article.uuid),
        }

        res = self.client.post(
            "/api/highlights",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        highlight = data.get("highlight")

        self.assertEqual(highlight.get("source"), body.get("source"))

        body = {
            "text": "hello old friend",
            "article_id": str(article.uuid),
        }

        res = self.client.post(
            "/api/highlights",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        highlight = data.get("highlight")

        self.assertEqual(highlight.get("source"), article.title)

        body = {
            "text": "hello old friend",
        }

        res = self.client.post(
            "/api/highlights",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        highlight = data.get("highlight")

        self.assertEqual(highlight.get("source"), "unknown")

    @patch("app.models.User.check_token")
    def test_add_new_highlight_with_tags(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        body = {
            "text": "hello old friend",
            "note": "this is super fun",
            "source": "my favorite friend!",
            "tags": ["pikachu", "bulbasaur", "charmander"],
        }

        res = self.client.post(
            "/api/highlights",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        highlight = data.get("highlight")

        self.assertCountEqual(
            [tag.get("name") for tag in highlight.get("tags")], body.get("tags")
        )

    @patch("app.models.User.check_token")
    def test_add_new_highlight_fails_with_bad_data(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        highlight1 = Highlight(user_id=user.id)
        db.session.add(highlight1)
        db.session.commit()

        body = {
            "uuid": highlight1.uuid,
            "text": "hello old friend",
            "note": "this is super fun",
            "source": "my favorite friend!",
        }

        res = self.client.post(
            "/api/highlights",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            data.get("message"), "Highlight exists, use update methods instead."
        )

        body = {"note": "this is super fun", "source": "my favorite friend!"}

        res = self.client.post(
            "/api/highlights",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data.get("message"), "Text is a required field")


class UpdateHighlightApiTests(unittest.TestCase):
    def setUp(self) -> None:
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
        return super().setUp()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        return super().tearDown()

    @patch("app.models.User.check_token")
    def test_update_highlight(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        highlight = Highlight(user_id=user.id, text="Foo", note="Bar", source="Baz")

        db.session.add(highlight)
        db.session.commit()

        body = {
            "text": "hello old friend",
            "note": "this is super fun",
            "source": "my favorite friend!",
        }

        res = self.client.patch(
            f"/api/highlights/{highlight.uuid}",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        highlight = data.get("highlight")
        self.assertEqual(highlight.get("text"), body.get("text"))
        self.assertEqual(highlight.get("note"), body.get("note"))
        self.assertEqual(highlight.get("source"), body.get("source"))

    @patch("app.models.User.check_token")
    def test_update_highlight_ignores_fields(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        highlight = Highlight(user_id=user.id, text="Foo", note="Bar", source="Baz")

        db.session.add(highlight)
        db.session.commit()

        body = {
            "uuid": "12345abc",
            "id": "55",
            "text": "hello old friend",
            "note": "this is super fun",
            "source": "my favorite friend!",
        }

        self.client.patch(
            f"/api/highlights/{highlight.uuid}",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )

        self.assertNotEqual(highlight.uuid, body.get("uuid"))
        self.assertNotEqual(highlight.id, body.get("id"))
        self.assertEqual(highlight.text, body.get("text"))
        self.assertEqual(highlight.note, body.get("note"))
        self.assertEqual(highlight.source, body.get("source"))

    @patch("app.models.User.check_token")
    def test_update_highlight_tags(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        highlight = Highlight(user_id=user.id, text="Foo", note="Bar", source="Baz")

        db.session.add(highlight)
        db.session.commit()

        body = {"tags": ["pikachu", "bulbasaur", "charmander"]}

        res = self.client.patch(
            f"/api/highlights/{highlight.uuid}",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        returned_highlight = data.get("highlight")
        self.assertCountEqual(
            highlight.to_dict().get("tags"), returned_highlight.get("tags")
        )
        self.assertCountEqual(highlight.tag_list, body.get("tags"))

    @patch("app.models.User.check_token")
    def test_update_highlight_errors(self, mock_check_token):
        user = User.query.first()
        mock_check_token.return_value = user

        highlight = Highlight(user_id=user.id, text="Foo", note="Bar", source="Baz")

        db.session.add(highlight)
        db.session.commit()

        # json error
        body = None

        res = self.client.patch(
            f"/api/highlights/{highlight.uuid}",
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

        highlight2 = Highlight(user_id=2)
        db.session.add(highlight2)
        db.session.commit()

        # wrong user
        body = {"text": "foo"}

        res = self.client.patch(
            f"/api/highlights/{highlight2.uuid}",
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(data.get("message"), "Resource not found")
