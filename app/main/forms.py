from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired, URL, ValidationError,  Optional
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



class AddTopicForm(FlaskForm):
    title = StringField('Topic title ...', validators=[DataRequired()])
    
    def validate_title(self, title):
        title = Topic.query.filter_by(title=title.data.lower()).first()
        if title is not None:
            raise ValidationError('Topic with this name already exists.')

class AddHighlightForm(FlaskForm):
    text = TextAreaField('Highlight')
    note = TextAreaField('Add a note or description')





