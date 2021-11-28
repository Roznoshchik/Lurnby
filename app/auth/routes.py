import json
import requests

from flask import (flash, redirect, url_for, render_template, request,
                   current_app, session)
from flask_login import current_user, login_user, logout_user, login_required

from app import db
from app.auth import bp
from app.auth.forms import (LoginForm, RegisterForm, ResetPasswordRequestForm,
                            ResetPasswordForm)
from app.auth.email import send_password_reset_email
from app.models import User, Comms, Event

from werkzeug.urls import url_parse
from oauthlib.oauth2 import WebApplicationClient


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.articles'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query \
               .filter_by(username=form.username.data.lower()).first()
        if user is not None:
            if user.check_password(form.password.data):
                login_user(user, remember=True)
                next_page = request.args.get('next')
                if not next_page or url_parse(next_page).netloc != '':
                    next_page = url_for('main.articles')
                return redirect(next_page)

            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))

        else:
            user = User.query \
                   .filter_by(email=form.username.data.lower()).first()
            if user is None or not user.check_password(form.password.data):
                flash('Invalid username or password', 'error')
                return redirect(url_for('auth.login'))

            login_user(user, remember=True)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('main.articles')
            return redirect(next_page)

    return render_template('auth/login.html', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


def get_google_provider_cfg():
    return requests.get(current_app.config['GOOGLE_DISCOVERY_URL']).json()


@bp.route('/google_login')
def google_login():

    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    client = WebApplicationClient(current_app.config['GOOGLE_CLIENT_ID'])

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
        prompt="select_account"
    )
    return redirect(request_uri)


@bp.route('/google_login/callback')
def callback():
    code = request.args.get("code")
    # print(f'from google callback page \n\n{session["ref"]}\n\n')

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    client = WebApplicationClient(current_app.config['GOOGLE_CLIENT_ID'])

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(current_app.config['GOOGLE_CLIENT_ID'],
              current_app.config['GOOGLE_CLIENT_SECRET'],)
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in your db with the information provided
    # by Google
    newuser = User(goog_id=unique_id, email=users_email, firstname=users_name)
    user = User.query.filter_by(email=users_email).first()
    if user is None:
        db.session.add(newuser)
        db.session.commit()
        comms = Comms(user_id=newuser.id)
        db.session.add(comms)
        db.session.commit()
        print(comms)
        user = User.query.filter_by(goog_id=unique_id).first()
        # login_user(user, remember=True)
        return redirect(url_for('auth.tos_accept', id=user.id))


    if user is not None:
        if user.goog_id is None:
            user.goog_id = unique_id
            user.firstname = users_name
            db.session.commit()

        login_user(user, remember=True)
    return redirect(url_for("main.articles"))



@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.articles'))
    form = RegisterForm()
    
    # session['ref'] = request.args.get('ref')

    if form.validate_on_submit():
        # print(f'from register page \n\n{session["ref"]}\n\n')
        user = User(username=form.username.data.lower(),
                    firstname=form.firstname.data,
                    email=form.email.data.lower())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        comms = Comms(user_id=user.id)
        db.session.add(comms)
        print(comms)
        db.session.commit()
        # flash('Congratulations, you are now a registered user!', 'message')
        return redirect(url_for('auth.tos_accept', id=user.id))
    return render_template('auth/register.html', title='Register', form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.articles'))
    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password',
              'message')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title='Reset Password', form=form)



@bp.route('/reset_password_request2', methods=['GET', 'POST'])
def reset_password_request2():
    
    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password',
              'message')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title='Reset Password', form=form)





@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.articles'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('auth.login'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        ev = Event.add('reset password')
        if ev:
            db.session.add(ev)
        db.session.commit()
        flash('Your password has been reset.', 'message')
        
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@bp.route('/tos_accept/<id>', methods=['GET', 'POST'])
def tos_accept(id):
    u = User.query.get(id)
    reply = request.args.get('tos')
    if reply == 'accept':
        u.tos = True
        db.session.commit()
        login_user(u)
        ev = Event.add('user registered')
        if ev:
            db.session.add(ev)
        ev = Event.add('tos accepted')
        if ev:
            db.session.add(ev)
        db.session.commit()
        print('redirecting user who accepted')
        return redirect(url_for('main.articles'))
    
    elif reply == 'decline':
        db.session.delete(u)
        db.session.commit()
        print('deleting user who declined')
        return redirect(url_for('auth.register'))

    return render_template('legal/auth_tos_accept.html', u=u)
