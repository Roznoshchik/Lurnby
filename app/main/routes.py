import json
import requests
import tempfile
import os

from app import db
from app.main.forms import ContentForm, AddTopicForm, AddHighlightForm
from app.main.pulltext import pull_text
from app.main.ebooks import epub2text, epubTitle
from app.models import User, Article, Topic, Highlight, highlights_topics, Tag


from flask import flash, redirect, url_for, render_template, request, jsonify
from flask_login import current_user, login_required

from datetime import datetime

# from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
# from wtforms import BooleanField

from app.main import bp

@bp.route("/", methods=['GET','POST'])
@bp.route("/index", methods=['GET','POST'])
@login_required
def index():
    form = ContentForm()

    if request.method =='POST' and form.validate():
        url = request.form['url']
        if url:
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
        if text:
            text = "<pre>" + text + "</pre>"
            title = request.form['title']    
            source = request.form['source']
            new_article = Article(unread=True, title=title, source=source, content=text, user_id=current_user.id, archived=False, filetype="manual" )
            db.session.add(new_article)
            db.session.commit()
            flash('Article added!', 'message')


        f = form.epub.data
        if f:
            basedir = os.path.abspath(os.path.dirname(__file__))
            filename = secure_filename(f.filename)
            
            path = os.path.join(
                basedir, 'temp'
            )
            if not os.path.isdir(path): 
                os.mkdir(path)
            
            path = os.path.join(
                basedir, 'temp', filename
            )


            f.save(path)
            
            content = epub2text(path)
            title = epubTitle(path)
            
            title = title[0][0]
            epubtext = ""
            for item in content:
                epubtext = epubtext + "<pre>" + item +"</pre>"

            new_article = Article(unread=True, title=title, content=epubtext, user_id=current_user.id, archived=False, filetype="epub" )
            db.session.add(new_article)
            db.session.commit()
            os.remove(path)
            flash('Article added!', 'message')
       
       
        #return render_template('text.html', title =text["title"], author = text["byline"], content=text["plain_content"])
        
        return redirect(url_for('main.index'))

    elif request.method =='POST' and not form.validate():
        url = request.form['url']
        if url:
            for error in form.url.errors:
                flash(error, 'error')
        
        for error in form.epub.errors:
            flash(error, 'error')

        flash(form.errors, 'error')
        return redirect(url_for('main.index'))

    return render_template('index.html', title="Elegant Reader", form=form)
 



@bp.route('/articles')
@login_required
def articles():
    unread_articles = Article.query.filter_by(unread=True, user_id=current_user.id).all()
    read_articles = Article.query.filter_by(unread=False, user_id=current_user.id).all()


    return render_template('articles.html', unread_articles=unread_articles, read_articles=read_articles)

@bp.route('/article/<id>', methods =['POST', 'GET'])
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


@bp.route('/article/<id>/highlight-storage', methods =['POST', 'GET'])
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



@bp.route('/article/addhighlight', methods =['POST'])
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

   
@bp.route('/view_highlight/<id>', methods=['GET', 'POST'])
@login_required
def view_highlight(id):
    highlight = Highlight.query.filter_by(id = id).first_or_404()
    article = Article.query.filter_by(id = highlight.article_id).first()
    
    addtopicform = AddTopicForm()
    form = AddHighlightForm()
    
    member = highlight.topics.filter_by(user_id=current_user.id).all()
    nonmember = highlight.not_in_topics(current_user)
    
    source = article.source
    source_url = article.source_url
    
    inappurl = url_for('main.article', id = article.id)
    
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
        return redirect(url_for('main.topics'))


@bp.route('/archivehighlight/<id>')
@login_required
def archivehighlight(id):
    
    highlight = Highlight.query.filter_by(id=id).first()
    if current_user.id != highlight.user_id:
        return render_template('errors/404.html'), 404

    highlight.archived = True
    db.session.commit()
    
    flash('Highlight has been deleted. <a href="'+ url_for('main.unarchivehighlight', id = id) + '"  class="alert-link">UNDO</a>', 'error')
    return redirect(url_for('main.topics'))

@bp.route('/unarchivehighlight/<id>')
@login_required
def unarchivehighlight(id):
    
    highlight = Highlight.query.filter_by(id=id).first()
    if current_user.id != highlight.user_id:
        return render_template('errors/404.html'), 404

    highlight.archived = False
    db.session.commit()
        
    return redirect(url_for('main.topics'))


@bp.route('/topics', methods=['GET', 'POST'])
@login_required
def topics():
    topics = Topic.query.filter_by(archived=False, user_id=current_user.id).all()
    highlights = Highlight.query.filter_by(user_id=current_user.id, archived=False).all()

    
    notopics = []
    
    for highlight in highlights:
        if highlight.not_added_topic():
            notopics.append(highlight)
   






    form2=AddHighlightForm()
    
    form = AddTopicForm()
    
    if form.validate_on_submit():

        newtopic=Topic(title=form.title.data, user_id=current_user.id, archived=False)
        db.session.add(newtopic)

        db.session.commit()
        #return render_template('topics.html', form=form, topics=topics)
        return redirect(url_for('main.topics'))

    return render_template('topics.html', form=form,form2=form2, highlights = highlights, notopics=notopics, topics=topics)


@bp.route('/topics/add', methods=['POST'])
@login_required
def add_new_topic():

    newtopic = Topic.query.filter_by(title=request.form['title'].lower()).first()
    if newtopic is not None:
        return  render_template('errors/404.html'), 404
    
    newtopic = Topic(title=request.form['title'].lower(), user_id=current_user.id, archived=False)
    db.session.add(newtopic)
    db.session.commit()

    return jsonify({
        'title': newtopic.title,
        'id': newtopic.id
    })
   


@bp.route('/archivetopic/<topic_id>')
@login_required

def archivetopic(topic_id):
    
    topic = Topic.query.filter_by(id=topic_id).first()
    if current_user.id != topic.user_id:
        return render_template('errors/404.html'), 404

    if topic is not None:
        topic.archived = True
        topic.title = topic.title + "-id:" + str(topic.id)
        db.session.commit()
    else:
        flash('Something went wrong! Please try again.', 'error')

    return redirect(url_for('main.topics'))



