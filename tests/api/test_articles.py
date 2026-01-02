from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from uuid import uuid4, UUID
from unittest.mock import patch

import sqlalchemy as sa

from app import db
from app.models import Article, User, Tag
from app.api.helpers.query_maker import get_total_count
from app.api.helpers import article_query_maker as aqm
from tests.conftest import BaseTestCase
from tests.mocks.mocks import mock_articles, mock_tags


class MockResponse:
    def __init__(self, text) -> None:
        self.text = text


class AddArticleApiTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        os.environ["testing"] = "1"

        # setup user
        user = User(email="test@test.com")
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        super().tearDown()

    @patch("app.models.user.User.launch_task")
    @patch("app.models.User.check_token")
    def test_add_supplied_epub_article(self, mock_check_token, mock_launch_task):
        from app.models import Task

        mock_check_token.return_value = User.query.first()
        mock_task = Task(id="mock-task-id", name="bg_add_article", user=User.query.first())
        db.session.add(mock_task)
        mock_launch_task.return_value = mock_task

        mock_file = open(f"{Path(os.path.dirname(__file__)).parent}/mocks/mock.epub", "rb")
        payload = {"tags": ["pikachu"]}

        res = self.client.post(
            "/api/articles",
            data={"file": mock_file, "data": json.dumps(payload)},
            headers={"Authorization": "Bearer abc123"},
        )

        data = res.json
        article = Article.query.filter_by(id=1).first()
        tag = article.tags.all()[0]

        self.assertEqual(res.status_code, 201)
        self.assertEqual(str(article.uuid), data["article"]["id"])
        self.assertTrue("task_id" in data)
        self.assertTrue(data["processing"])
        self.assertEqual(tag.name, "pikachu")
        mock_file.close()

    @patch("app.models.user.User.launch_task")
    @patch("app.models.User.check_token")
    def test_add_supplied_pdf_article(self, mock_check_token, mock_launch_task):
        from app.models import Task

        mock_check_token.return_value = User.query.first()
        mock_task = Task(id="mock-task-id", name="bg_add_article", user=User.query.first())
        db.session.add(mock_task)
        mock_launch_task.return_value = mock_task

        mock_file = open(f"{Path(os.path.dirname(__file__)).parent}/mocks/mock.pdf", "rb")

        res = self.client.post(
            "/api/articles",
            data={"file": mock_file},
            headers={"Authorization": "Bearer abc123"},
        )

        data = res.json
        article = Article.query.filter_by(id=1).first()

        self.assertEqual(res.status_code, 201)
        self.assertEqual(str(article.uuid), data["article"]["id"])
        self.assertTrue("task_id" in data)
        self.assertTrue(data["processing"])
        mock_file.close()

    @patch("app.api.helpers.add_article_methods.s3.generate_presigned_url")
    @patch("app.models.User.check_token")
    def test_add_upload_article(self, mock_check_token, mock_s3):
        mock_check_token.return_value = User.query.first()
        mock_s3.return_value = "foo.com"
        payload = {"upload_file_ext": "pdf"}

        res = self.client.post(
            "/api/articles",
            data={"data": json.dumps(payload)},
            headers={"Authorization": "Bearer abc123"},
        )

        data = res.json
        article = Article.query.filter_by(id=1).first()

        self.assertEqual(res.status_code, 201)
        self.assertEqual(str(article.uuid), data["article"]["id"])
        self.assertTrue("upload_url" in data)
        self.assertEqual(data["upload_url"], "foo.com")
        self.assertEqual(".pdf", data["upload_file_ext"])
        self.assertTrue("location" in data)
        self.assertTrue(data["processing"])

    @patch("app.models.User.check_token")
    def test_add_manual_entry(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        payload = {
            "manual_entry": {
                "title": "The road to being a master",
                "content": "This story was 25 years in the making",
                "source": "Nintendo",
            },
            "tags": ["pikachu", "bulbasaur", "charmander"],
            "notes": "Hello old friend!",
        }

        res = self.client.post(
            "/api/articles",
            data={"data": json.dumps(payload)},
            headers={"Authorization": "Bearer abc123"},
        )
        article = Article.query.filter_by(id=1).first()
        tags = [tag.name for tag in article.tags.all()]

        self.assertEqual(res.status_code, 201)
        self.assertEqual(str(article.uuid), res.json.get("article")["id"])
        self.assertEqual("Hello old friend!", article.notes)
        self.assertEqual("The road to being a master", article.title)
        self.assertTrue("This story was 25 years in the making" in article.content)
        for tag in payload["tags"]:
            self.assertTrue(tag in tags)

    @patch("app.api.helpers.add_article_methods.pull_text")
    @patch("app.models.User.check_token")
    def test_add_url_entry(self, mock_check_token, mock_pull_text):
        mock_check_token.return_value = User.query.first()
        mock_pull_text.return_value = {
            "title": "The coolest Title Ever",
            "content": "<p>Is there anybody going to listen to my story?</p>",
        }

        payload = {"url": "https://www.mock.com"}

        res = self.client.post(
            "/api/articles",
            data={"data": json.dumps(payload)},
            headers={"Authorization": "Bearer abc123"},
        )
        article = Article.query.filter_by(id=1).first()

        self.assertEqual(res.status_code, 201)
        self.assertEqual("The coolest Title Ever", res.json["article"]["title"])
        self.assertEqual("https://www.mock.com", article.source_url)
        self.assertEqual("https://www.mock.com", res.json["article"]["source"])
        self.assertTrue("Is there anybody going to listen to my story?" in article.content)

    @patch("app.models.User.check_token")
    def test_article_uploaded_returns_error_without_query_args(self, mock_check_token):
        mock_check_token.return_value = User.query.first()
        article = Article(processing=True)
        db.session.add(article)
        db.session.commit()

        res = self.client.get(
            f"/api/articles/{article.uuid}/uploaded",
            headers={"Authorization": "Bearer abc123"},
        )

        self.assertEqual(res.json["message"], 'upload_file_ext query arg should be ".epub" or ".pdf"')

        args = {"upload_file_ext": "txt"}
        res = self.client.get(
            f"/api/articles/{article.uuid}/uploaded",
            query_string=args,
            headers={"Authorization": "Bearer abc123"},
        )
        self.assertEqual(res.json["message"], 'upload_file_ext query arg should be ".epub" or ".pdf"')

    @patch("app.models.user.User.launch_task")
    @patch("app.models.User.check_token")
    def test_article_uploaded_returns_task_id(self, mock_check_token, mock_launch_task):
        from app.models import Task

        mock_check_token.return_value = User.query.first()
        mock_task = Task(id="mock-task-id", name="bg_add_article", user=User.query.first())
        db.session.add(mock_task)
        mock_launch_task.return_value = mock_task

        article = Article(processing=True, user_id=User.query.first().id)
        db.session.add(article)
        db.session.commit()

        args = {"upload_file_ext": "epub"}
        res = self.client.get(
            f"/api/articles/{article.uuid}/uploaded",
            query_string=args,
            headers={"Authorization": "Bearer abc123"},
        )

        self.assertEqual(res.json["article"]["id"], str(article.uuid))
        self.assertTrue("task_id" in res.json)
        self.assertTrue(res.json["processing"])

    @patch("app.api.helpers.add_article_methods.pull_text")
    @patch("app.models.User.check_token")
    def test_bad_data_returns_400(self, mock_check_token, mock_pull_text):
        mock_check_token.return_value = User.query.first()
        # Simulate URL that returns non-parseable content (like an image)
        mock_pull_text.return_value = {"title": None, "content": None}

        # empty payload
        payload = {"tags": ["pikachu", "bulbasaur", "charmander"]}

        res = self.client.post(
            "/api/articles",
            data={"data": json.dumps(payload)},
            headers={"Authorization": "Bearer abc123"},
        )

        data = res.json
        self.assertEqual(res.status_code, 400)
        self.assertEqual("No article to create. Check data and try again", data["message"])

        # bad url (fails validators.url check before pull_text is called)
        payload = {"url": "foo.bar"}

        res = self.client.post(
            "/api/articles",
            data={"data": json.dumps(payload)},
            headers={"Authorization": "Bearer abc123"},
        )

        data = res.json
        self.assertEqual(res.status_code, 400)
        self.assertEqual("Can't validate url. Please check the data and try again", data["message"])

        # valid url format but content can't be parsed (e.g., image URL)
        payload = {"url": "https://www.example.com/image.png"}

        res = self.client.post(
            "/api/articles",
            data={"data": json.dumps(payload)},
            headers={"Authorization": "Bearer abc123"},
        )

        data = res.json
        self.assertEqual(res.status_code, 400)
        self.assertEqual("Something went wrong. Please check the url", data["message"])

        # manual submission missing data
        payload = {"manual_entry": {"pikachu": "was here"}}

        res = self.client.post(
            "/api/articles",
            data={"data": json.dumps(payload)},
            headers={"Authorization": "Bearer abc123"},
        )

        data = res.json
        self.assertEqual(res.status_code, 400)
        self.assertEqual("Missing Title or Content", data["message"])

        # non pdf or no epub file
        mock_file = open(f"{Path(os.path.dirname(__file__)).parent}/mocks/mocks.py", "rb")

        payload = {"tags": ["pikachu", "bulbasaur", "charmander"]}

        res = self.client.post(
            "/api/articles",
            data={"file": mock_file, "data": json.dumps(payload)},
            headers={"Authorization": "Bearer abc123"},
        )

        data = res.json
        self.assertEqual(res.status_code, 400)
        self.assertEqual("File must be pdf or epub", data["message"])

        # non pdf or no epub file for upload

        payload = {"upload_file_ext": "txt"}

        res = self.client.post(
            "/api/articles",
            data={"data": json.dumps(payload)},
            headers={"Authorization": "Bearer abc123"},
        )

        data = res.json
        self.assertEqual(res.status_code, 400)
        self.assertEqual('upload_file_ext should be ".epub" or ".pdf"', data["message"])


class GetArticleApiTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        os.environ["testing"] = "1"

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
            a = Article(user_id=1)
            for key in article:
                if key != "tags":
                    setattr(a, key, article[key])

            db.session.add(a)
            for tag in article["tags"]:
                t = Tag.query.filter_by(name=tag).first()
                a.add_tag(t)

        # Add a second tag to "baba" article to test duplicate prevention
        # baba already has "pears" (id 3), add "banana" (id 1) too
        baba = Article.query.filter_by(title="baba").first()
        banana_tag = Tag.query.filter_by(name="banana").first()
        baba.add_tag(banana_tag)

        db.session.commit()

    def tearDown(self):
        super().tearDown()

    @patch("app.api.articles.aqm.get_recent_articles")
    @patch("app.api.articles.get_total_count")
    @patch("app.models.User.check_token")
    def test_get_articles(self, mock_check_token, mock_total_count, mock_recent):
        """Test article filtering and pagination.

        Note: get_total_count and get_recent_articles are mocked here
        and tested separately in test_get_total_count and test_get_recent_articles.
        """
        mock_check_token.return_value = User.query.first()
        mock_total_count.return_value = 4
        mock_recent.return_value = []

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

        # then check filter by tags (OR logic, no duplicates)
        # tag_ids 1,3 = banana, pears
        # foo has banana, bar has banana, baba has both banana AND pears
        # Should return 3 articles (not 4 with baba duplicated)
        params = {"tag_ids": "1,3"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(3, len(data["articles"]))
        # Verify no duplicate article IDs
        article_ids = [a["id"] for a in data["articles"]]
        self.assertEqual(len(article_ids), len(set(article_ids)))

        # then check that pagination returns 1 and has_next is True
        params = {"per_page": "1"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(1, len(data["articles"]))
        self.assertTrue(data["has_next"])

        # then check that pagination returns 4 and has_next is False
        params = {"per_page": "4"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(4, len(data["articles"]))
        self.assertFalse(data["has_next"])

        # then check that pagination returns all and has_next is False
        params = {"per_page": "all"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(4, len(data["articles"]))
        self.assertFalse(data["has_next"])

        # then check that we can get the last page
        params = {"per_page": "1", "page": "4"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(1, len(data["articles"]))
        self.assertFalse(data["has_next"])

        # then check that we can get the 2nd page and has_next is True
        params = {"per_page": "1", "page": "2"}
        res = self.client.get(
            "/api/articles",
            query_string=params,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(1, len(data["articles"]))
        self.assertTrue(data["has_next"])

    def test_get_total_count(self):
        """Test that get_total_count returns correct count for filtered queries."""
        user = User.query.first()

        # Base query - should count 5 total articles
        stmt = sa.select(Article).where(
            Article.user_id == user.id,
            Article.processing.isnot(True),
        )
        self.assertEqual(get_total_count(stmt), 5)

        # With status filter - archived
        filtered_stmt = aqm.filter_by_status(stmt, "archived")
        self.assertEqual(get_total_count(filtered_stmt), 1)

        # With status filter - unread
        filtered_stmt = aqm.filter_by_status(stmt, "unread")
        self.assertEqual(get_total_count(filtered_stmt), 1)

        # With search filter
        filtered_stmt = aqm.filter_by_search_phrase(stmt, "baz")
        self.assertEqual(get_total_count(filtered_stmt), 1)

    def test_get_recent_articles(self):
        """Test that get_recent_articles returns most recently read articles."""
        user = User.query.first()

        # Should return up to 3 most recent articles with date_read set
        recent = aqm.get_recent_articles(user.id, limit=3)
        self.assertLessEqual(len(recent), 3)

        # All returned articles should have date_read set
        for article in recent:
            self.assertIsNotNone(article.date_read)

        # Should be ordered by date_read desc (most recent first)
        if len(recent) > 1:
            for i in range(len(recent) - 1):
                self.assertGreaterEqual(recent[i].date_read, recent[i + 1].date_read)

        # Should not include archived articles
        for article in recent:
            self.assertFalse(article.archived)


class UpdateArticleApiTests(BaseTestCase):
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
    def test_no_article_returns_error(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        id = str(uuid4())
        body = {}
        res = self.client.patch(
            "/api/articles/" + id,
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(404, res.status_code)
        self.assertEqual("The resource can't be found", data["message"])

    @patch("app.models.User.check_token")
    def test_no_data_returns_error(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        article = Article(user_id=User.query.first().id, title="Hello World")
        db.session.add(article)
        db.session.commit()

        res = self.client.patch(
            "/api/articles/" + str(article.uuid),
            headers={"Authorization": "Bearer abc123"},
        )

        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data.get("message"), "Check data")

    @patch("app.models.User.check_token")
    def test_article_updates_only_allowed_fields(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        article = Article(user_id=User.query.first().id, title="Hello World")
        db.session.add(article)
        db.session.commit()

        new_date = datetime.utcnow() + timedelta(days=1)

        body = {
            "article_created_date": new_date,
            "title": "Goodbye Cruel World",
            "notes": "This is a note",
        }

        res = self.client.patch(
            "/api/articles/" + str(article.uuid),
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )

        data = json.loads(res.data)

        self.assertEqual(article.notes, "This is a note")
        self.assertEqual(article.title, "Goodbye Cruel World")
        self.assertNotEqual(article.article_created_date, new_date)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["article"]["title"], article.title)

    @patch("app.models.User.check_token")
    def test_article_updates_tags(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        article = Article(user_id=User.query.first().id, title="Hello World")
        db.session.add(article)
        db.session.commit()

        tags = ["pikachu", "bulbasaur", "charmander"]
        for tag in tags:
            new_tag = Tag(name=tag, user_id=User.query.first().id)
            db.session.add(new_tag)
            article.add_tag(new_tag)

        db.session.commit()

        self.assertEqual(article.tag_list, tags)

        body = {"tags": ["charmander", "bulbasaur", "squirtle"]}

        res = self.client.patch(
            "/api/articles/" + str(article.uuid),
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )

        self.assertEqual(res.status_code, 200)
        self.assertCountEqual(article.tag_list, body["tags"])


class DeleteArticleApiTests(BaseTestCase):
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
    def test_no_article_returns_error(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        id = str(uuid4())
        body = {}
        res = self.client.delete(
            "/api/articles/" + id,
            json=body,
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)
        self.assertEqual(400, res.status_code)
        self.assertEqual("The resource can't be found", data["message"])

    @patch("app.models.User.check_token")
    def test_article_deletes(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        article = Article(user_id=User.query.first().id, title="Hello World")
        db.session.add(article)
        db.session.commit()

        id = str(article.uuid)
        res = self.client.delete("/api/articles/" + id, headers={"Authorization": "Bearer abc123"})
        self.assertEqual(res.status_code, 200)

        article = Article.query.filter_by(uuid=UUID(id)).first()
        self.assertIsNone(article)


class ExportArticleApiTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        os.environ["testing"] = "1"

        # setup user
        user = User(email="test@test.com")
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        super().tearDown()

    @patch("app.tasks.send_email")
    @patch("app.tasks.s3")
    @patch("app.models.User.check_token")
    def test_export_article_returns_task(self, mock_check_token, mock_s3, mock_send_email):
        mock_check_token.return_value = User.query.first()

        article = Article(
            user_id=User.query.first().id,
            title="Alabama Arkansaw I do Love My Ma and Pa",
        )
        db.session.add(article)
        db.session.commit()

        res = self.client.get(
            f"/api/articles/{str(article.uuid)}/export?export_file_ext=csv",
            headers={"Authorization": "Bearer abc123"},
        )
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertTrue("task_id" in data)
        self.assertIsNotNone(data["task_id"])

        self.assertTrue("location" in data)
        self.assertIsNotNone(data["location"])

        self.assertTrue(data["processing"])
        self.assertEqual(mock_s3.upload_file.call_count, 1)
        self.assertEqual(mock_s3.generate_presigned_url.call_count, 1)
        self.assertEqual(mock_send_email.call_count, 1)
