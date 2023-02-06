from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    BooleanField,
    SelectField,
)
from wtforms.validators import DataRequired, Email


class AddApprovedSenderForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Approve email")


class DeleteAccountForm(FlaskForm):
    export = SelectField(
        "Export Type",
        choices=[
            ("none", "Don't Export"),
            ("txt", "Export as TXT"),
            ("json", "Export as JSON"),
        ],
    )
    submit = SubmitField("Delete my account")


class CommunicationForm(FlaskForm):
    educational = BooleanField("Educational")
    informational = BooleanField("Informational")
    promotions = BooleanField("Promotions")
    highlights = BooleanField("Highlights")
    reminders = BooleanField("Review")
    submit = SubmitField("Update my preferences")
