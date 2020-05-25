from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired, URL, ValidationError, Email, EqualTo, Length

class URLForm(FlaskForm):
    url = URLField('URL', validators=[DataRequired(), URL()])
    submit = SubmitField('Get Content')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    repeat_password = PasswordField('Repeat Password', validators=[EqualTo('password')])
    submit = SubmitField('Sign In')

class AddTopicForm(FlaskForm):
    title = StringField('Topic title ...', validators=[DataRequired()])