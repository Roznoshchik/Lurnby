import json
import os
from threading import Thread
from uuid import UUID, uuid4

from sqlalchemy.sql.sqltypes import JSON
import validators

from app import csrf, db, s3, bucket
from app.email import send_email
from app.main.forms import (ContentForm, AddTopicForm,
                            AddHighlightForm,
                            SuggestionForm)
from app.main.pulltext import pull_text
from app.main.review import order_highlights
from app.main.ebooks import epubTitle, epubConverted
from app.main.pdf import importPDF
from app.models import (User, Approved_Sender, Article, Topic, Highlight, Tag,
                        tags_articles, tags_highlights, Notification, Suggestion,
                        Task, update_user_last_action, highlights_topics, Event)

import sys
sys.path.insert(1, './app/ReadabiliPy')
from readabilipy import simple_json_from_html_string

from data import data_dashboard

from bs4 import BeautifulSoup
from flask import flash, redirect, url_for, render_template, request, jsonify, current_app
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf.csrf import CSRFError

from datetime import datetime, date, timedelta
import time
from sqlalchemy import desc, or_, collate, func

from werkzeug.utils import secure_filename

from app.main import bp



# ############################################ #
# ##     New table layout for articles      ## #
# ############################################ #
# @bp.route('/articles2', methods=['GET', 'POST'])
@bp.route('/', methods=['GET', 'POST'])
@bp.route('/articles', methods=['GET', 'POST'])
@login_required
def articles():
    today_start = datetime(datetime.utcnow().year, datetime.utcnow().month, datetime.utcnow().day, 0, 0)
    today_end = today_start + timedelta(days=1)
    ev = Event.query.filter(Event.name =='visited platform', Event.date >= today_start, Event.date < today_end, Event.user_id==current_user.id).first()
    if not ev:
        ev = Event(user_id=current_user.id, name='visited platform', date=datetime.utcnow())
        db.session.add(ev)
        db.session.commit()
    
    month_start = datetime(datetime.utcnow().year, datetime.utcnow().month, 1, 0, 0)
    review_streak = Event.query.filter(Event.name =='reviewed a highlight', Event.user_id==current_user.id , Event.date >= month_start).count()


    query = current_user.articles.filter_by(archived=False)
    order = []
    col = getattr(Article, 'done')
    col = col.asc()
    order.append(col)
    col = getattr(Article, "date_read")
    col = col.desc()
    order.append(col)
  
    articles = query.order_by(*order).paginate(1, 15, False)
    has_next = articles.has_next if articles.has_next else None 
    count = query.count()
    suggestion = Suggestion.get_random()
    showing = f'Showing 0 to {count if count < 15 else 15} out of {count} articles.'

    if request.method == 'POST':
        data = json.loads(request.data)
        
        page = int(data['page'])
        per_page = data['per_page']
        title_sort = data['title_sort'].lower()
        opened_sort = data['opened_sort'].lower()
        status = data['status'].lower()
        search = data['search']
        tag_ids = data['tags']

        # print(title_sort)

        # first make user specific and unarchived
        query = Article.query.filter_by(user_id=current_user.id, archived=False)
        # total_count = query.count()

        # then filter for search
        if search != "":

            query =  query.filter(db.or_(
                Article.title.ilike(f'%{search}%'),
                Article.source_url.ilike(f'%{search}%'),
                Article.source.ilike(f'%{search}%'),
                Article.notes.ilike(f'%{search}%')
            ))
        
        # then filter by read status
        if status == "new":
           query = query.filter(Article.unread==True, Article.done==False)
        elif status == 'in progress':
            query = query.filter(Article.unread==False, Article.done==False)
        elif status == 'finished reading':
            query = query.filter(Article.unread==False, Article.done==True)

        # then filter by tags        
        if tag_ids != []:
            # these are just shortcuts to make the lines in the below queries shorter
            join_aid = tags_articles.c.article_id
            join_tid = tags_articles.c.tag_id

            query = query.join(tags_articles, (join_aid == Article.id))   
            query = query.filter(join_tid.in_(tag_ids))      

        # then sort 
        order = []
        col = getattr(Article, 'done')
        order.append(col.asc())
        if title_sort == 'desc':
            col = getattr(Article, "title")
            col = func.lower(col)
            col = col.desc()
            order.append(col)
        elif title_sort == 'asc':
            col = getattr(Article, "title")
            col = func.lower(col)
            col = col.asc()
            order.append(col) 
        if opened_sort == 'asc':
            if title_sort:
                col = getattr(Article, "date_read_date")
            else:
                col = getattr(Article, "date_read")
            col = col.asc()
            order.append(col)
        else:
            if title_sort:
                col = getattr(Article, "date_read_date")
            else:
                col = getattr(Article, "date_read")
            col = col.desc()
            order.append(col)
        query = query.order_by(*order)
   
        filtered_count = query.count()
        if per_page == 'all':
            per_page = filtered_count
        else:
            per_page = int(per_page)
        
        if filtered_count < per_page:
            visible_count = f'0 to {filtered_count}' 
        else:
            visible_count = f'{(per_page * page) - per_page } to {per_page * page}'

        query = query.paginate(page, per_page, False)
        has_next = query.has_next if query.has_next else None

        return json.dumps({'html': render_template('_all_articles.html', page=page, articles = query.items),
                            'showing':f'Showing {visible_count} out of {filtered_count} articles.',
                            'has_next': has_next })



    return render_template('articles_new.html', review_streak = review_streak, 
                           showing=showing, articles=articles.items, 
                           user=current_user,suggestion=suggestion, page=1, 
                           has_next=has_next)





# ########################################################### #
# ##     notifications / not finished needs front end      ## #
# ########################################################### #

@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])


# ########################################################### #
# ##     notifications / not finished needs front end      ## #
# ########################################################### #

@bp.route('/service-worker.js')
def sw():
    return current_app.send_static_file('service-worker.js')


# ################################ #
# ##     export highlights      ## #
# ################################ #

