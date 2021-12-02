from datetime import date, datetime, timedelta
import glob
import os
import sys
import json
import boto3
from rq import get_current_job
from flask import render_template, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename
from bs4 import BeautifulSoup


from app import create_app, db, s3, bucket
from app.export import get_zip
from app.email import send_email
from app.main.ebooks import epubTitle, epubConverted
from app.main.pdf import importPDF
from app.models import Task, Article, Highlight, Tag, User, Event


app = create_app()
app.app_context().push()

def delete_user(u):
    highlights=u.highlights.all()
    topics = u.topics.all()
    articles = u.articles.all()
    tags = u.tags.all()
    senders = u.approved_senders.all()
    comms = u.comms
    for h in highlights:
        db.session.execute(f'DELETE from highlights_topics where highlight_id={h.id}')
        db.session.delete(h)
    for t in topics:
        db.session.execute(f'DELETE from highlights_topics where topic_id={t.id}')
        db.session.delete(t)
    for t in tags:
        db.session.execute(f'DELETE from tags_articles where tag_id={t.id}')
        db.session.delete(t)
    for a in articles:
        db.session.execute(f'DELETE from tags_articles where article_id={a.id}')
        db.session.delete(a)
    for s in senders:
        db.session.delete(s)
    db.session.delete(comms)
    #db.session.delete(u)
    u.email=None
    u.goog_id=None
    u.firstname = None
    u.username = None
    u.add_by_email=None
    u.token=None
    u.deleted=True
    db.session.commit()


def _set_task_progress(progress):
    job = get_current_job()
  
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress',
                                   {'task_id': job.get_id(),
                                     'progress': progress })
        if progress >= 100:
            task.complete = True
        db.session.commit()


def account_export(uid, ext, delete=False):
    try:
        _set_task_progress(0)
        user = User.query.get(uid)
        if ext != 'none':
            print('exporting')
            if os.environ.get('DEV'):
                az_path_base = f'staging/{user.id}/exports/'
            else:
                az_path_base = f'{user.id}/exports/'
            filename = get_zip(user, ext)
            az_path = f'{az_path_base}lurnby-export.zip'
            s3.upload_file(
                Bucket = bucket,

                Filename=filename,
                Key=az_path
                )
            location = s3.get_bucket_location(Bucket=bucket)['LocationConstraint']
            #url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, az_path)
            url = s3.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': az_path}, ExpiresIn = 604800)

            delete_date = (datetime.today()+ timedelta(days=7)).strftime("%B %d, %Y")
            send_email('[Lurnby] Your exported data',
                    sender=app.config['ADMINS'][0], recipients=[user.email],
                    text_body=render_template('email/export_highlights.txt', url=url, user=user, delete_date=delete_date),
                    html_body=render_template('email/export_highlights.html', url=url, user=user, delete_date=delete_date),
                    sync=True)
        if delete:
            # if os.environ.get('DEV'):
            #     az_path_base = f'staging/{user.id}/'
            # else:
            #     az_path_base = f'{user.id}/'

            # az = boto3.resource('s3')
            # buck = az.Bucket(bucket)
            # buck.objects.filter(Prefix=az_path_base).delete()
            delete_user(user)

            # for tag in user.tags.all():
            #     db.session.delete(tag)
            # for highlight in user.highlights.all():
            #     db.session.delete(highlight)
            # for topic in user.topics.all():
            #     db.session.delete(topic)
            # for article in user.articles.all():
            #     db.session.delete(article)
            # _set_task_progress(100)
            # db.session.delete(user)
            # db.session.commit()
        
    except:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
  


