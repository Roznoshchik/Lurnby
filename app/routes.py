import json
import requests

from app import app, client, db
from flask import flash, redirect, url_for, render_template, request, jsonify
from app.forms import ContentForm, LoginForm, RegisterForm, AddTopicForm, ResetPasswordRequestForm, ResetPasswordForm, AddHighlightForm
from app.pulltext import pull_text
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Article, Topic, Highlight, highlights_topics, Tag
from werkzeug.urls import url_parse
from datetime import datetime
from app.email import send_password_reset_email
from wtforms import BooleanField


@app.route("/", methods=['GET','POST'])
@app.route("/index", methods=['GET','POST'])
@login_required
def index():
    form = ContentForm()


    if request.method =='POST':
        print("ARE WE HERE?")

        url = request.form['url']
        print(url)
        if url != "":
            urltext = pull_text(url)
            
            title = urltext["title"]
            content = urltext["content"]
            
            """
            if current_user.is_anonymous:
                return render_template('text.html', title =text["title"], author = text["byline"], content=text["content"])
            """

            new_article = Article(unread=True, title=title, source_url=url, content=content, user_id=current_user.id, archived=False, filetype="url" )
            db.session.add(new_article)
            db.session.commit()
            flash('Article added!', 'message')

        text = request.form['text']
        print(text)
        if text != "":
            title = request.form['title']    
            source = request.form['source']
            new_article = Article(unread=True, title=title, source=source, content=text, user_id=current_user.id, archived=False, filetype="manual" )
            db.session.add(new_article)
            db.session.commit()
            flash('Article added!', 'message')


            epub = form.epub.data



        #return render_template('text.html', title =text["title"], author = text["byline"], content=text["plain_content"])
        
        return redirect(url_for('index'))

    return render_template('index.html', title="Elegant Reader", form=form)
 

    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.lower()).first()
        if user is not None:
            if user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                if not next_page or url_parse(next_page).netloc != '':
                    next_page = url_for('index')
                return redirect(next_page)

            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

        else:
            user = User.query.filter_by(email=form.username.data.lower()).first()
            if user is None or not user.check_password(form.password.data):
                flash('Invalid username or password', 'error')
                return redirect(url_for('login'))

            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
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
    newuser = User(goog_id=unique_id, email=users_email, firstname=users_name)
    user = User.query.filter_by(email=users_email).first()    
    if user is None:
        db.session.add(newuser)
        db.session.commit()
        user = User.query.filter_by(goog_id=unique_id).first()
        login_user(user)
    
    if user is not None:
        if user.goog_id == None:   
            user.goog_id = unique_id
            user.firstname = users_name
            db.session.commit()
        
        login_user(user)
    return redirect(url_for("index"))



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user=User(username=form.username.data.lower(), firstname=form.firstname.data, email=form.email.data.lower())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'message')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/articles')
@login_required
def articles():
    unread_articles = Article.query.filter_by(unread=True, user_id=current_user.id).all()
    read_articles = Article.query.filter_by(unread=False, user_id=current_user.id).all()


    return render_template('articles.html', unread_articles=unread_articles, read_articles=read_articles)

@app.route('/article/<id>', methods =['POST', 'GET'])
@login_required
def article(id):
    article = Article.query.filter_by(id=id).first()
    article.unread = False
    article.last_reviewed = datetime.utcnow()
    db.session.commit()

    topics = Topic.query.filter_by(user_id=current_user.id, archived=False)
    content = article.content
    title = article.title

    addtopicform = AddTopicForm()
    
    

    form = AddHighlightForm()
    
    if form.validate_on_submit():
        topics = Topic.query.filter_by(user_id=current_user.id, archived=False)

        newHighlight = Highlight(user_id = current_user.id, article_id = form.article_id.data, text = form.text.data, note = form.note.data, archived=False)
        db.session.add(newHighlight)
        for t in topics:
            if request.form.get(t.title):
                newHighlight.AddToTopic(t)
        
        db.session.commit()
     

    return render_template('text.html', title =title, article_id = id, content=content, form=form, addtopicform=addtopicform, topics=topics)


@app.route('/article/<id>/highlight-storage', methods =['POST', 'GET'])
@login_required
def storeHighlights(id):
    article = Article.query.filter_by(id=id).first()

    if request.method == "GET":
        serialized = article.highlightedText
        if serialized is not None:
            return jsonify({
                'SerializedHighlights': article.highlightedText
            })
        else: 
            return json.dumps({'success':False}), 403, {'ContentType':'application/json'}  

    if request.method == "POST":
        article.highlightedText = request.form['SerializedHighlights']
        db.session.commit()
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}  