@bp.route('/export_highlights', methods=['POST'])
@login_required
def export_highlights():

    if current_user.get_task_in_progress('export_highlights'):
        return (json.dumps({'msg': 'An export task is currently in progress'}),
                    400, {'ContentType': 'application/json'})
    else:
        
        ev = Event(user_id=current_user.id, name='exported highlights', date=datetime.utcnow())
        db.session.add(ev)
        db.session.commit()

        data = json.loads(request.form['data'])
        u = User.query.get(current_user.id)

        if 'article_export' in data and data['article_export']:
            article_highlights = Article.query.get(data['article_id']).highlights.filter_by(archived=False).all()
            current_user.launch_task('export_highlights', 'Exporting highlights...', u, article_highlights, 'article', data['ext'])
            update_user_last_action('requested export')
            db.session.commit()
        
        elif 'topic_export' in data and data['topic_export']:
            data = json.loads(request.form['data'])
        
            search = data['search']
            has_topics = data['has_topics']
            created_sort = data['created_sort']
            topics = data['filters']
            per_page = data['per_page']          
            page = data['page']

            
            # first query unarchived highlights
            query = Highlight.query.filter_by(user_id=current_user.id, archived=False)
            
            # set desc order default
            col = getattr(Highlight, "created_date")
            col.desc()

            # filter for topics
            if topics != []:
        
                topic_ids = []
                
                for t in topics:
                    topic = Topic.query.filter_by(title=t).first()
                    topic_ids.append(topic.id)

                h_tid = highlights_topics.c.topic_id
                t_hid = highlights_topics.c.highlight_id

                query = query.join(highlights_topics, (t_hid == Highlight.id))
                query = query.filter(h_tid.in_(topic_ids))

            #filter for no_topics
            if has_topics.lower() == 'with_topics':
                query = query.filter(Highlight.no_topics==False)
            elif has_topics.lower() == 'no_topics':
                query = query.filter(Highlight.no_topics==True)

            # filter for sort 
            if created_sort == 'asc':
                col.asc()
            
            query = query.order_by(col)
    
            # then filter for search
            if data['search'] != "":
                query = query.join(Article, Highlight.article_id == Article.id)

                query =  query.filter(db.or_(
                    Highlight.text.ilike(f'%{search}%'),
                    Highlight.note.ilike(f'%{search}%'),
                    # Highlight.article_id.in_(article_ids)
                    Article.title.ilike(f'%{search}%')
                ))

            filtered_count = query.count()
            #highlights = query.all() 

            # paginate
            if per_page == 'all':
                per_page = filtered_count
                showing_count = filtered_count
            else:
                per_page = int(per_page)
                showing_count = f'{(per_page * page) - per_page} to {per_page * page}'
                
                if filtered_count < per_page:
                    showing_count = filtered_count  


            if not page:
                page = 1

            highlights = query.paginate(page, per_page, False).items

            current_user.launch_task('export_highlights', 'Exporting highlights...', u, highlights, 'topics', data['ext'])
            update_user_last_action('requested export')
            db.session.commit()
        else:
            return (json.dumps({'msg': 'Something went wrong.'}),
                    400, {'ContentType': 'application/json'})
    return (json.dumps({'msg': "Your export is being prepared. You will receive an email with download instructions shortly!"}),
            200, {'ContentType': 'application/json'})

# ##################################### #
# ##     Process incoming email      ## #
# ##################################### #

@bp.route('/email', methods=['POST'])
@csrf.exempt
def add_by_email():
    #print(request.form['from'])
    recipient = request.form['to']
    if '<' in recipient:
        recipient = recipient.split('<')[1][:-1]
    print('email to: ')
    print(recipient)
    u = User.query.filter_by(add_by_email=recipient).first()
    print('identified user:')
    print(u)
    emails = [e.email for e in Approved_Sender.query.filter_by(user_id=u.id).all()]
    print('approved senders:')
    print(emails)
    email = request.form['from'].lower()
    if '<' in email:
        email = request.form['from'].split('<')[1][:-1]
        print('sender: ')
        print(email)
    process = False
    if email in emails and u:
        login_user(u)
        process = True
    
    if process:
        print('processing email')

        for i in request.form:
            print(i)
            
        print('\n\n')

        subject = request.form.get('subject', False)
        html = request.form.get('html', False)
        text = request.form.get('text', False).lstrip()        
      
        if subject.lower().rstrip() == 'link':
            print('\n\n')
            print(subject)
            url = None
            
            if html:
                print('html')
                soup = BeautifulSoup(html, 'lxml')
                links = soup.find_all('a')
                url = links[0]['href'].rstrip()
            
            elif text:
                url = text.split('\n')[0].rstrip()
            else:
                print('no text in body')
                return 400
            
            if url:
                # print(url)
                # print('validating url')
                # print(validators.url(url))
                
                if not validators.url(url):
                    print('bad url')
                    return (json.dumps({'bad_url': True}),
                            400, {'ContentType': 'application/json'})

                urltext = pull_text(url)

                title = urltext["title"]
                content = urltext["content"]

                if not title or not content:
                    print('couldnt process article')
                    return (json.dumps({'bad_url': True}),
                            400, {'ContentType': 'application/json'})

                new_article = Article(unread=True, progress=0.0,
                                    title=title, source_url=url, content=content,
                                    user_id=u.id, archived=False,
                                    filetype="url")
                
        else:
            content = None
            if html:
                article = simple_json_from_html_string(html,
                                           content_digests=False,
                                           node_indexes=False,
                                           use_readability=True)
                content = article['content'] 
            elif text.rstrip() != '':
                content = text

            if subject:
                title = subject
            else:
                title = 'untitled'            

            if content:
                new_article = Article(unread=True, progress=0.0,
                                    title=title, source='email', content=content,
                                    user_id=current_user.id, archived=False,
                                    filetype="email")
            else:
                return 'No Content', 400

        db.session.add(new_article)
        new_article.date_read_date = datetime.utcnow().date()
        new_article.estimated_reading()
        
        u.launch_task("set_images_lazy", "lazy load images", new_article.id)
        u.launch_task("set_absolute_urls", "set absolute urls", new_article.id)

        ev = Event(user_id=current_user.id, name='added article', date=datetime.utcnow())
        db.session.add(ev)
        db.session.commit()

        db.session.commit()

        logout_user()
    
    return ''

