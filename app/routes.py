import json
import requests

from app import app, client, db
from flask import flash, redirect, url_for, render_template, request
from app.forms import URLForm, LoginForm, RegisterForm
from app.pulltext import pull_text
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from werkzeug.urls import url_parse

@app.route("/", methods=['GET','POST'])
@app.route("/index", methods=['GET','POST'])
def index():
    form = URLForm()
    if form.validate_on_submit():
        

        if request.method =='POST':
            url = request.form['url']
            text = pull_text(url)
            return render_template('text.html', title =text["title"], author = text["byline"], content=text["plain_content"])
            
        return redirect(url_for('index'))

    return render_template('index.html', title="Elegant Reader", form=form)
 

    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None:
            if user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                if not next_page or url_parse(next_page).netloc != '':
                    next_page = url_for('dashboard')
                return redirect(next_page)

            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

        else:
            user = User.query.filter_by(email=form.username.data).first()
            if user is None or not user.check_password(form.password.data):
                flash('Invalid username or password', 'error')
                return redirect(url_for('login'))

            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('dashboard')
            return redirect(next_page)
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

def get_google_provider_cfg():
    return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()

@app.route('/google_login')
def google_login():

    
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope = ["openid", "email", "profile"],
        prompt="select_account"
    )
    return redirect(request_uri)

@app.route('/google_login/callback')
def callback():
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
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
        auth=(app.config['GOOGLE_CLIENT_ID'], app.config['GOOGLE_CLIENT_SECRET'],)
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
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in your db with the information provided
    # by Google
    newuser = User(goog_id=unique_id, email=users_email, username=users_name)
    user = User.query.filter_by(goog_id=unique_id).first()    
    if user is None:
        db.session.add(newuser)
        db.session.commit()
        user = User.query.filter_by(goog_id=unique_id).first()
        login_user(user)
    
    if user is not None:
        login_user(user)
    return redirect(url_for("dashboard"))



@app.route('/register.html', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegisterForm()
    if form.validate_on_submit():
        user=User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'message')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

