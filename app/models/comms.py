from app.models.base import db


class Comms(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)
    informational = db.Column(db.Boolean, default=True)
    educational = db.Column(db.Boolean, default=True)
    promotional = db.Column(db.Boolean, default=True)
    highlights = db.Column(db.Boolean, default=True)
    reminders = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return (
            f"<User {self.user_id}>\n"
            f"informational: {self.informational}, educational: {self.educational}, "
            f"promotional: {self.promotional}, highlights: {self.highlights}, "
            f"reminders: {self.reminders}"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "informational": self.informational,
            "educational": self.educational,
            "promotional": self.promotional,
            "highlights": self.highlights,
            "reminders": self.reminders,
        }
