from datetime import datetime, timedelta
from flask_login import current_user

from app.models.base import db


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
    def add(kind, daily=False, user=current_user):
        from app.models.user import User
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
                Event.name == kind,
                Event.date >= today_start,
                Event.date < today_end,
                Event.user_id == user.id,
            ).first()
            if not ev:
                ev = Event(user_id=user.id, name=kind, date=datetime.utcnow())
                update_user_last_action(kind, user=user)
                return ev
            else:
                return False
        else:
            ev = Event(user_id=user.id, name=kind, date=datetime.utcnow())
            update_user_last_action(kind, user=user)
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
