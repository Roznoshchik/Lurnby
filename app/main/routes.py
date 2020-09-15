import json
import requests
import tempfile
import os
import validators

from app import db
from app.main.forms import ContentForm, AddTopicForm, AddHighlightForm
from app.main.pulltext import pull_text
from app.main.ebooks import epub2text, epubTitle
from app.models import User, Article, Topic, Highlight, highlights_topics, Tag, tags_articles, tags_highlights


from flask import flash, redirect, url_for, render_template, request, jsonify
from flask_login import current_user, login_required
from flask_wtf.csrf import CSRFError

from datetime import datetime, date

# from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
# from wtforms import BooleanField

from app.main import bp

"""
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
         

            new_article = Article(unread=True, title=title, source_url=url, content=content, user_id=current_user.id, archived=False, filetype="url" )
            db.session.add(new_article)
            db.session.commit()
            flash('Article added!', 'message')

        text = request.form['text']
        if text:
            text = "<pre>" + text + "</pre>"
            title = request.form['title']    
            source = request.form['source']
            if source == '':
                today = date.today()
                today = today.strftime("%B %d, %Y")
                source = 'manually added ' + today
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
        
        return redirect(url_for('main.articles'))

    elif request.method =='POST' and not form.validate():
        url = request.form['url']
        if url:
            for error in form.url.errors:
                flash(error, 'error')
        
        for error in form.epub.errors:
            flash(error, 'error')

        flash(form.errors, 'error')
        return redirect(url_for('main.articles'))

    return render_template('index.html', title="Elegant Reader", form=form)
    """




@bp.route("/", methods=['GET','POST'])
@bp.route("/index", methods=['GET','POST'])
@bp.route('/articles', methods=['GET'])
@login_required
def articles():
    form = ContentForm()
    

    articles =  Article.query.filter_by(user_id=current_user.id, archived=False).all()
    tags = Tag.query.all()

    if (request.method == 'GET'):
        if(request.json):

            tag_ids = request.json

            articles = Article.query.join(tags_articles, (tags_articles.c.article_id == Article.id))
            articles = articles.filter(tags_articles.c.tag_id.in_(tag_ids)).all()
        
            return render_template('articles.html', articles)


    done_articles = Article.query.filter_by(archived=False, done = True, user_id=current_user.id).all()
    unread_articles = Article.query.filter_by(unread=True,done = False, archived=False, user_id=current_user.id).all()
    read_articles = Article.query.filter_by(unread=False, done=False,archived=False, user_id=current_user.id).all()


    return render_template('articles.html', form = form, done_articles = done_articles, unread_articles=unread_articles,user=current_user, read_articles=read_articles)

@bp.route('/articles/new', methods = ['GET', 'POST'])
@login_required
@bp.errorhandler(CSRFError)
def add_article():

    form = ContentForm()

    if request.method=='POST':
        
        notes = request.form['notes']
        tags = json.loads(request.form['tags'])
        epub = request.form['epub']
        title = request.form['title']
        source = request.form['source']
        content = request.form['content']
        url = request.form['url']

        for i in request.form:
            print (i + ': '+ request.form[i])


        if (title == 'none' and url == 'none' and epub == 'none'):
            return json.dumps({'no_article':True}), 400, {'ContentType':'application/json'}



        if (title != 'none'):

            if content == '':
                return json.dumps({'manual_fail':True}), 400, {'ContentType':'application/json'}


            content = "<pre>" + content + "</pre>"
            if source == '':
                today = date.today()
                today = today.strftime("%B %d, %Y")
                source = 'manually added ' + today
           
            new_article = Article(unread=True, notes = notes, progress=0.0, title=title, source=source, content=content, user_id=current_user.id, archived=False, filetype="manual" )
            db.session.add(new_article)
            for tag in tags:
                t = Tag.query.filter_by(name=tag).first()
                
                if not t:
                    t = Tag(name=tag, user_id=current_user.id)
                    db.session.add(t)
                    new_article.AddToTag(t)
                else:
                    new_article.AddToTag(t)        
            
           
            db.session.commit()
        
        if (url != 'none'):
            
            if not validators.url(url):
                return json.dumps({'bad_url':True}), 400, {'ContentType':'application/json'}


            urltext = pull_text(url)
            
            title = urltext["title"]
            content = urltext["content"]

            if not title or not content:
                return json.dumps({'bad_url':True}), 400, {'ContentType':'application/json'}

            

            new_article = Article(unread=True, notes = notes, progress=0.0, title=title, source_url=url, content=content, user_id=current_user.id, archived=False, filetype="url" )
            db.session.add(new_article)

            for tag in tags:
                t = Tag.query.filter_by(name=tag).first()
                
                if not t:
                    t = Tag(name=tag, user_id=current_user.id)
                    db.session.add(t)
                    new_article.AddToTag(t)
                else:
                    new_article.AddToTag(t)        
            
            db.session.commit()
        
        if epub == "true":
            f = request.files['epub_file']

            filename = f.filename
            if filename != '':
                file_ext = os.path.splitext(filename)[1]
                if file_ext != '.epub':
                    return json.dumps({'not_epub':True}), 400, {'ContentType':'application/json'}
           
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

        
            today = date.today()
            today = today.strftime("%B %d, %Y")
            source = 'Epub File: added ' + today


            new_article = Article(unread=True, title=title, content=epubtext, source=source, user_id=current_user.id, archived=False, progress = 0.0, filetype="epub" )
            db.session.add(new_article)

            for tag in tags:
                t = Tag.query.filter_by(name=tag).first()
                
                if not t:
                    t = Tag(name=tag, user_id=current_user.id)
                    db.session.add(t)
                    new_article.AddToTag(t)
                else:
                    new_article.AddToTag(t)        
            
            db.session.commit()
            os.remove(path)
             
        done_articles = Article.query.filter_by(archived=False, done = True, user_id=current_user.id).all()
        unread_articles = Article.query.filter_by(unread=True,done = False, archived=False, user_id=current_user.id).all()
        read_articles = Article.query.filter_by(unread=False, done=False,archived=False, user_id=current_user.id).all()
    
    return render_template('articles_all.html', form = form, done_articles = done_articles, unread_articles=unread_articles, read_articles=read_articles, user=current_user)

