import os
import sys
import json
from rq import get_current_job
from flask import render_template

from app import create_app, db, s3, bucket
from app.email import send_email
from app.models import Task, Article, Highlight

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