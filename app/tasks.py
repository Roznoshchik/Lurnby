from datetime import date
import os
import sys
import json
from rq import get_current_job
from flask import render_template
from flask_login import current_user
from werkzeug.utils import secure_filename
from bs4 import BeautifulSoup


from app import create_app, db, s3, bucket
from app.email import send_email
from app.main.ebooks import epubTitle, epubConverted
from app.main.pdf import importPDF
from app.models import Task, Article, Highlight, Tag


app = create_app()
app.app_context().push()

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
            url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, az_path)
            
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
            url = "https://s3-%s.amazonaws.com/%s/%s" % (location, bucket, az_path)
            
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