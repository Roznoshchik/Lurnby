from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FormField, FieldList
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired, URL, ValidationError, Email, EqualTo, Length
from app.models import User, Topic

class ContentForm(FlaskForm):
    url = URLField('URL', validators=[URL()])
    epub = FileField('Choose an epub file', validators=[
        FileRequired(),
        FileAllowed(['epub'], 'Epub only.')
    ])

    title = StringField('Title')
    source = StringField('Source')
    text = TextAreaField('Copy and paste text')
    submit = SubmitField('Get Content')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    firstname = StringField('First name')
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    repeat_password = PasswordField('Repeat Password', validators=[EqualTo('password')])
    submit = SubmitField('Sign In')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data.lower()).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user is not None:
            raise ValidationError('Please use a different email')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    repeat_password = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Your Password')


class AddTopicForm(FlaskForm):
    title = StringField('Topic title ...', validators=[DataRequired()])
    
    def validate_title(self, title):
        title = Topic.query.filter_by(title=title.data.lower()).first()
        if title is not None:
            raise ValidationError('Topic with this name already exists.')

class AddHighlightForm(FlaskForm):
    text = TextAreaField('Highlight')
    note = TextAreaField('Add a note or description')





