from bs4 import BeautifulSoup
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, call
from zipfile import ZipFile

from app import db, create_app
from app.models import User
from app.helpers.ebooks import process_images, process_links
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    MAIL_SUPPRESS_SEND = True


class EbookProcessingTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.temp_dir = tempfile.mkdtemp()
        db.create_all()

        user = User(email="hello@world.com")
        db.session.add(user)
        db.session.commit()
        self.user = user

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        shutil.rmtree(self.temp_dir)

    def test_process_images(self):
        epub_file = os.path.join(os.path.dirname(__file__), "../mocks", "mock.epub")

        soup = BeautifulSoup(
            """
            <html>
                <body>
                    <img src="images/pikachu.jpg">
                    <image xlink:href="images/bulbasaur.jpg">
                </body>
            </html>
            """,
            "lxml",
        )
        with patch("app.helpers.ebooks.s3") as mock_s3:
            with patch("app.helpers.ebooks.find_img_path") as mock_find_img:
                mock_find_img.return_value = "path/to/img/"
                soup = process_images(soup, epub_file, self.user)

        image_tag = soup.find("image")
        img_tag = soup.find("img")
        self.assertIsNotNone(image_tag)
        self.assertIsNotNone(img_tag)
        self.assertTrue(
            image_tag["xlink:href"] == "/download/1/staging/1/test.epub/bulbasaur.jpg"
            or image_tag["xlink:href"] == "/download/1/1/test.epub/bulbasaur.jpg"
        )
        self.assertTrue(
            img_tag["src"] == "/download/1/staging/1/test.epub/pikachu.jpg"
            or img_tag["src"] == "/download/1/1/test.epub/pikachu.jpg"
        )

    def test_process_links(self):
        html = """
            <html>
                <body>
                    <a href="#section1">Link1</a>
                    <a href="http://example.com">Link2</a>
                    <a href="https://example.com">Link3</a>
                    <a href="http://example.com#canary">Link4</a>
                    <a href="path/to/local/file">Link5</a>
                </body>
            </html>
            """
        soup = BeautifulSoup(html, "html.parser")
        soup = process_links(soup)

        # Check that the simple anchor tag was untouched
        link1 = soup.find_all("a")[0]
        self.assertEqual(link1["href"], "#section1")

        # Check that the http link has been left untouched
        link2 = soup.find_all("a")[1]
        self.assertEqual(link2["href"], "http://example.com")

        # Check that the https link has been left untouched
        link3 = soup.find_all("a")[2]
        self.assertEqual(link3["href"], "https://example.com")

        # Check that the http link with an anchor tag was modified
        link4 = soup.find_all("a")[3]
        self.assertEqual(link4["href"], "#canary")

        # Check that any other hrefs have been removed
        link5 = soup.find_all("a")[4]
        self.assertEqual(link5["href"], "")