def handle_csrf_error(e):
    return json.dumps({'success':False}), 500, {'ContentType':'application/json'}

@bp.route('/articles/filter', methods=['GET', 'POST'])
@login_required
def filter_articles():

    form = ContentForm()
    data = json.loads(request.form['data'])
    tag_ids = data['tags']
    
    if tag_ids == []:
        done_articles = Article.query.filter_by(archived=False, done = True, user_id=current_user.id).all()
        unread_articles = Article.query.filter_by(unread=True,done = False, archived=False, user_id=current_user.id).all()
        read_articles = Article.query.filter_by(unread=False, done=False,archived=False, user_id=current_user.id).all()
        
        print('no tags passed')
        print('done articles')
        for a in done_articles:
            print(a.id, a.title, a.tags.all(),'\n\n')
        for a in unread_articles:
            print(a.id, a.title, a.tags.all(),'\n\n')
        for a in read_articles:
            print(a.id, a.title, a.tags.all(),'\n\n')

        return render_template('articles_all.html', form = form, done_articles = done_articles, unread_articles=unread_articles, read_articles=read_articles, user=current_user)


    active_tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()

    done_articles = Article.query.filter_by(archived=False, done = True, user_id=current_user.id).join(tags_articles, (tags_articles.c.article_id == Article.id))
    done_articles = done_articles.filter(tags_articles.c.tag_id.in_(tag_ids)).all()
    
    print('tags passed')
    print('done articles')
    for a in done_articles:
        print(a.id, a.title, a.tags.all(),'\n\n')

    unread_articles = Article.query.filter_by(unread=True,done = False, archived=False, user_id=current_user.id).join(tags_articles, (tags_articles.c.article_id == Article.id))
    unread_articles = unread_articles.filter(tags_articles.c.tag_id.in_(tag_ids)).all()
    print('unread articles')
    for a in unread_articles:
        print(a.id, a.title, a.tags.all(),'\n\n')


    read_articles = Article.query.filter_by(unread=False, done=False,archived=False, user_id=current_user.id).join(tags_articles, (tags_articles.c.article_id == Article.id))
    read_articles = read_articles.filter(tags_articles.c.tag_id.in_(tag_ids)).all()
    print('read articles')
    for a in read_articles:
        print(a.id, a.title, a.tags.all(),'\n\n')

    return render_template('articles_all.html', form = form, done_articles = done_articles, unread_articles=unread_articles, read_articles=read_articles, user=current_user, active_tags = active_tags)


    

@bp.route('/article/<id>', defaults={"highlight_id": "none" }, methods =['POST', 'GET'])
@bp.route('/article/<id>/<highlight_id>', methods =['POST', 'GET'])
@login_required
def article(id, highlight_id):
    article = Article.query.filter_by(id=id).first()
    article.unread = False
    article.last_reviewed = datetime.utcnow()
    db.session.commit()

    topics = Topic.query.filter_by(user_id=current_user.id, archived=False)
    content = article.content
    title = article.title

    addtopicform = AddTopicForm()
    
    if highlight_id != "none":
        highlight = Highlight.query.filter_by(id = highlight_id).first()
        article.progress = highlight.position
        db.session.commit()
    

    form = AddHighlightForm()
    
    if form.validate_on_submit():
        topics = Topic.query.filter_by(user_id=current_user.id, archived=False)

        newHighlight = Highlight(user_id = current_user.id, article_id = form.article_id.data, text = form.text.data, note = form.note.data, archived=False)
        db.session.add(newHighlight)
        for t in topics:
            if request.form.get(t.title):
                newHighlight.AddToTopic(t)
        
        db.session.commit()
     

    return render_template('text.html', title = title, article_id = id, content=content, form=form, addtopicform=addtopicform, topics=topics)


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


