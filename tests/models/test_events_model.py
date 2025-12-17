from datetime import datetime, timedelta
from app import db
from app.models import Event, User
from app.models.event import EventName
from tests.conftest import BaseTestCase


class EventTest(BaseTestCase):
    def test_add_event(self):
        # User is created (Comms and Event created automatically via after_insert hook)
        user = User(
            username="test_user",
            email="test@example.com",
            password_hash="password",
        )
        db.session.add(user)
        db.session.commit()

        # Test adding a regular event
        event = Event.add(EventName.CREATED_ACCOUNT, user=user)
        db.session.add(event)
        db.session.commit()
        self.assertIsInstance(event, Event)
        self.assertEqual(event.user_id, user.id)
        self.assertEqual(event.name, EventName.CREATED_ACCOUNT.value)

        # Test adding daily event
        daily_event = Event.add(EventName.REVIEWED_HIGHLIGHTS, daily=True, user=user)
        db.session.add(daily_event)
        db.session.commit()

        self.assertIsInstance(daily_event, Event)
        self.assertEqual(daily_event.user_id, user.id)
        self.assertEqual(daily_event.name, EventName.REVIEWED_HIGHLIGHTS.value)

        today_start = datetime(
            datetime.utcnow().year, datetime.utcnow().month, datetime.utcnow().day, 0, 0
        )
        today_end = today_start + timedelta(days=1)

        existing_event = Event.query.filter(
            Event.name == EventName.REVIEWED_HIGHLIGHTS.value,
            Event.date >= today_start,
            Event.date < today_end,
            Event.user_id == user.id,
        ).first()

        self.assertIsInstance(existing_event, Event)
        self.assertEqual(existing_event, daily_event)
        # Daily events return False if already added today
        self.assertFalse(Event.add(EventName.REVIEWED_HIGHLIGHTS, daily=True, user=user))

        # Test __repr__
        self.assertEqual(
            str(event),
            f'<User {user.id} {EventName.CREATED_ACCOUNT.value} on {event.date.strftime("%b %d %Y %H:%M:%S")}>',
        )