# ######################## #
# ##     dashboard      ## #
# ######################## #

@bp.route('/app_dashboard/users', methods=['GET', 'POST'])
@login_required
@bp.errorhandler(CSRFError)
def user_dashboard():

    if request.method == 'POST':
        uid = json.loads(request.form['user'])
        u = User.query.filter_by(id=uid).first()
        u.test_account = True
        db.session.commit()

    users = data_dashboard()
    
    today_start = datetime(datetime.utcnow().year, datetime.utcnow().month, datetime.utcnow().day, 0, 0)
    month_start = datetime(datetime.utcnow().year, datetime.utcnow().month, 1, 0, 0)
    daily_active = db.session.query(Event.user_id).filter(Event.date >= today_start).distinct().join(User, Event.user_id == User.id).filter(User.test_account==False).count() - 1
    monthly_active = db.session.query(Event.user_id).filter(Event.date >= month_start).distinct().join(User, Event.user_id == User.id).filter(User.test_account==False).count() - 1
    

    return render_template('dashboard/user_dash.html', user=current_user,
                           users=users, daily_active=daily_active,
                           monthly_active = monthly_active)


@bp.route('/app_dashboard/suggestions', methods=['GET', 'POST'])
@login_required
@bp.errorhandler(CSRFError)
def suggestions_dashboard():

    form = SuggestionForm()
    if form.validate_on_submit():
        url = form.url.data
        title = form.title.data
        summary = form.summary.data

        suggestion = Suggestion(title=title, url=url, summary=summary)
        db.session.add(suggestion)
        db.session.commit()

    suggestions = Suggestion.query.all()

    return render_template('dashboard/suggestion_dash.html',
                           form=form, suggestions=suggestions)

# ########################## #
# ##    app feedback      ## #
# ########################## #

@bp.route('/feedback', methods=['POST'])
@login_required
@bp.errorhandler(CSRFError)
def feedback():

    data = json.loads(request.form['data'])
    recipients = ['research@lurnby.com']
    sender = 'team@lurnby.com'
    subject = 'App Feedback from ' + data['email']
    text_body = (data['email'] + '\n\n' + data['url'] + '\n\n' +
                 data['feedback'])

    html_body = ('<p>' + data['email'] + '</p><p>' + data['url']
                 + '</p><p>' + data['feedback'] + '</p>')

    send_email(subject, sender, recipients, text_body, html_body)
    update_user_last_action('submitted feedback')
    ev = Event(user_id=current_user.id, name='submitted feedback', date=datetime.utcnow())
    db.session.add(ev)

    return 'Thank you for the feedback!'


# ###################################### #
# ##     Pre load random article      ## #
# ###################################### #

@bp.route('/articles/add_suggestion', methods=['GET'])
@login_required
@bp.errorhandler(CSRFError)
def add_suggested_article():
    s = Suggestion.get_random()
    s.users.append(current_user)
    url = s.url
    
    urltext = pull_text(url)
    title = urltext["title"]
    content = urltext["content"]

    new_article = Article(unread=True, progress=0.0,
                                  title=title, source_url=url, content=content,
                                  user_id=current_user.id, archived=False,
                                  filetype="url")

    db.session.add(new_article)
    new_article.date_read_date = datetime.utcnow().date()
    new_article.estimated_reading()
    ev = Event(user_id=current_user.id, name='added suggested article', date=datetime.utcnow())
    db.session.add(ev)

    db.session.commit()

    form = ContentForm()

    articles = Article.return_articles_with_count()
    recent = articles['recent']
    done_articles = articles['done']
    unread_articles = articles['unread']
    read_articles = articles['read']

    x = render_template('articles_all.html', form=form,
                           recent=recent, 
                           done_articles=done_articles,
                           unread_articles=unread_articles,
                           read_articles=read_articles, user=current_user)

    return json.dumps({'content': x})


# ############################# #
# ##     Add New Article     ## #
# ############################# #


