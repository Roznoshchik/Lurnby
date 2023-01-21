import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from app import create_app, db
from app.models import Article, User
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


class MockResponse:
    def __init__(self, text) -> None:
        self.text = text


class AddArticleApiTests(unittest.TestCase):
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
    def test_add_supplied_epub_article(self, mock_check_token):
        mock_check_token.return_value = User.query.first()
        mock_file = open(
            f"{Path(os.path.dirname(__file__)).parent.parent}/mocks/mock.epub", "rb"
        )
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
        self.assertEqual(str(article.uuid), data["article_id"])
        self.assertTrue("task_id" in data)
        self.assertTrue(data["processing"])
        self.assertEqual(tag.name, "pikachu")

    @patch("app.models.User.check_token")
    def test_add_supplied_pdf_article(self, mock_check_token):
        mock_check_token.return_value = User.query.first()
        mock_file = open(
            f"{Path(os.path.dirname(__file__)).parent.parent}/mocks/mock.pdf", "rb"
        )
        # payload = {"tags": ["pikachu"]}

        res = self.client.post(
            "/api/articles",
            data={"file": mock_file},
            headers={"Authorization": "Bearer abc123"},
        )

        data = res.json
        article = Article.query.filter_by(id=1).first()

        self.assertEqual(res.status_code, 201)
        self.assertEqual(str(article.uuid), data["article_id"])
        self.assertTrue("task_id" in data)
        self.assertTrue(data["processing"])

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
        self.assertEqual(str(article.uuid), data["article_id"])
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

    @patch("app.main.pulltext.requests.get")
    @patch("app.models.User.check_token")
    def test_add_url_entry(self, mock_check_token, mock_get):
        mock_check_token.return_value = User.query.first()
        with open(
            f"{Path(os.path.dirname(__file__)).parent.parent}/mocks/mock_html_req.txt",
            "r",
        ) as file:
            html = file.read()

        mock_get.return_value = MockResponse(html)

        payload = {"url": "https://www.mock.com"}

        res = self.client.post(
            "/api/articles",
            data={"data": json.dumps(payload)},
            headers={"Authorization": "Bearer abc123"},
        )
        article = Article.query.filter_by(id=1).first()

        self.assertEqual(res.status_code, 201)
        self.assertEqual("The coolest Title Ever", res.json["article"]["title"])
        self.assertTrue(
            "Is there anybody going to listen to my story?" in article.content
        )

    @patch("app.models.User.check_token")
    def test_bad_data_returns_400(self, mock_check_token):
        mock_check_token.return_value = User.query.first()

        # empty payload
        payload = {"tags": ["pikachu", "bulbasaur", "charmander"]}

        res = self.client.post(
            "/api/articles",
            data={"data": json.dumps(payload)},
            headers={"Authorization": "Bearer abc123"},
        )

        data = res.json
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            "No article to create. Check data and try again", data["message"]
        )

        # bad url
        payload = {"url": "foo.bar"}

        res = self.client.post(
            "/api/articles",
            data={"data": json.dumps(payload)},
            headers={"Authorization": "Bearer abc123"},
        )

        data = res.json
        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            "Can't validate url. Please check the data and try again", data["message"]
        )

        # bad url that passes validators check
        payload = {"url": "https://www.lurnby.com/static/images/rrfeedback-40.png"}

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
        mock_file = open(
            f"{Path(os.path.dirname(__file__)).parent.parent}/mocks/mocks.py", "rb"
        )

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
