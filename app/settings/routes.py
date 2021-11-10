from flask import (flash, redirect, url_for, render_template, request,
                   current_app)
from flask_login import current_user, login_required
from flask_wtf.csrf import CSRFError


from app.settings import bp
from app.models import Approved_Sender, User, update_user_last_action, Event
from app.settings.forms import AddApprovedSenderForm
from app.auth.forms import UpdateAccountForm
from app import db

from datetime import datetime, timedelta


# ############################### #
# ##     Account settings      ## #
# ############################### #
@bp.route('/settings/account', methods=['GET', 'POST'])
@login_required
@bp.errorhandler(CSRFError)
def settings_account():
    approved_senders = Approved_Sender.query.filter_by(user_id=current_user.id
                                                       ).all()
    form = UpdateAccountForm()

    if form.validate_on_submit():
        
        flash('Settings updated!', 'success')
        return redirect(url_for('settings.settings_account'))

        
    # return render_template('settings.html',form=form, senders=approved_senders)
    return render_template('settings/settings_content.html',form=form, senders=approved_senders)

# ############################# #
# ##     email settings      ## #
# ############################# #

@bp.route('/settings/email', methods=['GET', 'POST'])
@login_required
@bp.errorhandler(CSRFError)
def settings_email():
    approved_senders = Approved_Sender.query.filter_by(user_id=current_user.id
                                                       ).all()
    form = AddApprovedSenderForm()

    if form.validate_on_submit():
        email = form.email.data
        update_user_last_action('added approved sender')
        print('adding approved sender:')
        print(email)
        email = email.lower()
        print(email)
        e = Approved_Sender(user_id=current_user.id, email=email)
        db.session.add(e)

        ev = Event(user_id=current_user.id, name='added approved sender', date=datetime.utcnow())
        db.session.add(ev)

        db.session.commit()

        return redirect(url_for('settings.settings_email'))
        
    # return render_template('settings.html',form=form, senders=approved_senders)
    return render_template('settings/settings_content.html',form=form, senders=approved_senders)

@bp.route('/enable-add-by-email', methods=['POST'])
@login_required
@bp.errorhandler(CSRFError)
def enable_add_by_email():
    current_user.set_lurnby_email()
    update_user_last_action('enabled add by email')
    e = Approved_Sender(user_id=current_user.id, email=current_user.email)
    db.session.add(e)
    ev = Event(user_id=current_user.id, name='enabled add by email', date=datetime.utcnow())
    db.session.add(ev)
    
    db.session.commit()

    return '', 200