@bp.route('/articles/new', methods=['GET', 'POST'])
@login_required
@bp.errorhandler(CSRFError)
def add_article():

    form = ContentForm()


    def render_articles():
        query = current_user.articles.filter_by(archived=False)
        col = getattr(Article, "date_read")
        col = col.desc()
        articles = query.order_by(col).all()
        count = query.count()
        showing = f'Showing {count} out of {count} articles.'
        
        return render_template('_articles_with_filter.html',user=current_user, showing=showing, articles=articles)


    rendered_articles = render_articles()

    if request.method == 'POST':

        data = json.loads(request.data)

        notes = data['notes']
        tags = json.loads(data['tags'])
        pdf = data['pdf']
        epub = data['epub']
        title = data['title']
        source = data['source']
        content = data['content']
        url = data['url']

        try:
             not_epub = data['not_epub']
             
             if not_epub:
                return (json.dumps({'not_epub': True, 'html': rendered_articles}),
                        400, {'ContentType': 'application/json'})
        except:
            pass

        try:
            not_pdf = data['not_pdf']
            if not_pdf:
                return (json.dumps({'not_pdf': True, 'html': rendered_articles}),
                        400, {'ContentType': 'application/json'})
        except:
            pass

        today = date.today()
        today = today.strftime("%B %d, %Y")

        if (title == 'none' and url == 'none' 
            and epub == 'none' and pdf == 'none'):
            
            return (json.dumps({'no_article': True, 'html': rendered_articles}),
                    400, {'ContentType': 'application/json'})

        if (title != 'none'):

            if content == '':
                return (json.dumps({'manual_fail': True, 'html': rendered_articles}),
                        400, {'ContentType': 'application/json'})

            content = "<pre>" + content + "</pre>"
            if source == '':
                source = 'manually added ' + today

            new_article = Article(unread=True, notes=notes, progress=0.0,
                                  title=title, source=source, content=content,
                                  user_id=current_user.id, archived=False,
                                  filetype="manual")

            db.session.add(new_article)
            new_article.date_read_date = datetime.utcnow().date()
            new_article.estimated_reading()
            ev = Event.add('added article')
            if ev:
                db.session.add(ev)
                db.session.commit()
            

        if (url != 'none'):

            if not validators.url(url):
                print("can't validate url")

                return (json.dumps({'bad_url': True, 'html': rendered_articles}),
                        400, {'ContentType': 'application/json'})
            
            try:
                urltext = pull_text(url)
            except:
                print("can't extact text")

                return (json.dumps({'bad_url': True, 'html': rendered_articles}),
                        400, {'ContentType': 'application/json'})

            title = urltext["title"]
            content = urltext["content"]

            if not title or not content:
                print("no title or content")

                return (json.dumps({'bad_url': True, 'html': rendered_articles}),
                        400, {'ContentType': 'application/json'})

            new_article = Article(unread=True, notes=notes, progress=0.0,
                                  title=title, source_url=url, content=content,
                                  user_id=current_user.id, archived=False,
                                  filetype="url")

            db.session.add(new_article)
            new_article.date_read_date = datetime.utcnow().date()
            new_article.estimated_reading()
            ev = Event.add('added article')
            if ev:
                db.session.add(ev)
                db.session.commit()

        if pdf == 'true' or epub =='true':
            
            a_id = str(uuid4())
            url = s3.generate_presigned_url(
                ClientMethod='put_object', 
                Params={'Bucket': bucket, 'Key': a_id},
                ExpiresIn=3600)

            return (json.dumps({'processing': True, 'url':url, 'a_id': a_id}), 200, {'ContentType': 'application/json'})

        for tag in tags:
            t = Tag.query.filter_by(name=tag, user_id=current_user.id
                                    ).first()

            if not t:
                t = Tag(name=tag, archived=False, user_id=current_user.id)
                db.session.add(t)
                new_article.AddToTag(t)
            else:
                new_article.AddToTag(t)
            
    db.session.commit()
    current_user.launch_task("set_images_lazy", "lazy load images", new_article.id)
    current_user.launch_task("set_absolute_urls", "set absolute urls", new_article.id)

    db.session.commit()

    articles = Article.return_articles_with_count()
    recent = articles['recent']
    done_articles = articles['done']
    unread_articles = articles['unread']
    read_articles = articles['read']
    
    html = render_articles()

    # html = render_template('articles_all.html', form=form,
    #                        recent=recent, 
    #                        done_articles=done_articles,
    #                        unread_articles=unread_articles,
    #                        read_articles=read_articles, user=current_user)

    res = json.dumps({'processing':False, 'html': html})
    return (res, 200, {'ContentType': 'application/json'})
    


def handle_csrf_error(e):
    return (json.dumps({'success': False}),
            500, {'ContentType': 'application/json'})


# ################################ #
# ##     epub + pdf bg add      ## #
# ################################ #
@bp.route('/articles/bg', methods=['POST'])
def bg_add_article():
    data = json.loads(request.data)
    a_id = data['a_id']
    tags = json.loads(data['tags'])
    pdf = data['pdf']
    epub = data['epub']

    u = User.query.get(current_user.id)
    processing = current_user.launch_task('bg_add_article', 'adding article...',u, a_id, pdf, epub, tags)
    update_user_last_action('added article')
    
    ev = Event(user_id=current_user.id, name='added article', date=datetime.utcnow())
    db.session.add(ev)
    
    db.session.commit()

    res = json.dumps({'taskID': processing.id})
    return (res, 200, {'ContentType': 'application/json'})


# ########################################### #
# ##     epub + pdf processing status      ## #
# ########################################### #

@bp.route('/articles/processing/<task_id>/<a_id>')
def process_article(task_id, a_id):
    process = Task.query.get(task_id)


    # return (json.dumps({'html': 'success'}), 200, {'ContentType': 'application/json'})
    for i in range(25):
        time.sleep(1)
        if process.complete:
            query = current_user.articles.filter_by(archived=False)
            col = getattr(Article, "date_read")
            col = col.desc()
            articles = query.order_by(col).all()
            count = query.count()
            showing = f'Showing {count} out of {count} articles.'
            html = render_template('_articles_with_filter.html',user=current_user, showing=showing, articles=articles)
            ev = Event.add('added article')
            if ev:
                db.session.add(ev)
                db.session.commit()
            # delete object from amazon
            s3.delete_object(
                Bucket = bucket,
                Key = a_id
            )
            return (json.dumps({'html': html}), 200, {'ContentType': 'application/json'})

    return (json.dumps({'processing': True, 'taskID':process.id, 'a_id':a_id}), 200, {'ContentType': 'application/json'})


# ##################################### #
# ##     Get Reader preferences      ## #
# ##################################### #

@bp.route('/article/preferences', methods=['POST', 'GET'])
@login_required
def reader_preferences():
    if request.method == "POST":
        current_user.preferences = json.dumps(json.loads
                                              (request.form['Preferences']))

        db.session.commit()

        return (json.dumps({'success': True}),
                200, {'ContentType': 'application/json'})

    if request.method == "GET":
        preferences = current_user.preferences

        return jsonify({'Preferences': preferences})

# ########################################## #
# ##     Download images for article      ## #
# ########################################## #

@bp.route('/download/<int:id>/<path:resource>')
@login_required
def download_image(id,resource):
    
    if id != current_user.id:
        return 'resource not found', 403

    """ resource: name of the file to download"""
    url = s3.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': resource}, ExpiresIn = 30)
    return redirect(url, code=302)

# ########################### #
# ##     View Article      ## #
# ########################### #

