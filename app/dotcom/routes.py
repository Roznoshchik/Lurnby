from flask import (flash, redirect, url_for, render_template, request,
                   current_app, send_file, json)
from flask_login import current_user, login_required
from flask_wtf.csrf import CSRFError


from app.dotcom import bp
from app import csrf, db, s3, bucket

from datetime import datetime, timedelta

import os

# ################################## #
# ##     Download from amazon     ## #
# ################################## #
@bp.route('/download/<int:id>/<path:resource>')
@login_required
def download_image(id,resource):
    
    if id != current_user.id:
        return 'resource not found', 403

    print(id)
    print(resource)
    """ resource: name of the file to download"""
    url = s3.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': resource}, ExpiresIn = 30)
    return redirect(url, code=302)





# ############################# #
# ##     service worker      ## #
# ############################# #
@bp.route('/service-worker.js')
def serviceworker():
    
    x = send_file('service-worker.js')
    return x


# ##################### #
# ##     robots      ## #
# ##################### #
@bp.route('/robots.txt')
def robots():
    if os.environ.get('DEV'):
        x = send_file('robots-dev.txt')
    else:
        x = send_file('robots-prod.txt')
    return x


@bp.route('/')
@bp.route('/index')
def index():
    return render_template('dotcom/landing.html')


@bp.route('/who-is-lurnby-for')
def who():

    return render_template('dotcom/who-is-lurnby-for.html')


@bp.route('/how-lurnby-works')
def how():

    return render_template('dotcom/how-lurnby-works.html')


@bp.route('/how-much-lurnby-costs')
def costs():

    return render_template('dotcom/how-much-lurnby-costs.html')


@bp.route('/how-to-start-using-lurnby')
def use():

    return render_template('dotcom/how-to-start-using-lurnby.html')


@bp.route('/find-out-more-about-lurnby')
def questions():

    return render_template('dotcom/find-out-more-about-lurnby.html')


@bp.route('/tutorials-and-demos')
def tutorials():

    return render_template('dotcom/tutorials-and-demos.html')


