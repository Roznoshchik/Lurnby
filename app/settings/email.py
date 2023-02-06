from app.email import send_email

from flask import render_template, current_app


def send_email_verification(user, email):
    token = user.get_reset_password_token()
    print(f"sending email - [Lurnby] Verify your email for user: {user.id}")

    send_email(
        "Lurnby - Verify your email",
        sender=current_app.config["ADMINS"][0],
        recipients=[email],
        text_body=render_template(
            "settings/email/verify_email.txt", user=user, token=token, email=email
        ),
        html_body=render_template(
            "settings/email/verify_email.html", user=user, token=token, email=email
        ),
    )


def send_delete_verification(user):
    token = user.get_delete_account_token()
    print(f"sending email - [Lurnby] Confirm account deletion for user: {user.id}")
    send_email(
        "Lurnby - Confirm account deletion",
        sender=current_app.config["ADMINS"][0],
        recipients=[user.email],
        text_body=render_template(
            "settings/email/delete_verify.txt", user=user, token=token
        ),
        html_body=render_template(
            "settings/email/delete_verify.html", user=user, token=token
        ),
    )
