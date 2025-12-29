import fitz
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from app import db, create_app
from app.models import User
from app.helpers.pdf import (
    process_images_and_get_url_dict,
    create_sizes_to_header_tags_dict,
)
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    MAIL_SUPPRESS_SEND = True


class PDFProcessingTests(unittest.TestCase):
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
        pdf_file = os.path.join(os.path.dirname(__file__), "../mocks", "test.pdf")
        pdf_doc = fitz.open(pdf_file)
        title_for_dir = "foo_bar_baz"

        expected_staging_dict = {
            4: '<img src =/download/1/staging/1/foo_bar_baz/0.jpeg loading="lazy">',
            24: '<img src =/download/1/staging/1/foo_bar_baz/1.jpeg loading="lazy">',
            25: '<img src =/download/1/staging/1/foo_bar_baz/2.jpeg loading="lazy">',
            26: '<img src =/download/1/staging/1/foo_bar_baz/3.jpeg loading="lazy">',
        }

        expected_non_staging_dict = {
            4: '<img src =/download/1/1/foo_bar_baz/0.jpeg loading="lazy">',
            24: '<img src =/download/1/1/foo_bar_baz/1.jpeg loading="lazy">',
            25: '<img src =/download/1/1/foo_bar_baz/2.jpeg loading="lazy">',
            26: '<img src =/download/1/1/foo_bar_baz/3.jpeg loading="lazy">',
        }

        with patch("app.helpers.pdf.s3"):
            url_dict = process_images_and_get_url_dict(pdf_doc, title_for_dir, self.user)

        if os.environ.get("DEV"):
            self.assertDictEqual(url_dict, expected_staging_dict)
        else:
            self.assertDictEqual(url_dict, expected_non_staging_dict)

    def test_create_sizes_to_header_tags_dict(self):
        # Mock pdf_doc and its get_text method to return test data
        page1 = {
            "blocks": [
                {
                    "type": 0,
                    "lines": [
                        {
                            "spans": [
                                {"size": 15},
                                {"size": 16},
                                {"size": 17},
                                {"size": 18},
                                {"size": 19},
                                {"size": 24},
                                {"size": 36},
                                {"size": 51},
                            ]
                        }
                    ],
                }
            ]
        }

        pdf_doc = [MagicMock(get_text=MagicMock(return_value=page1))]

        # Call the function and check the output
        expected_sizes = {
            15: "p",
            16: "p",
            17: "h5",
            18: "h5",
            19: "h5",
            24: "h4",
            36: "h2",
            51: "h1",
        }
        actual_sizes = create_sizes_to_header_tags_dict(pdf_doc)
        self.assertEqual(expected_sizes, actual_sizes)
