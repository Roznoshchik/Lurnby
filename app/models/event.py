from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional
from flask_login import current_user
import sqlalchemy as sa
import sqlalchemy.orm as so

from app.models.base import db


class EventName(Enum):
    """Event name constants for tracking user actions"""
    ADDED_APPROVED_SENDER = "added approved sender"
    ADDED_ARTICLE = "added article"
    ADDED_HIGHLIGHT = "added highlight"
    ADDED_SUGGESTED_ARTICLE = "added suggested article"
    ADDED_TAG = "added tag"
    ADDED_TOPIC = "added topic"
    CREATED_ACCOUNT = "created account"
    DELETED_ACCOUNT = "deleted account"
    DELETED_ARTICLE = "deleted article"
    DELETED_HIGHLIGHT = "deleted highlight"
    DELETED_TAG = "deleted tag"
    ENABLED_ADD_BY_EMAIL = "enabled add by email"
    EXPORTED_ALL_DATA = "exported all data"
    EXPORTED_ARTICLE = "exported article"
    EXPORTED_HIGHLIGHTS = "exported highlights"
    OPENED_ARTICLE = "opened article"
    RESET_PASSWORD = "reset password"
    REVIEWED_HIGHLIGHTS = "reviewed highlights"
    REVIEWED_A_HIGHLIGHT = "reviewed a highlight"
    SUBMITTED_FEEDBACK = "submitted feedback"
    TOS_ACCEPTED = "tos accepted"
    UPDATED_ACCOUNT_EMAIL = "updated account email"
    UPDATED_ARTICLE = "updated article"
    UPDATED_ARTICLE_TAGS = "updated article tags"
    UPDATED_COMMS = "updated comms"
    UPDATED_HIGHLIGHT = "updated highlight"
    UPDATED_HIGHLIGHT_TOPICS = "updated highlight topics"
    UPDATED_PASSWORD = "updated password"
    UPDATED_TAG = "updated tag"
    UPDATED_USER_CREDENTIALS = "updated user credentials"
    UPDATED_USER_INFO = "updated user info"
    USER_REGISTERED = "user registered"
    VISITED_PLATFORM = "visited platform"


class Event(db.Model):
    __tablename__ = 'event'
    __table_args__ = (
        sa.Index('ix_event_user_name_date', 'user_id', 'name', 'date'),
    )

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"))
    name: so.Mapped[str] = so.mapped_column(sa.String())
    date: so.Mapped[datetime] = so.mapped_column(sa.DateTime())

    @staticmethod
    def add(kind: EventName | str, daily=False, user=current_user):
        """Add an event with the given EventName enum or string

        Args:
            kind: EventName enum or string that matches an EventName value
            daily: If True, only creates one event per day for this type
            user: User object (defaults to current_user)

        Returns:
            Event object if created, False if daily event already exists

        Raises:
            ValueError: If kind is a string that doesn't match any EventName value
        """
        from app.models.user import User

        # Convert to EventName enum (raises ValueError if invalid)
        event_enum = EventName(kind)
        event_name = event_enum.value

        if daily:
            today_start = datetime(
                datetime.utcnow().year,
                datetime.utcnow().month,
                datetime.utcnow().day,
                0,
                0,
            )
            today_end = today_start + timedelta(days=1)
            stmt = sa.select(Event).where(
                Event.name == event_name,
                Event.date >= today_start,
                Event.date < today_end,
                Event.user_id == user.id,
            )
            ev = db.session.scalar(stmt)
            if not ev:
                ev = Event(user_id=user.id, name=event_name, date=datetime.utcnow())
                update_user_last_action(event_name, user=user)
                return ev
            else:
                return False
        else:
            ev = Event(user_id=user.id, name=event_name, date=datetime.utcnow())
            update_user_last_action(event_name, user=user)
            return ev

    @staticmethod
    def count_events(
        user_id: int,
        event_names: list[EventName],
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Count events by type, user, and date range

        Args:
            user_id: User ID to filter by
            event_names: List of EventName enums to count
            start_date: Start of date range (inclusive)
            end_date: End of date range (exclusive)

        Returns:
            Count of matching events
        """
        # Convert EventName enums to their string values
        name_values = [event.value for event in event_names]

        stmt = sa.select(sa.func.count()).select_from(Event).where(
            Event.user_id == user_id,
            Event.name.in_(name_values),
            Event.date >= start_date,
            Event.date < end_date
        )
        count = db.session.scalar(stmt)

        return count

    @staticmethod
    def count_reviews_this_month(user_id: int) -> int:
        """Count review events for this month"""
        now = datetime.now(timezone.utc)
        month_start = datetime(now.year, now.month, 1, 0, 0)
        next_month = month_start.replace(month=now.month + 1) if now.month < 12 else datetime(now.year + 1, 1, 1)

        return Event.count_events(
            user_id,
            [EventName.REVIEWED_A_HIGHLIGHT],
            month_start,
            next_month
        )

    @staticmethod
    def count_articles_opened_this_month(user_id: int) -> int:
        """Count articles opened this month"""
        now = datetime.now(timezone.utc)
        month_start = datetime(now.year, now.month, 1, 0, 0)
        next_month = month_start.replace(month=now.month + 1) if now.month < 12 else datetime(now.year + 1, 1, 1)

        return Event.count_events(
            user_id,
            [EventName.OPENED_ARTICLE],
            month_start,
            next_month
        )

    @staticmethod
    def count_highlights_added_this_month(user_id: int) -> int:
        """Count highlights added this month"""
        now = datetime.now(timezone.utc)
        month_start = datetime(now.year, now.month, 1, 0, 0)
        next_month = month_start.replace(month=now.month + 1) if now.month < 12 else datetime(now.year + 1, 1, 1)

        return Event.count_events(
            user_id,
            [EventName.ADDED_HIGHLIGHT],
            month_start,
            next_month
        )

    def __repr__(self):
        return f'<User {self.user_id} {self.name} on {self.date.strftime("%b %d %Y %H:%M:%S")}>'


def update_user_last_action(action, user=current_user):
    from app.models.user import User
    from app.models.base import CustomLogger

    logger = CustomLogger("MODELS")
    if current_user:
        logger.info(f"last action = {action}")
        db.session.execute(
            User.__table__.update().values(last_action=action).where(User.id == user.id)
        )
