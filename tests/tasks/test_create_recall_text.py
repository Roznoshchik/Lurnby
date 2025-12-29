import unittest
from unittest.mock import patch
from app import db, create_app
from app.models import Highlight
from app.tasks import create_recall_text
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


class RecallTextCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch("app.tasks.logger.error")
    def test_highlight_not_found(self, mock_logger_error):
        # Test the case where the highlight doesn't exist
        result = create_recall_text(1)
        mock_logger_error.assert_called_once_with("Couldn't find highlight with id: 1")
        self.assertIsNone(result)

    def test_highlight_found(self):
        # Test the case where the highlight exists
        highlight = Highlight(text="Alan Walker went to Tokyo for his honeymoon.")
        db.session.add(highlight)
        db.session.commit()
        create_recall_text(highlight.id)
        self.assertTrue("Alan" in highlight.prompt)
        self.assertTrue("Walker" in highlight.prompt)
        self.assertTrue("Tokyo" in highlight.prompt)
        self.assertTrue("to" in highlight.prompt)
        self.assertTrue("for" in highlight.prompt)
        self.assertTrue("his" in highlight.prompt)

        highlight2 = Highlight(text="stop right this minute.")
        db.session.add(highlight2)
        db.session.commit()
        create_recall_text(highlight2.id)

        self.assertTrue("_____" in highlight2.prompt)
