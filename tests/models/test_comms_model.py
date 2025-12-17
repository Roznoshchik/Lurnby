from app import db
from app.models import User
from tests.conftest import BaseTestCase


class CommsTest(BaseTestCase):

    def test_repr(self):
        user = User(email="test1@example.com")
        db.session.add(user)
        db.session.commit()

        comms = user.comms

        expected = (
            f"<User {user.id}>\n"
            "informational: True, educational: True, "
            "promotional: True, highlights: True, "
            "reminders: True"
        )
        self.assertEqual(repr(comms), expected)

    def test_to_dict(self):
        user = User(email="test2@example.com")
        db.session.add(user)
        db.session.commit()

        comms = user.comms
        comms.informational = False
        comms.educational = False
        comms.promotional = False
        comms.highlights = False
        comms.reminders = False
        db.session.commit()

        self.assertEqual(
            comms.to_dict(),
            {
                "id": comms.id,
                "user_id": user.id,
                "informational": False,
                "educational": False,
                "promotional": False,
                "highlights": False,
                "reminders": False,
            },
        )

    def test_defaults(self):
        user = User(email="test3@example.com")
        db.session.add(user)
        db.session.commit()

        comms = user.comms
        self.assertEqual(comms.informational, True)
        self.assertEqual(comms.educational, True)
        self.assertEqual(comms.promotional, True)
        self.assertEqual(comms.highlights, True)
        self.assertEqual(comms.reminders, True)