def export_highlights(user, highlights, source, ext):
    try:
        _set_task_progress(0)
        data = []
        i = 0
        total_highlights = len(highlights)
        
        basedir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(
            basedir, 'temp'
        )

        if not os.path.isdir(path):
            os.mkdir(path)

        if os.environ.get('DEV'):
            az_path_base = f'staging/{user.id}/exports/'
        else:
            az_path_base = f'{user.id}/exports/'


        if ext == 'txt':
            if source == 'article':
                a = Article.query.get(highlights[0].article_id)
                title = a.title
                a_source = a.source_url if a.source_url else a.source
                with open(f'{path}/highlights.txt', 'w', encoding='utf-16') as f:
                    f.write(f'FROM: {title} \nSOURCE: {a_source}\n\n')
                    for highlight in highlights:
                        highlight = Highlight.query.get(highlight.id) 
                        f.write(f'TEXT:\n{highlight.text}\n\n')
                        if highlight.note:
                            f.write(f'NOTE:\n{highlight.note}\n\n')
                        if highlight.topics.count() > 0:
                            f.write(f'TOPICS:\n{", ".join([topic.title for topic in highlight.topics.filter_by(archived=False).all()])}\n\n')
                        i += 1
                        _set_task_progress(100 * i // total_highlights)
                    f.write('\n')
            else:
                with open(f'{path}/highlights.txt', 'w', encoding='utf-16') as f:
                    for highlight in highlights:
                        highlight = Highlight.query.get(highlight.id) 
                        a = highlight.article
                        title = a.title
                        a_source = a.source_url if a.source_url else a.source
                        f.write(f'FROM: {title}\nSOURCE: {a_source}\n\n')
                        f.write(f'TEXT:\n{highlight.text}\n\n')
                        if highlight.note:
                            f.write(f'NOTE:\n{highlight.note}\n\n')
                        f.write(f'TOPICS:\n{", ".join([topic.title for topic in highlight.topics.filter_by(archived=False).all()])}\n\n')
                        f.write('\n')
                        
                        i += 1
                        _set_task_progress(100 * i // total_highlights)
                    f.write('\n')
            
            filename = f'{path}/highlights.txt'
            az_path = f'{az_path_base}highlights.txt'
            s3.upload_file(
                Bucket = bucket,
                Filename=filename,
                Key=az_path
                )
            location = s3.get_bucket_location(Bucket=bucket)['LocationConstraint']
            #url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, az_path)
            url = s3.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': az_path}, ExpiresIn = 604800)



            send_email('[Lurnby] Your exported highlights',
                    sender=app.config['ADMINS'][0], recipients=[user.email],
                    text_body=render_template('email/export_highlights.txt', url=url, user=user),
                    html_body=render_template('email/export_highlights.html', url=url, user=user),
                    sync=True)
            
        else:
            for highlight in highlights:
                highlight = Highlight.query.get(highlight.id)
                if source == 'topics':
                    data.append({
                            'from': highlight.article.title,
                            'source': highlight.article.source_url if highlight.article.source_url else highlight.article.source,
                            'text': highlight.text,
                            'note': highlight.note,
                            'topics': [topic.title for topic in highlight.topics.filter_by(archived=False).all()]
                            })
                else:
                    data.append({'text': highlight.text,
                                'note': highlight.note,
                                'topics': [topic.title for topic in highlight.topics.filter_by(archived=False).all() ]
                                })
                i += 1
                _set_task_progress(100 * i // total_highlights)

            with open(f'{path}/highlights.json', 'w', encoding='utf-16') as f:
                f.write(json.dumps({'highlights': data}, ensure_ascii=False, indent=4))
           
            filename = f'{path}/highlights.json'
            az_path = f'{az_path_base}highlights.json'
            s3.upload_file(
                Bucket = bucket,
                Filename=filename,
                Key=az_path
                )
            location = s3.get_bucket_location(Bucket=bucket)['LocationConstraint']
            # url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, az_path)
            url = s3.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': az_path}, ExpiresIn = 604800)


            send_email('[Lurnby] Your exported highlights',
                    sender=app.config['ADMINS'][0], recipients=[user.email],
                    text_body=render_template('email/export_highlights.txt', url=url, user=user),
                    html_body=render_template('email/export_highlights.html', url=url, user=user),
                    sync=True)                
                
    except:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)

    
def bg_add_article(u, a_id, pdf, epub, tags):
    try:
        _set_task_progress(0)
        today = date.today()
        today = today.strftime("%B %d, %Y")
        
        basedir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(
            basedir, 'temp'
        )

        if not os.path.isdir(path):
            os.mkdir(path)

        path = f'{path}/{a_id}'

        if pdf == 'true':
            path = f'{path}.pdf'
            with open(path, "w") as f:
                pass
            s3.download_file(bucket, a_id, path)

            _set_task_progress(10)
            pdf = importPDF(path, u)
            _set_task_progress(90)
            source = 'PDF File: added ' + today

            article = Article(content=pdf['content'], archived=False,
                            source=source, progress = 0.0,
                            unread=True, title=pdf['title'],
                            user_id = u.id, filetype='pdf')
            db.session.add(article)
            article.date_read_date = datetime.utcnow().date()
            article.estimated_reading()
            for tag in tags:
                t = Tag.query.filter_by(name=tag, user_id=u.id
                                        ).first()

                if not t:
                    t = Tag(name=tag, archived=False, user_id=u.id)
                    db.session.add(t)
                    article.AddToTag(t)

                else:
                    article.AddToTag(t)

            db.session.commit()
        else:
            path = f'{path}.epub'
            s3.download_file(bucket, a_id, path)

            content = epubConverted(path, u)
            title = epubTitle(path)
            title = title[0][0]
            epubtext = content

            source = 'Epub File: added ' + today

            new_article = Article(unread=True, title=title, content=epubtext,
                                source=source, user_id=u.id,
                                archived=False, progress=0.0,
                                filetype="epub")

            db.session.add(new_article)
            new_article.date_read_date = datetime.utcnow().date()
            new_article.estimated_reading()

            for tag in tags:
                t = Tag.query.filter_by(name=tag, user_id=u.id
                                        ).first()

                if not t:
                    t = Tag(name=tag, archived=False, user_id=u.id)
                    db.session.add(t)
                    new_article.AddToTag(t)

                else:
                    new_article.AddToTag(t)

            db.session.commit()
            os.remove(path)
            
    except:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)

def set_images_lazy(aid):
    try:
        _set_task_progress(0)
        a = Article.query.get(aid)
        soup = BeautifulSoup(a.content, "html5lib")
        images = soup.find_all("img")
        for img in images:
            img["loading"] = "lazy"
        a.content = str(soup.prettify())
        db.session.commit()
    except:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)

def set_absolute_urls(aid):
    try:
        _set_task_progress(0)
        a = Article.query.get(aid)
        if a.source_url:
            soup = BeautifulSoup(a.content, "html5lib")
            images = soup.find_all("img")
            for img in images:
                try:
                    if 'http' not in img['src']:
                        img['src'] = f'{a.source_url}{img["src"]}'
                except:
                    print('no src in image')
            links = soup.find_all('a')
            for l in links:
                try:
                    if 'http' not in l['href']:
                        l['href'] = f'{a.source_url}{l["href"]}'
                except:
                    print('no href in url')
            a.content = str(soup.prettify())
            db.session.commit()
    except:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)