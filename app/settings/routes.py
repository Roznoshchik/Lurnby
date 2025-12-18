from flask import flash, redirect, url_for, render_template, request, json
from flask_login import current_user, login_required, logout_user, login_user
from flask_wtf.csrf import CSRFError


from app.settings import bp
from app.models import Approved_Sender, User, update_user_last_action, Event
from app.models.event import EventName
from app.settings.forms import (
    AddApprovedSenderForm,
    DeleteAccountForm,
    CommunicationForm,
)
from app.auth.forms import UpdateAccountForm, UpdatePasswordForm, UpdateEmailForm
from app.settings.email import send_email_verification, send_delete_verification
from app import db

from datetime import datetime


# ############################### #
# ##     Account settings      ## #
# ############################### #


@bp.route("/settings/account", methods=["GET", "POST"])
@login_required
@bp.errorhandler(CSRFError)
def settings_account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        flash("Settings updated!", "success")
        name = form.firstname.data
        username = form.username.data

        current_user.firstname = name
        current_user.username = username.lower()
        ev = Event.add("updated user credentials")
        if ev:
            db.session.add(ev)

        db.session.commit()

    u = {
        "username": current_user.username
        if current_user.username
        else current_user.email,
        "name": current_user.firstname if current_user.firstname else None,
        "email": current_user.email,
    }

    # return render_template('settings.html',form=form, senders=approved_senders)
    return render_template("settings/settings_account.html", form=form, u=u)


# ############################# #
# ##     Update password     ## #
# ############################# #


@bp.route("/settings/account/password", methods=["GET", "POST"])
@login_required
@bp.errorhandler(CSRFError)
def update_password():
    form = UpdatePasswordForm()
    pw = False
    if current_user.password_hash:
        pw = True

    if form.validate_on_submit():
        new = form.new_password.data
        if pw:
            curr = form.current_password.data
            if current_user.check_password(curr):
                current_user.set_password(new)
            else:
                flash("Current password is incorrect", "error")
                # return redirect(url_for('settings.update_password'))
                return render_template(
                    "settings/settings_password.html", form=form, pw=pw
                )
        else:
            current_user.set_password(new)

        flash("Password Set!", "success")
        ev = Event.add("updated password")
        if ev:
            db.session.add(ev)
        db.session.commit()

        return redirect(url_for("settings.settings_account"))

    return render_template("settings/settings_password.html", form=form, pw=pw)


# ########################### #
# ##     Update email      ## #
# ########################### #


@bp.route("/settings/account/email", methods=["GET", "POST"])
@login_required
@bp.errorhandler(CSRFError)
def update_email():
    form = UpdateEmailForm()

    if form.validate_on_submit():
        if form.validate_on_submit():
            send_email_verification(current_user, form.email.data)
            flash("Please check your email for a verification link", "success")

        # return redirect(url_for('settings.update_email'))

    return render_template("settings/settings_account_email.html", form=form)


# ################################## #
# ##     Update email verify      ## #
# ################################## #


@bp.route("/settings/verify_email/<token>/<email>", methods=["GET", "POST"])
def verify_email(token, email):
    user = User.verify_reset_password_token(token)
    if user:
        login_user(user, remember=True)

        if user.username == user.email:
            user.username = email.lower()
        user.email = email.lower()
        ev = Event.add("updated account email")
        if ev:
            db.session.add(ev)
        db.session.commit()
        flash("Your email has been updated!", "success")
        return redirect(url_for("settings.settings_account"))


# ############################ #
# ##     Delete Account     ## #
# ############################ #


@bp.route("/settings/account/delete", methods=["GET", "POST"])
@login_required
def delete_verify():
    if request.method == "POST":
        send_delete_verification(current_user)
        return json.dumps({"success": "true"}), 200

    return render_template("/settings/settings_delete_verify.html")


# ############################ #
# ##     Delete Confirm     ## #
# ############################ #
@bp.route("/settings/account/delete/<token>", methods=["GET"])
def delete_confirm(token):

    user = User.verify_delete_account_token(token)
    if user:
        login_user(user, remember=True)
        return redirect(url_for("settings.delete_final"))

    else:
        flash("Email verification unsuccessful. Try again", "error")
        # return redirect(url_for('settings.settings_account'))

    return render_template("/settings/settings_delete_verify.html")


# ########################## #
# ##     Delete Final     ## #
# ########################## #


@bp.route("/settings/account/delete/final", methods=["GET", "POST"])
@login_required
def delete_final():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        current_user.launch_task(
            "account_export",
            "exporting data...",
            current_user.id,
            form.export.data,
            delete=True,
        )
        db.session.commit()
        ev = Event.add("deleted account")
        if ev:
            db.session.add(ev)
            db.session.commit()
        logout_user()
        return redirect(url_for("auth.register"))

    return render_template("/settings/settings_delete_confirm.html", form=form)


# ############################# #
# ##     Content settings      ## #
# ############################# #


@bp.route("/settings/content", methods=["GET", "POST"])
@login_required
@bp.errorhandler(CSRFError)
def settings_content():
    approved_senders = Approved_Sender.query.filter_by(user_id=current_user.id).all()
    form = AddApprovedSenderForm()

    if form.validate_on_submit():
        email = form.email.data
        update_user_last_action("added approved sender")
        # print('adding approved sender:')
        # print(email)
        email = email.lower()
        # print(email)
        e = Approved_Sender(user_id=current_user.id, email=email)
        db.session.add(e)

        ev = Event.add("added approved sender")
        if ev:
            db.session.add(ev)

        db.session.commit()
        approved_senders = Approved_Sender.query.filter_by(
            user_id=current_user.id
        ).all()

        # return redirect(url_for('settings.settings_content'))

    # return render_template('settings.html',form=form, senders=approved_senders)
    return render_template(
        "settings/settings_content.html", form=form, senders=approved_senders
    )


# ########################## #
# ##     Enable email     ## #
# ########################## #


@bp.route("/enable-add-by-email", methods=["POST"])
@login_required
@bp.errorhandler(CSRFError)
def enable_add_by_email():
    current_user.set_lurnby_email()
    update_user_last_action("enabled add by email")
    e = Approved_Sender(user_id=current_user.id, email=current_user.email)
    db.session.add(e)
    ev = Event.add(EventName.ENABLED_ADD_BY_EMAIL)
    if ev:
        db.session.add(ev)

    db.session.commit()

    return "", 200


# ######################### #
# ##     Export Data     ## #
# ######################### #


@bp.route("/settings/content/export", methods=["POST"])
@login_required
def export():
    data = json.loads(request.data)
    current_user.launch_task(
        "account_export",
        "exporting data...",
        current_user.id,
        data["ext"],
        delete=False,
    )
    ev = Event.add("exported all data")
    if ev:
        db.session.add(ev)

    db.session.commit()

    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


# ############################ #
# ##     Notifications      ## #
# ############################ #


@bp.route("/settings/communication", methods=["GET", "POST"])
@login_required
def comms():

    form = CommunicationForm()
    comms = current_user.comms
    # print(comms)

    if form.validate_on_submit():
        comms.highlights = form.data["highlights"]
        comms.reminders = form.data["reminders"]
        comms.promotional = form.data["promotions"]
        comms.educational = form.data["educational"]
        comms.informational = form.data["informational"]

        ev = Event.add("updated comms")
        if ev:
            db.session.add(ev)
        db.session.commit()

        flash("Preferences updated", "success")

    return render_template(
        "settings/settings_communication.html", form=form, comms=comms
    )