@bp.route('/article/<uuid>', methods=['GET'])
@login_required
def article(uuid):
    uuid_hash = UUID(uuid)

    highlight_id = request.args.get('highlight_id', None)
    #highlight = request.args.get('highlight', None)
    """
    if highlight_id == 'burrito':
        highlight_id = request.args.get('highlight_id')
    else:
        highlight_id = "none"
    """
    
    article = Article.query.filter_by(uuid=uuid_hash).first()
    if article.user_id == current_user.id:
        article.unread = False
        article.last_reviewed = datetime.utcnow()
        
       
        ev = Event(user_id=current_user.id, name='opened article', date=datetime.utcnow())
        db.session.add(ev)

        db.session.commit()

        topics = Topic.query.filter_by(user_id=current_user.id, archived=False).order_by(Topic.last_used.desc()).all()
        content = article.content
        title = article.title
        progress = article.progress

        addtopicform = AddTopicForm()

        form = AddHighlightForm()
        try: 
            bookmarks = json.loads(article.bookmarks)
        except TypeError:
            bookmarks = {}

        if 'furthest' in bookmarks:
            furthest = bookmarks['furthest']
            bookmarks.pop('furthest')
        else:
            furthest = progress

        preferences = json.loads(current_user.preferences)
        size = preferences['size']
        spacing = preferences['spacing']
        color = preferences['color']
        font = preferences['font']
        article.date_read = datetime.utcnow()
        article.date_read_date = datetime.utcnow().date()
        update_user_last_action('opened article for reading')
        db.session.commit()

        return render_template('text.html', highlight_id=highlight_id,
                               article=article, user=current_user,
                               progress=progress, size=size, color=color,
                               font=font, spacing=spacing, title=title,
                               article_uuid=uuid, content=content, form=form,
                               addtopicform=addtopicform, topics=topics,
                               furthest=furthest, bookmarks=bookmarks)
    else:
        return render_template('errors/404.html'), 404


@bp.route('/article/<uuid>/notes', methods=['POST'])
@login_required
def updatearticlenotes(uuid):

    uuid_hash = UUID(uuid)

    article = Article.query.filter_by(uuid=uuid_hash).first()

    if current_user.id != article.user_id:
        return render_template('errors/404.html'), 404

   
    article.notes = request.form['updated_notes']
    db.session.commit()

    return (json.dumps({'success': True}),
            200, {'ContentType': 'application/json'})


@bp.route('/article/<uuid>/highlight-storage', methods=['POST', 'GET'])
@login_required
def storeHighlights(uuid):
    uuid_hash = UUID(uuid)

    article = Article.query.filter_by(uuid=uuid_hash).first()

    if request.method == "GET":
        serialized = article.highlightedText
        if serialized is not None:
            return jsonify({
                'SerializedHighlights': article.highlightedText
            })
        else:
            return (json.dumps({'success': False}),
                    403, {'ContentType': 'application/json'})

    if request.method == "POST":
        article.content = request.form['updated_content']
        db.session.commit()
        return (json.dumps({'success': True}),
                200, {'ContentType': 'application/json'})


@bp.route('/article/<uuid>/finished', methods=['GET'])
@login_required
def mark_read(uuid):
    uuid_hash = UUID(uuid)
    article = Article.query.filter_by(uuid=uuid_hash).first()
    
    if article.user_id == current_user.id:
        article.done = True
        db.session.commit()
        flash('Another article finished!', 'success')
        return redirect(url_for('main.articles'))
    else:
        return render_template('errors/404.html'), 404


@bp.route('/article/<uuid>/progress', methods=['GET', 'POST'])
@login_required
def storeProgress(uuid):
    uuid_hash = UUID(uuid)
    article = Article.query.filter_by(uuid=uuid_hash).first()

    if request.method == "POST":
        article.progress = request.form['Progress']

        if (request.form['Progress'] == 100):
            article.done = True

        db.session.commit()
        return (json.dumps({'success': True}),
                200, {'ContentType': 'application/json'})

    if request.method == "GET":
        progress = article.progress
        if progress is None:
            progress = 0

        return jsonify({'Progress': article.progress})

@bp.route('/article/<uuid>/bookmarks', methods=['POST'])
@login_required
def save_bookmarks(uuid):
    uuid_hash = UUID(uuid)
    article = Article.query.filter_by(uuid=uuid_hash).first()
    if article.user_id == current_user.id:
        bookmarks = json.loads(request.form['bookmarks'])
        article.bookmarks = json.dumps(bookmarks)
        db.session.commit()
        
    return 'Saved bookmarks', 200


@bp.route('/view_article/<uuid>', methods=['GET'])
@login_required
def view_article(uuid):
    uuid_hash = UUID(uuid)
    article = Article.query.filter_by(uuid=uuid_hash).first()
    if article.user_id == current_user.id:
        return render_template('viewarticle.html', article=article)
    else:
        return render_template('errors/404.html'), 404


@bp.route('/view_add_article/', methods=['GET'])
@login_required
def view_add_article():
    form = ContentForm()

    return render_template('add_article_modal.html', form=form,
                           user=current_user)


@bp.route('/articles/<uuid>/update', methods=['POST'])
@login_required
def updateArticle(uuid):

    form = ContentForm()
    uuid_hash = UUID(uuid)

    article = Article.query.filter_by(uuid=uuid_hash).first()
    if article.user_id == current_user.id:
        if request.method == "POST":

            data = json.loads(request.form['data'])

            if (data['read_status'] == 'read'):
                article.done = True

            if (data['read_status'] == 'unread'):
                article.done = False
                article.progress = 0.0
                article.unread = True

            if (data['read_status'] == 'keep'):
                article.done = False
                article.unread = False

            article.title = data['title']
            article.notes = data['notes']
            if 'content' in data:
                article.content = data['content']

            for tag in data['tags']:
                t = Tag.query.filter_by(name=tag, user_id=current_user.id
                                        ).first()
                if not t:
                    t = Tag(user_id=current_user.id, archived=False, name=tag)
                    db.session.add(t)
                    ev = Event.add('added tag')
                    if ev:
                        db.session.add(ev)
                article.AddToTag(t)

            for tag in data['remove_tags']:
                t = Tag.query.filter_by(name=tag, user_id=current_user.id
                                        ).first()
                if not t:
                    t = Tag(user_id=current_user.id, name=tag)
                    db.session.add(t)
                    ev = Event.add('added tag')
                    if ev:
                        db.session.add(ev)
                article.RemoveFromTag(t)
            
            ev = Event.add('updated article')
            if ev:
                db.session.add(ev)
            db.session.commit()

            query = current_user.articles.filter_by(archived=False)
            order = []
            col = getattr(Article, 'done')
            order.append(col.asc())
            col = getattr(Article, "date_read")
            order.append(col.desc())
            articles = query.order_by(*order).all()
            count = query.count()
            showing = f'Showing {count} out of {count} articles.'
            
            return render_template('_articles_with_filter.html',user=current_user, showing=showing, articles=articles)



            # articles = Article.return_articles_with_count()
            # recent = articles['recent']
            # done_articles = articles['done']
            # unread_articles = articles['unread']
            # read_articles = articles['read']

            # return render_template('articles_all.html', form=form,
            #                        done_articles=done_articles,
            #                        recent=recent,
            #                        unread_articles=unread_articles,
            #                        read_articles=read_articles,
            #                        user=current_user)
    else:
        render_template('errors/404.html'), 404


