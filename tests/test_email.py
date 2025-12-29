from flask_mail import Message
import unittest
from unittest.mock import patch
from app import db, create_app
from app.email import send_email, mail
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    MAIL_SUPPRESS_SEND = True


class SendEmail(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch.object(mail, "send")
    def test_send_email(self, mock_send):
        with patch.object(mail, "send") as mock_send:
            subject = "Test Subject"
            sender = "test@example.com"
            recipients = ["recipient@example.com"]
            text_body = "This is a test message"
            html_body = "<h1>This is a test message</h1>"
            send_email(subject, sender, recipients, text_body, html_body)

            expected_msg = Message(subject=subject, sender=sender, recipients=recipients)
            expected_msg.body = text_body
            expected_msg.html = html_body

            sent_msg = mock_send.call_args_list[0][0][0]

            self.assertEqual(sent_msg.subject, expected_msg.subject)
            self.assertEqual(sent_msg.sender, expected_msg.sender)
            self.assertEqual(sent_msg.recipients, expected_msg.recipients)
            self.assertEqual(sent_msg.body, expected_msg.body)
            self.assertEqual(sent_msg.html, expected_msg.html)
