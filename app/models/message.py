from datetime import datetime

from app.models.base import db


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.String())
    date = db.Column(db.Date())

    @staticmethod
    def add(name, user):
        msg = Message(user_id=user.id, name=name, date=datetime.utcnow())
        return msg

    def __repr__(self):
        return f'<User {self.user_id} {self.name} on {self.date.strftime("%b %d %Y %H:%M:%S")}>'