@bp.route('/articles/<uuid>/archive', methods=['GET', 'POST'])
@login_required
def archiveArticle(uuid):
    uuid_hash = UUID(uuid)
    article = Article.query.filter_by(uuid=uuid_hash).first()

    if article.user_id == current_user.id:
        article.archived = True
        db.session.commit()
        flash('Article has been archived. <a href="' +
              url_for('main.unarchiveArticle', uuid=uuid) +
              '"  class="main-button ">UNDO</a>', 'error')

        return redirect(url_for('main.articles'))
    else:
        return render_template('errors/404.html'), 404


@bp.route('/articles/<uuid>/unarchive', methods=['GET', 'POST'])
@login_required
def unarchiveArticle(uuid):
    uuid_hash = UUID(uuid)
    article = Article.query.filter_by(uuid=uuid_hash).first()
    article.archived = False
    db.session.commit()

    return redirect(url_for('main.articles'))

# ############################ #
# ##     Add highlight      ## #
# ############################ #

@bp.route('/article/addhighlight', methods=['POST'])
@login_required
def addhighlight():

    data = json.loads(request.form['data'])
    print(data)
    article = Article.query.filter_by(uuid=data['article_uuid']).first()

    newHighlight = Highlight(user_id=current_user.id,
                             article_id=article.id,
                             position=data['position'],
                             text=data['text'],
                             do_not_review=data['do_not_review'],
                             note=data['notes'], archived=False)

    db.session.add(newHighlight)
    
    ev = Event(user_id=current_user.id, name='added highlight', date=datetime.utcnow())
    db.session.add(ev)

    topics = data['topics']
    article = Article.query.filter_by(uuid=data['article_uuid']).first()

    for tag in article.tags.all():
        newHighlight.AddToTag(tag)

    for t in topics:
        topic = Topic.query.filter_by(title=t, user_id=current_user.id).first()
        if topic:
            newHighlight.AddToTopic(topic)
            topic.last_used = datetime.utcnow()
           
        else:
            newTopic = Topic(user_id=current_user.id, title=t, archived=False)
            db.session.add(newTopic)

            ev = Event(user_id=current_user.id, name='added topic', date=datetime.today())
            db.session.add(ev)

            newHighlight.AddToTopic(newTopic)
            newTopic.last_used = datetime.utcnow()


    db.session.commit()
    newHighlight.position = "#" + str(newHighlight.id)
    db.session.commit()

    article_url = url_for('main.article', uuid=article.uuid)
    
    return jsonify({
        'highlight_id': newHighlight.id,
        'highlight_text': newHighlight.text,
        'highlight_notes': newHighlight.note,
        'article_url': article_url,
        'topics': [t.title for t in Topic.query.filter_by(user_id=current_user.id, archived=False).order_by(Topic.last_used.desc()).all()]
    })


