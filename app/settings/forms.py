from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, DecimalField, BooleanField, SelectField
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired, URL, ValidationError, Email, Optional
from app.models import Topic


class AddApprovedSenderForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Approve email')

class DeleteAccountForm(FlaskForm):
    export = SelectField(u'Export Type', choices=[('none', "Don't Export"),('txt', 'Export as TXT'), ('json', 'Export as JSON')])
    submit = SubmitField('Delete my account')

class CommunicationForm(FlaskForm):
    educational = BooleanField('Educational')
    informational = BooleanField('Informational')
    promotions = BooleanField('Promotions')
    highlights = BooleanField('Highlights')
    reminders = BooleanField('Review')
    submit = SubmitField('Update my preferences')

