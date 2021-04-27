import sys
import json
from rq import get_current_job
from flask import render_template

from app import create_app, db
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
        
        if ext == 'txt':
            if source == 'article':
                a = Article.query.get(highlights[0].article_id)
                title = a.title
                a_source = a.source_url if a.source_url else a.source
                with open('temp/highlights.txt', 'w', encoding='utf-8') as f:
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
                    
                with open('temp/highlights.txt', 'r', encoding='utf-8') as txt:
                    
                    send_email('[Lurnby] Your exported highlights',
                            sender=app.config['ADMINS'][0], recipients=[user.email],
                            text_body=render_template('email/export_highlights.txt', user=user),
                            html_body=render_template('email/export_highlights.html', user=user),
                            attachments=[('highlights.txt', 'text/plain', txt.read())],
                            sync=True)
                    
            else:
                with open('highlights.txt', 'w') as f:
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

                with open('highlights.txt', 'r') as f:
                    send_email('[Lurnby] Your exported highlights',
                            sender=app.config['ADMINS'][0], recipients=[user.email],
                            text_body=render_template('email/export_highlights.txt', user=user),
                            html_body=render_template('email/export_highlights.html', user=user),
                            attachments=[('highlights.txt', 'text/plain', f.read())],
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

            send_email('[Lurnby] Your exported highlights',
                sender=app.config['ADMINS'][0], recipients=[user.email],
                text_body=render_template('email/export_highlights.txt', user=user),
                html_body=render_template('email/export_highlights.html', user=user),
                attachments=[('highlights.json', 'application/json',
                            json.dumps({'highlights': data}, indent=4))],
                sync=True)

    except:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)