@bp.route('/view_highlight/<id>', methods=['GET', 'POST'])
@login_required
def view_highlight(id):

    highlight = Highlight.query.filter_by(id=id).first_or_404()

    if highlight.user_id != current_user.id:
        return render_template('errors/404.html'), 404

    article = Article.query.filter_by(id=highlight.article_id).first()

    addtopicform = AddTopicForm()
    form = AddHighlightForm()

    member = highlight.topics.filter_by(user_id=current_user.id, archived=False
                                        ).all()

    nonmember = highlight.not_in_topics(current_user)

    source = article.source
    source_url = article.source_url

    inappurl = (url_for('main.article', uuid=article.uuid) +
                '?highlight_id=highlight' + str(highlight.id) +
                '&highlight=burrito')

    article_title = article.title

    if request.method == 'GET':
        form.text.data = highlight.text
        form.note.data = highlight.note
        topics_list = [t.title for t in Topic.query.filter_by(archived=False, user_id=current_user.id).all()]
        nonmember_list = [t.title for t in nonmember]
        html = render_template('highlight.html', user=current_user,
                               highlight=highlight,
                               addtopicform=addtopicform, form=form,
                               member=member, nonmember=nonmember,
                               article_title=article_title, source=source,
                               source_url=source_url, inappurl=inappurl)
        return (json.dumps({'html': html,'nonmember_list':nonmember_list, 'topics_list':topics_list}),
                200, {'ContentType': 'application/json'})

    if request.method == 'POST':

        data = json.loads(request.form['data'])

        highlight.text = data['highlight']
        highlight.note = data['notes']
        highlight.do_not_review = data['do_not_review']

        members = data['topics']
        for member in members:
            topic = Topic.query.filter_by(title=member,
                                          user_id=current_user.id).first()
            if topic:
                highlight.AddToTopic(topic)
                topic.last_used = datetime.utcnow()
            
            else:
                t = Topic(user_id=current_user.id, title=member, archived=False)
                db.session.add(t)
                ev = Event(user_id=current_user.id, name='added topic', date=datetime.today())
                db.session.add(ev)
                highlight.AddToTopic(t)
                t.last_used = datetime.utcnow()

        nonmembers = data['untopics']
        for nonmember in nonmembers:
            topic = Topic.query.filter_by(title=nonmember,
                                          user_id=current_user.id).first()
            if topic:
                highlight.RemoveFromTopic(topic)
                
            

        if highlight.topics.count() == 0:
            highlight.no_topics = True
        else:
            highlight.no_topics = False

        ev = Event.add('updated highlight')
        if ev:
            db.session.add(ev)

        db.session.commit()
        
        topics_list = [t.title for t in current_user.topics.order_by(Topic.last_used.desc()).all()]

        # checks to see if the update highlight request is on the topics page
        if (data['topics-page'] == 'true'):

            # checks to see if the view was filtered
            if (
                    (data['atags'] and data['atags'] != [])
                    or (data['atopics'] and data['atopics'] != [])
                    ):

                # tag_ids = data['atags']
                topic_ids = data['atopics']
                active_tags = []
                active_topics = []

                # if tag_ids != [] and tag_ids:
                #     active_tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
                #     t_hid = tags_highlights.c.highlight_id

                #     h = Highlight.query \
                #         .filter_by(user_id=current_user.id,
                #                    archived=False
                #                    ).join(tags_highlights,
                #                           (t_hid == Highlight.id))

                #     highlights = h.filter(tags_highlights.c.tag_id.in_(tag_ids)
                #                           ).all()
                # else:
                #     highlights = Highlight.query \
                #                  .filter_by(user_id=current_user.id,
                #                             archived=False).all()

                if topic_ids != [] and topic_ids:
                    active_topics = Topic.query.filter(Topic.id.in_(topic_ids)
                                                       ).all()

                    topics = Topic.query.filter_by(archived=False,
                                                   user_id=current_user.id)

                    topics = topics.filter(Topic.id.in_(topic_ids)).all()
                else:
                    topics = Topic.query.filter_by(archived=False,
                                                   user_id=current_user.id
                                                   ).order_by(Topic.last_used.desc()).all()

                notopics = []

                for highlight in highlights:
                    if highlight.not_added_topic():
                        notopics.append(highlight)

                filter_topics = Topic.query.filter_by(archived=False,
                                                      user_id=current_user.id
                                                      ).all()

                return render_template('topics_all.html',
                                       active_tags=active_tags,
                                       active_topics=active_topics,
                                       user=current_user,
                                       filter_topics=filter_topics,
                                       topics=topics, highlights=highlights,
                                       notopics=notopics)

            # if no filters active
            topics = Topic.query.filter_by(archived=False,
                                           user_id=current_user.id).all()

            highlights = Highlight.query.filter_by(user_id=current_user.id,
                                                   archived=False).all()

            notopics = []

            for highlight in highlights:
                if highlight.not_added_topic():
                    notopics.append(highlight)

            active_topics = []
            active_tags = []

            filter_topics = Topic.query.filter_by(archived=False,
                                                  user_id=current_user.id
                                                  ).all()

            return render_template('topics_all.html', active_tags=active_tags,
                                   active_topics=active_topics,
                                   user=current_user,
                                   filter_topics=filter_topics,
                                   topics=topics, highlights=highlights,
                                   notopics=notopics)

        return (json.dumps({'success': True, 'topics':topics_list}),
                200, {'ContentType': 'application/json'})


@bp.route('/archivehighlight/<id>')
@login_required
def archivehighlight(id):

    highlight = Highlight.query.filter_by(id=id).first()
    if current_user.id != highlight.user_id:
        return render_template('errors/404.html'), 404

    highlight.archived = True
    db.session.commit()

    

    return (json.dumps({'success': True}),
            200, {'ContentType': 'application/json'})

@bp.route('/unarchivehighlight/<id>')
@login_required
def unarchivehighlight(id):

    highlight = Highlight.query.filter_by(id=id).first()
    if current_user.id != highlight.user_id:
        return render_template('errors/404.html'), 404

    highlight.archived = False
    db.session.commit()

    return (json.dumps({'success': True}),
        200, {'ContentType': 'application/json'})


##########################
#                        #
#  Topics functions      #
#                        #
##########################

@bp.route('/highlights', methods=['GET', 'POST'])
@login_required
def highlights():
    month_start = datetime(datetime.utcnow().year, datetime.utcnow().month, 1, 0, 0)
    review_streak = Event.query.filter(Event.name =='reviewed a highlight', Event.user_id==current_user.id , Event.date >= month_start).count()


    query = Highlight.query.filter_by(user_id=current_user.id, archived=False)
    total_count = query.count()
    filtered_count = total_count
    showing_count = '0 to 15'
    col = getattr(Highlight, "created_date")
    topic_sort = getattr(Topic, "last_used").desc()

    highlights = query.order_by(col.desc()).paginate(1, 15, False).items

    topics = current_user.topics.filter_by(archived=False).order_by(topic_sort).all()

    if request.method == 'POST':
        data = json.loads(request.form['data'])
        
        search = data['search']
        has_topics = data['has_topics']
        created_sort = data['created_sort']
        topics = data['filters']
        per_page = data['per_page']          
        page = data['page']

        
        # first query unarchived highlights
        query = Highlight.query.filter_by(user_id=current_user.id, archived=False)
        
        # set desc order default
        col = getattr(Highlight, "created_date")
        topic_sort = getattr(Topic, "last_used").desc()

        
        all_user_topics = current_user.topics.filter_by(archived=False).order_by(topic_sort).all()
        print(topics)
        # filter for topics
        if topics != []:
    
            topic_ids = []
            
            for t in topics:
                topic = Topic.query.filter_by(title=t, user_id=current_user.id).first()
                all_user_topics.remove(topic)
                topic_ids.append(topic.id)

            h_tid = highlights_topics.c.topic_id
            t_hid = highlights_topics.c.highlight_id

            query = query.join(highlights_topics, (t_hid == Highlight.id))
            query = query.filter(h_tid.in_(topic_ids))

        #filter for no_topics
        if has_topics.lower() == 'with_topics':
            query = query.filter(Highlight.no_topics==False)
        elif has_topics.lower() == 'no_topics':
            query = query.filter(Highlight.no_topics==True)
    

        # filter for sort 
        if created_sort == 'asc':        
            query = query.order_by(col.asc())
        else:
            query = query.order_by(col.desc())

 
        # then filter for search
        if data['search'] != "":
            query = query.join(Article, Highlight.article_id == Article.id)

            query =  query.filter(db.or_(
                Highlight.text.ilike(f'%{search}%'),
                Highlight.note.ilike(f'%{search}%'),
                # Highlight.article_id.in_(article_ids)
                Article.title.ilike(f'%{search}%')
            ))
        

        filtered_count = query.count()
        #highlights = query.all() 

        # paginate
        if per_page == 'all':
            per_page = filtered_count
            showing_count = filtered_count
        else:
            per_page = int(per_page)
            showing_count = f'{(per_page * page) - per_page} to {per_page * page}'
            
            if filtered_count < per_page:
                showing_count = filtered_count  


        if not page:
            page = 1

        highlights = query.paginate(page, per_page, False)

        print(highlights.items)

        
        data = {
            'topics': [topic.title for topic in all_user_topics],
            'html': render_template('filter_highlights.html', highlights=highlights.items, page=page),
            'filtered_count': filtered_count,
            'showing_count': showing_count,
            'has_next': highlights.has_next if highlights.has_next else None       
        }

        return json.dumps(data)


    return render_template('highlights.html', user=current_user, 
                           highlights = highlights, topics=topics, page=1,
                           showing_count=showing_count, 
                           review_streak=review_streak, 
                           filtered_count=filtered_count)


