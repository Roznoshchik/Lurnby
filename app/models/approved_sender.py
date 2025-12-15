from app.models.base import db


class Approved_Sender(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    email = db.Column(db.String(120))

    def __repr__(self):
        return self.email