@bp.route('/article/<id>/progress', methods =['GET', 'POST'])
@login_required
def storeProgress(id):
    article = Article.query.filter_by(id=id).first()

    if request.method == "POST":
        article.progress = request.form['Progress']
        
        if (request.form['Progress'] == 100):
            article.done = True

        db.session.commit()
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}  
    
    if request.method == "GET":
        progress = article.progress
        if progress is None:
            progress = 0
        
        return jsonify({ 'Progress': article.progress })


@bp.route('/view_article/<id>', methods=['GET'])
@login_required
def view_article(id):
    article = Article.query.filter_by(id = id).first()
    
    return render_template('viewarticle.html', article = article)

@bp.route('/view_add_article/', methods=['GET'])
@login_required
def view_add_article():
    form=ContentForm()
    
    return render_template('add_article_modal.html', form=form, user=current_user)



@bp.route('/articles/<id>/update', methods =['POST'])
@login_required
def updateArticle(id):

    form = ContentForm()
    article = Article.query.filter_by(id=id).first()

    if request.method == "POST":

        data = json.loads(request.form['data'])
        
        if (data['read_status'] == 'read'):
            article.done = True
        if (data['read_status'] == 'unread'):
            article.done = False
            article.progress= 0.0
            article.unread = True
    
        article.title = data['title']
        article.notes = data['notes']
        article.content = data['content']
        
        
        for tag in data['tags']:
            t = Tag.query.filter_by(name=tag).first()
            if not t:
                t = Tag(user_id = current_user.id, name=tag)
                db.session.add(t)    
            
            article.AddToTag(t)
        
        for tag in data['remove_tags']:
            t = Tag.query.filter_by(name=tag).first()
            if not t:
                t = Tag(user_id = current_user.id, name=tag)
                db.session.add(t)    
            
            article.RemoveFromTag(t)

        db.session.commit()


        done_articles = Article.query.filter_by(archived=False, done = True, user_id=current_user.id).all()
        unread_articles = Article.query.filter_by(unread=True,done = False, archived=False, user_id=current_user.id).all()
        read_articles = Article.query.filter_by(unread=False, done=False,archived=False, user_id=current_user.id).all()


        return render_template('articles_all.html', form=form, done_articles = done_articles, unread_articles=unread_articles, read_articles=read_articles, user=current_user)


     
        #return json.dumps({'success':True}), 200, {'ContentType':'application/json'}  
        #return render_template('articles_all.html', article=article)
   
@bp.route('/articles/<id>/archive', methods =[ 'GET','POST'])
@login_required
def archiveArticle(id):
    article = Article.query.filter_by(id=id).first()
    article.archived=True
    db.session.commit()
    

    flash('Article has been archived. <a href="'+ url_for('main.unarchiveArticle', id = id) + '"  class="alert-link">UNDO</a>', 'error')
    return redirect(url_for('main.articles'))
    
@bp.route('/articles/<id>/unarchive', methods =[ 'GET','POST'])
@login_required
def unarchiveArticle(id):
    article = Article.query.filter_by(id=id).first()
    article.archived=False
    db.session.commit()
    

    return redirect(url_for('main.articles'))


@bp.route('/article/addhighlight', methods =['POST'])
@login_required
def addhighlight():
    
    topics = Topic.query.filter_by(user_id=current_user.id, archived=False)

    newHighlight = Highlight(user_id = current_user.id, article_id = request.form.get('article_id'), position = request.form.get('position'),  text = request.form.get('text'), note = request.form.get('note'), archived=False)
    db.session.add(newHighlight)
    
    list = request.form.getlist('topics')
    article = Article.query.filter_by(id = request.form.get('article_id')).first()

    for tag in articles.tags.all():
        newHighlight.AddToTag(tag)
    
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
    
    inappurl = url_for('main.article', id = article.id, highlight_id = highlight.id)


    
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

        tags = request.form.getlist('tag')
        for tag in tags:
            t = Tag.query.filter_by(name=tag).first()
            highlight.AddToTag(t)

        untags = request.form.getlist('untag')
        for tag in untags:
            t = Tag.query.filter_by(name=tag).first()
            highlight.RemoveFromTag(t)




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