@bp.route('/topics', methods=['GET', 'POST'])
@login_required
def topics():

    pass


@bp.route('/topics/add', methods=['POST'])
@login_required
def add_new_topic():

    pass


@bp.route('/topics/rename/<id>', methods=['POST'])
@login_required
def rename_topic(id):
    pass

@bp.route('/archivetopic/<topic_id>', methods=['POST'])
@login_required
def archivetopic(topic_id):

    pass

@bp.route('/unarchivetopic/<topic_id>', methods=['POST'])
@login_required
def unarchivetopic(topic_id):
    pass

@bp.route('/review', methods=['GET', 'POST'])
def review():

    col = getattr(Topic, "last_used").desc()
    topics = current_user.topics.filter_by(archived=False).order_by(col).all()
    highlights = current_user.highlights.filter_by(archived=False, do_not_review=False).all()
    tiers = order_highlights(highlights)
    empty = True
    for i in range(8):
        if len(tiers[i]) > 0:
            empty = False
            break
    days = [
        '1 day', '3 days', '1 week', '2 weeks', '1 month', '3 months', 'half a year', '1 year'
    ]

    if request.method == 'POST':

        data = json.loads(request.form['data'])
        highlights = []
        if data['filters'] != []:
            for t in data['filters']:
                topic = Topic.query.filter_by(title=t, user_id=current_user.id).first()
                
                highlights += topic.highlights.filter_by(archived=False).all()
            
            #print(highlights)
            highlights = list(set(highlights))
            #print(highlights)
            tiers = order_highlights(highlights)
            #print(tiers)
            empty = True
            for i in range(8):
                if len(tiers[i]) > 0:
                    empty = False
                    break
        else:
            highlights = current_user.highlights.filter_by(archived=False, do_not_review=False).all()  
            tiers = order_highlights(highlights)
            empty = True
            for i in range(8):
                if len(tiers[i]) > 0:
                    empty = False
                    break

        data = {
            'topics': [topic.title for topic in topics],
            'html': render_template('filter_review.html', tiers=tiers, 
                                    days=days, empty=empty)
        }

        return json.dumps(data)
        


    return render_template('review.html', topics=topics, tiers=tiers, days=days, empty=empty)

@bp.route('/review/settings', methods=['POST'])
def update_review_settings():
    data = json.loads(request.data)
    count = data['count']
    current_user.review_count = count
    db.session.commit()

    return (json.dumps({'success': True}),
                200, {'ContentType': 'application/json'})



@bp.route('/tier/<id>', methods=['POST'])
def tier(id):

    today_start = datetime(datetime.utcnow().year, datetime.utcnow().month, datetime.utcnow().day, 0, 0)
    today_end = today_start + timedelta(days=1)
    ev = Event.query.filter(Event.name =='reviewed highlights', Event.date >= today_start, Event.date < today_end).first()
    if not ev:
        ev = Event(user_id=current_user.id, name='reviewed highlights', date=datetime.utcnow())
        db.session.add(ev)
    
    ev = Event(user_id=current_user.id, name='reviewed a highlight', date=datetime.utcnow())
    db.session.add(ev) 
    
    db.session.commit()


    highlight = Highlight.query.filter_by(id=id).first()
    data = json.loads(request.form['data'])
    if data['tier'] == 'keep':
        # print('keep tier', highlight)
        highlight.review_date = datetime.utcnow()
        current_user.last_action = 'reviewed highlights'
        db.session.commit()

        return (json.dumps({'success': True}),
                200, {'ContentType': 'application/json'})

    if data['tier'] == 'lower':
        print('lower tier', highlight)
        highlight.review_schedule = highlight.review_schedule - 1
        highlight.review_date = datetime.utcnow()
        current_user.last_action = 'reviewed highlights'
        db.session.commit()

        return (json.dumps({'success': True}),
                200, {'ContentType': 'application/json'})
    
    if data['tier'] == 'raise':
        #print('raise tier', highlight)
        if highlight.review_schedule != 7:
            highlight.review_schedule = highlight.review_schedule + 1
            highlight.review_date = datetime.utcnow()
            current_user.last_action = 'reviewed highlights'
            db.session.commit()

        return (json.dumps({'success': True}),
                200, {'ContentType': 'application/json'})

    return (json.dumps({'success': False}),
                400, {'ContentType': 'application/json'})

@bp.route('/resources', methods=['GET'])
@login_required
def resources():

    return render_template('resources.html')
