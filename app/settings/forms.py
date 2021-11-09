from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, DecimalField, BooleanField
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired, URL, ValidationError, Email, Optional
from app.models import Topic


class AddApprovedSenderForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Approve email')
