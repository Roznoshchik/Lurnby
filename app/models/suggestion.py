from sqlalchemy import func

from app.models.base import db


class Suggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String)
    title = db.Column(db.String)
    summary = db.Column(db.String)
    users = db.relationship("User", backref="suggestion", lazy="dynamic")

    def __repr__(self):
        return f"<{self.title}: Users: {self.users.count()}>"

    @classmethod
    def get_random(cls):
        return Suggestion.query.order_by(func.random()).first()
