from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    firstname = StringField('First name')
    email = StringField('Email')
    submit = SubmitField('Sign In')

    def validate_username(self, username):
        print(username)
        user = User.query.filter_by(username=username.data.lower()).first()
        
        if user and user.username != username.data.lower():
            raise ValidationError(message='Username not available. Please use a different username.')



class UpdateEmailForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Email()])

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user is not None:
            raise ValidationError('This email is already being used.')





class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    firstname = StringField('First name')
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    repeat_password = PasswordField('Repeat Password',
                                    validators=[EqualTo('password')])
    submit = SubmitField('Sign In')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data.lower()).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user is not None:
            raise ValidationError('This email is already being used.')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class UpdatePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password', validators=[DataRequired()])
    repeat_password = PasswordField('Repeat New Password',
                                    validators=[DataRequired(),
                                                EqualTo('new_password', message="Passwords don't match")])
    submit = SubmitField('Update Your Password')



class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    repeat_password = PasswordField('Repeat Password',
                                    validators=[DataRequired(),
                                                EqualTo('password')])
    submit = SubmitField('Reset Your Password')
