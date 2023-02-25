from datetime import datetime, timedelta
import unittest
from app import db, create_app
from app.models import Event, User
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


class EventTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_event(self):
        user = User(
            username="test_user",
            email="test@example.com",
            password_hash="password",
        )
        db.session.add(user)
        db.session.commit()

        event = Event.add("created account", user=user)
        db.session.add(event)
        db.session.commit()
        self.assertIsInstance(event, Event)
        self.assertEqual(event.user_id, user.id)
        self.assertEqual(event.name, "created account")

        # Test adding daily event
        daily_event = Event.add("reviewed highlights", daily=True, user=user)
        db.session.add(daily_event)
        db.session.commit()

        self.assertIsInstance(daily_event, Event)
        self.assertEqual(daily_event.user_id, user.id)
        self.assertEqual(daily_event.name, "reviewed highlights")

        today_start = datetime(
            datetime.utcnow().year, datetime.utcnow().month, datetime.utcnow().day, 0, 0
        )
        today_end = today_start + timedelta(days=1)

        existing_event = Event.query.filter(
            Event.name == "reviewed highlights",
            Event.date >= today_start,
            Event.date < today_end,
            Event.user_id == user.id,
        ).first()

        self.assertIsInstance(existing_event, Event)
        self.assertEqual(existing_event, daily_event)
        self.assertFalse(Event.add("reviewed highlights", daily=True, user=user))

        # Test __repr__
        self.assertEqual(
            str(event),
            f'<User {user.id} created account on {event.date.strftime("%b %d %Y %H:%M:%S")}>',
        )
