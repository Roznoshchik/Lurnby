from flask import flash, render_template, request

from flask_login import current_user

import json
from app.content import bp
from app import db
from app.models import Event


@bp.route("/terms-of-service", methods=["GET"])
def terms():
    return render_template("legal/tos.html")


@bp.route("/privacy-policy", methods=["GET"])
def privacy():
    return render_template("legal/privacy.html")


@bp.route("/intellectual-property-policy", methods=["GET"])
def ipp():
    return render_template("legal/ipp.html")


@bp.route("/legal/accept_terms", methods=["GET", "POST"])
def accept_terms():

    if request.method == "POST":
        data = json.loads(request.data)
        action = data["action"]

        if action == "accept_terms":
            current_user.tos = True
            flash(
                "Thank you for accepting the terms and continuing to use Lurnby",
                "success",
            )
            ev = Event.add("tos accepted")
            if ev:
                db.session.add(ev)
            db.session.commit()

            return json.dumps({"accepted": True})

        else:
            flash(
                "Please accept our updated terms to continue using Lurnby or delete your account below",
                "error",
            )

    return json.dumps({"html": render_template("legal/accept_tos_modal.html")}), 200
