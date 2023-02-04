import json
import os

from random import randrange
import unittest

from app import create_app, db
from app.api.errors import LurnbyValueError
from app.helpers.export_helpers import (
    create_zip_file_for_article,
    get_highlights_export,
    export_to_csv,
    export_to_json,
    export_to_txt,
    create_plain_text_article_dict,
    create_list_of_highlight_dicts,
)
from app.models import Article, User, Tag, Highlight

from config import Config
from tests.mocks.mocks import mock_articles, mock_tags, mock_highlight


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


class ExportArticleTests(unittest.TestCase):
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
            a = Article(user_id=1)
            for key in article:
                if key != "tags":
                    setattr(a, key, article[key])

            for tag in article["tags"]:
                t = Tag.query.filter_by(name=tag).first()
            db.session.add(a)
            a.AddToTag(t)

            for _ in range(randrange(10)):
                highlight = Highlight(user_id=1, article_id=a.id)

                for key in mock_highlight:
                    setattr(highlight, key, mock_highlight[key])

                db.session.add(highlight)

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_zip_file_fails_with_wrong_ext(self):
        article = Article.query.first()

        basedir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(basedir, "temp")

        if not os.path.isdir(path):
            os.mkdir(path)

        with self.assertRaises(LurnbyValueError) as cm:
            create_zip_file_for_article(article, path, "pikachu")

        self.assertEqual(
            str(cm.exception), 'ext must be one of "csv", "txt", or "json"'
        )

    def test_zip_file_exists(self):
        article = Article.query.first()

        basedir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(basedir, "temp")

        if not os.path.isdir(path):
            os.mkdir(path)

        zip_path = create_zip_file_for_article(article, path, "json")

        self.assertTrue(os.path.exists(zip_path))
        os.remove(zip_path)

    def test_export_to_json(self):
        article = Article.query.first()
        article_dict = create_plain_text_article_dict(article)
        article_highlights = create_list_of_highlight_dicts(article.highlights.all())

        basedir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(basedir, "temp")

        if not os.path.isdir(path):
            os.mkdir(path)

        article_path, highlights_path = export_to_json(
            path, article_dict, article_highlights
        )

        with open(article_path, "r") as file:
            loaded_article = json.loads(file.read())

        with open(highlights_path, "r") as file:
            loaded_highlights = json.loads(file.read())

        self.assertEqual(loaded_article["title"], article.title)
        self.assertTrue(loaded_article["notes"] in article.notes)
        self.assertTrue(len(loaded_highlights) == len(article.highlights.all()))
        self.assertTrue(os.path.exists(article_path))
        self.assertTrue(os.path.exists(highlights_path))

        os.remove(article_path)
        os.remove(highlights_path)

    def test_export_to_text(self):
        article = Article.query.first()
        article_dict = create_plain_text_article_dict(article)
        article_highlights = create_list_of_highlight_dicts(article.highlights.all())

        basedir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(basedir, "temp")

        if not os.path.isdir(path):
            os.mkdir(path)

        article_path, highlights_path = export_to_txt(
            path, article_dict, article_highlights
        )

        self.assertTrue(os.path.exists(article_path))
        self.assertTrue(os.path.exists(highlights_path))

        os.remove(article_path)
        os.remove(highlights_path)

    def test_export_to_csv(self):
        article = Article.query.first()
        article_dict = create_plain_text_article_dict(article)
        article_highlights = create_list_of_highlight_dicts(article.highlights.all())

        basedir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(basedir, "temp")

        if not os.path.isdir(path):
            os.mkdir(path)

        article_path, highlights_path = export_to_csv(
            path, article_dict, article_highlights
        )

        self.assertTrue(os.path.exists(article_path))
        self.assertTrue(os.path.exists(highlights_path))

        os.remove(article_path)
        os.remove(highlights_path)


class ExportHighlightTests(unittest.TestCase):
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
            a = Article(user_id=1)
            for key in article:
                if key != "tags":
                    setattr(a, key, article[key])

            for tag in article["tags"]:
                t = Tag.query.filter_by(name=tag).first()
            db.session.add(a)
            a.AddToTag(t)

            for _ in range(randrange(10)):
                highlight = Highlight(user_id=1, article_id=a.id)

                for key in mock_highlight:
                    setattr(highlight, key, mock_highlight[key])

                db.session.add(highlight)

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_zip_file_fails_with_wrong_ext(self):
        user = User.query.first()
        highlights = user.highlights.all()

        basedir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(basedir, "temp")

        if not os.path.isdir(path):
            os.mkdir(path)

        with self.assertRaises(LurnbyValueError) as cm:
            get_highlights_export(highlights, path, "pikachu")

        self.assertEqual(
            str(cm.exception), 'ext must be one of "csv", "txt", or "json"'
        )

    def test_zip_file_exists(self):
        user = User.query.first()
        highlights = user.highlights.all()

        basedir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(basedir, "temp")

        if not os.path.isdir(path):
            os.mkdir(path)

        zip_path = get_highlights_export(highlights, path, "json")

        self.assertTrue(os.path.exists(zip_path))
        os.remove(zip_path)

    def test_export_to_json(self):
        user = User.query.first()
        highlights = user.highlights.all()
        highlights = create_list_of_highlight_dicts(highlights)

        basedir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(basedir, "temp")

        if not os.path.isdir(path):
            os.mkdir(path)

        article_path, highlights_path = export_to_json(path, None, highlights)

        with open(highlights_path, "r") as file:
            loaded_highlights = json.loads(file.read())

        self.assertTrue(len(loaded_highlights) == len(user.highlights.all()))
        self.assertTrue(os.path.exists(highlights_path))
        self.assertFalse(os.path.exists(article_path))

        os.remove(highlights_path)

    def test_export_to_text(self):
        user = User.query.first()
        highlights = user.highlights.all()
        highlights = create_list_of_highlight_dicts(highlights)

        basedir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(basedir, "temp")

        if not os.path.isdir(path):
            os.mkdir(path)

        article_path, highlights_path = export_to_txt(path, None, highlights)

        self.assertFalse(os.path.exists(article_path))
        self.assertTrue(os.path.exists(highlights_path))

        os.remove(highlights_path)

    def test_export_to_csv(self):
        user = User.query.first()
        highlights = user.highlights.all()
        highlights = create_list_of_highlight_dicts(highlights)

        basedir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(basedir, "temp")

        if not os.path.isdir(path):
            os.mkdir(path)

        article_path, highlights_path = export_to_csv(path, None, highlights)

        self.assertFalse(os.path.exists(article_path))
        self.assertTrue(os.path.exists(highlights_path))

        os.remove(highlights_path)
