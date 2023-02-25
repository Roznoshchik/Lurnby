import unittest
from app import db, create_app
from app.models import Comms
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


class CommsTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_repr(self):
        user_id = 123
        comms = Comms(user_id=user_id)
        db.session.add(comms)
        db.session.commit()

        expected = (
            f"<User {user_id}>\n"
            "informational: True, educational: True, "
            "promotional: True, highlights: True, "
            "reminders: True"
        )
        self.assertEqual(repr(comms), expected)

    def test_to_dict(self):
        user_id = 456
        comms = Comms(
            user_id=user_id,
            informational=False,
            educational=False,
            promotional=False,
            highlights=False,
            reminders=False,
        )
        db.session.add(comms)
        db.session.commit()
        self.assertEqual(
            comms.to_dict(),
            {
                "id": comms.id,
                "user_id": user_id,
                "informational": False,
                "educational": False,
                "promotional": False,
                "highlights": False,
                "reminders": False,
            },
        )

    def test_defaults(self):
        comms = Comms(user_id=789)
        db.session.add(comms)
        db.session.commit()
        self.assertEqual(comms.informational, True)
        self.assertEqual(comms.educational, True)
        self.assertEqual(comms.promotional, True)
        self.assertEqual(comms.highlights, True)
        self.assertEqual(comms.reminders, True)


if __name__ == "__main__":
    unittest.main()
