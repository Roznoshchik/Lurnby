from datetime import datetime, timedelta
from enum import Enum
from flask_login import current_user

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
    ENABLED_ADD_BY_EMAIL = "enabled add by email"
    EXPORTED_ALL_DATA = "exported all data"
    EXPORTED_HIGHLIGHTS = "exported highlights"
    OPENED_ARTICLE = "opened article"
    DELETED_ARTICLE = "deleted article"
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
    UPDATED_USER_CREDENTIALS = "updated user credentials"
    UPDATED_USER_INFO = "updated user info"
    USER_REGISTERED = "user registered"
    VISITED_PLATFORM = "visited platform"


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.String())
    date = db.Column(db.DateTime())

    """
    Tracked Events

    -> added approved sender     //    all
    -> added article             //    all
    -> added highlight           //    all
    -> added suggested article   //    all
    -> added tag                 //    all
    -> added topic               //    all
    -> created account           //    one time
    -> deleted account           //    one time
    -> enabled add by email      //    one time
    -> exported all data         //    all
    -> exported highlights       //    all
    -> opened article            //    all
    -> deleted article           //    all
    -> reset password            //    all
    -> reviewed highlights       //    daily
    -> reviewed a highlight      //    all
    -> submitted feedback        //    all
    -> tos accepted              //    one time
    -> updated account email     //    all
    -> updated article           //    all
    -> updated article tags      //    all
    -> updated comms             //    all
    -> updated highlight         //    all
    -> updated highlight topics  //    all
    -> updated password          //    all
    XX updated tag               //    all
    XX updated topic             //    all
    -> updated user credentials  //    all
    -> updated user info         //    all
    -> user registered           //    all
    -> visited platform          //    daily

    """

    @staticmethod
    def add(kind: EventName, daily=False, user=current_user):
        """Add an event with the given EventName enum"""
        from app.models.user import User

        event_name = kind.value

        if daily:
            today_start = datetime(
                datetime.utcnow().year,
                datetime.utcnow().month,
                datetime.utcnow().day,
                0,
                0,
            )
            today_end = today_start + timedelta(days=1)
            ev = Event.query.filter(
                Event.name == event_name,
                Event.date >= today_start,
                Event.date < today_end,
                Event.user_id == user.id,
            ).first()
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