@app.route('/article/addhighlight', methods =['POST'])
@login_required
def addhighlight():
    
    topics = Topic.query.filter_by(user_id=current_user.id, archived=False)

    newHighlight = Highlight(user_id = current_user.id, article_id = request.form.get('article_id'), text = request.form.get('text'), note = request.form.get('note'), archived=False)
    db.session.add(newHighlight)
    
    list = request.form.getlist('topics')
    
    for t in list:
        print(t)
        topic = Topic.query.filter_by(title=t).first()
        print (topic, topic.title)
        newHighlight.AddToTopic(topic) 
    
    db.session.commit() 
    
    return jsonify({
        'highlight_id': newHighlight.id
    })

   
@app.route('/view_highlight/<id>', methods=['GET', 'POST'])
@login_required
def view_highlight(id):
    highlight = Highlight.query.filter_by(id = id).first_or_404()
    article = Article.query.filter_by(id = highlight.article_id).first()
    
    addtopicform = AddTopicForm()
    form = AddHighlightForm()
    
    member = highlight.in_topics().all()
    nonmember = highlight.not_in_topics()
    
    source = article.source
    source_url = article.source_url
    
    inappurl = url_for('article', id = article.id)
    
    article_title = article.title



    if request.method == 'GET':
        form.text.data = highlight.text
        form.note.data = highlight.note

        return render_template('highlight.html', highlight = highlight,addtopicform=addtopicform, form = form, member = member, nonmember = nonmember, article_title=article_title, source = source, source_url=source_url, inappurl=inappurl)


    if request.method == 'POST':
        highlight.text = request.form['text']
        highlight.note = request.form['note']

        members = request.form.getlist('members')
        print(members)
        for member in members:
            topic = Topic.query.filter_by(title=member).first()
            highlight.AddToTopic(topic)
        

        nonmembers = request.form.getlist('nonmembers')
        for nonmember in nonmembers:
            topic = Topic.query.filter_by(title=nonmember).first()
            highlight.RemoveFromTopic(topic)


        db.session.commit()
        return redirect(url_for('topics'))


@app.route('/archivehighlight/<id>')
@login_required
def archivehighlight(id):
    
    highlight = Highlight.query.filter_by(id=id).first()
    if current_user.id != highlight.user_id:
        return render_template('404.html'), 404

    highlight.archived = True
    db.session.commit()
    
    flash('Highlight has been deleted. <a href="'+ url_for('unarchivehighlight', id = id) + '"  class="alert-link">UNDO</a>', 'error')
    return redirect(url_for('topics'))

@app.route('/unarchivehighlight/<id>')
@login_required
def unarchivehighlight(id):
    
    highlight = Highlight.query.filter_by(id=id).first()
    if current_user.id != highlight.user_id:
        return render_template('404.html'), 404

    highlight.archived = False
    db.session.commit()
        
    return redirect(url_for('topics'))


@app.route('/topics', methods=['GET', 'POST'])
@login_required
def topics():
    topics = Topic.query.filter_by(archived=False, user_id=current_user.id).all()
    highlights = Highlight.query.filter_by(user_id=current_user.id, archived=False).all()

    
    notopics = []
    
    for highlight in highlights:
        if highlight.not_added():
            notopics.append(highlight)
   






    form2=AddHighlightForm()
    
    form = AddTopicForm()
    
    if form.validate_on_submit():

        newtopic=Topic(title=form.title.data, user_id=current_user.id, archived=False)
        db.session.add(newtopic)

        db.session.commit()
        #return render_template('topics.html', form=form, topics=topics)
        return redirect(url_for('topics'))

    return render_template('topics.html', form=form,form2=form2, highlights = highlights, notopics=notopics, topics=topics)


@app.route('/topics/add', methods=['POST'])
@login_required
def add_new_topic():

    newtopic = Topic.query.filter_by(title=request.form['title'].lower()).first()
    if newtopic is not None:
        return  render_template('404.html'), 404
    
    newtopic = Topic(title=request.form['title'].lower(), user_id=current_user.id, archived=False)
    db.session.add(newtopic)
    db.session.commit()

    return jsonify({
        'title': newtopic.title,
        'id': newtopic.id
    })
   


@app.route('/archivetopic/<topic_id>')
@login_required

def archivetopic(topic_id):
    
    topic = Topic.query.filter_by(id=topic_id).first()
    if current_user.id != topic.user_id:
        return render_template('404.html'), 404

    if topic is not None:
        topic.archived = True
        topic.title = topic.title + "-id:" + str(topic.id)
        db.session.commit()
    else:
        flash('Something went wrong! Please try again.', 'error')

    return redirect(url_for('topics'))





@app.route('/reset_password_request', methods=['GET', 'POST'])
@login_required

def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password', 'message')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods = ['GET','POST'])
@login_required

def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('login'))
    form=ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.', 'message')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)