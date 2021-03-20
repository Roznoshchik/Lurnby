import os

from flask import render_template, request
from flask_login import current_user
from werkzeug.utils import secure_filename

from app import s3, bucket, db
from app.experiments import bp
from app.main.pdf import importPDF
from app.models import Article, User


@bp.route('/uploads', methods = ['GET', 'POST'])
def uploads():
    msg = None
    form  = request.form
    if request.method == 'POST':
        upload = request.files['file']
        if upload:
              
            filename = secure_filename(upload.filename)
            
            basedir = os.path.abspath(os.path.dirname(__file__))

            path = os.path.join(
                basedir, 'temp'
            )

            if not os.path.isdir(path):
                os.mkdir(path)

            path = os.path.join(
                basedir, 'temp', filename
            )

            upload.save(path)

            pdf = importPDF(path)

            article = Article(content = pdf['content'], archived=False,
                              unread=True, title=pdf['title'],
                              user_id = current_user.id)
            db.session.add(article)
            db.session.commit()

    return render_template('experiments/uploads.html', msg=msg)
    
    