from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, DecimalField, BooleanField
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired, URL, ValidationError, Email, Optional
from app.models import Topic


class ContentForm(FlaskForm):
    url = URLField('URL', validators=[
        URL(),
        Optional()
    ])
    epub = FileField('Choose an epub file', validators=[
        FileAllowed(['epub'], 'Epub only.')
    ])

    title = StringField('Title')
    source = StringField('Source')
    text = TextAreaField('Copy and paste text')
    submit = SubmitField('Get Content')


class SuggestionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    url = URLField('URL', validators=[
        URL()
    ])   
    summary = TextAreaField('Summary')
    submit = SubmitField('Add')


class AddTopicForm(FlaskForm):
    title = StringField('Topic title ...', validators=[DataRequired()])

    def validate_title(self, title):
        title = Topic.query.filter_by(title=title.data.lower()).first()
        if title is not None:
            raise ValidationError('Topic with this name already exists.')


class AddHighlightForm(FlaskForm):
    text = TextAreaField('Highlight')
    note = TextAreaField('Add a note or description')
    position = DecimalField(places=3, rounding=None, use_locale=False)
    do_not_review = BooleanField()

class AddApprovedSenderForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Approve email')
