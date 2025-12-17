from flask import jsonify, request
from app import db
from app.api import bp
from app.api.auth import basic_auth, token_auth
from app.api.errors import bad_request
from app.models import User


@bp.post("/auth/login")
@basic_auth.login_required
def login():
    """
    Login endpoint for web app and mobile apps.
    Expects Authorization: Basic <base64(username:password)> header.
    Returns access token (short-lived) and refresh token (long-lived).
    Also sets refresh token as HttpOnly cookie for web browsers.
    """
    user = basic_auth.current_user()

    access_token = user.get_access_token()
    refresh_token = user.get_refresh_token()
    db.session.commit()

    response = jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict()
    })

    # Set HttpOnly cookie for web browsers
    response.set_cookie(
        "refresh_token",
        refresh_token,
        max_age=2592000,  # 30 days
        httponly=True,
        secure=True,
        samesite="Lax"
    )

    return response


@bp.post("/auth/google")
def google_login():
    """
    Google OAuth login endpoint for web app and mobile apps.
    Expects JSON: {goog_id, email, first_name}.
    Returns access token (short-lived) and refresh token (long-lived).
    Also sets refresh token as HttpOnly cookie for web browsers.
    """
    data = request.get_json() or {}
    if "goog_id" not in data or "email" not in data or "first_name" not in data:
        return bad_request("must include goog_id, email, and first_name fields")

    user = User.query.filter_by(email=data["email"]).first()
    created = False
    if not user:
        user = User(
            goog_id=data["goog_id"],
            email=data["email"],
            firstname=data["first_name"]
        )
        db.session.add(user)
        db.session.commit()  # Comms created automatically via after_insert event
        created = True

    access_token = user.get_access_token()
    refresh_token = user.get_refresh_token()
    db.session.commit()

    response = jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict()
    })

    # Set HttpOnly cookie for web browsers
    response.set_cookie(
        "refresh_token",
        refresh_token,
        max_age=2592000,  # 30 days
        httponly=True,
        secure=True,
        samesite="Lax"
    )

    if created:
        response.status_code = 201

    return response


@bp.post("/auth/refresh")
def refresh():
    """
    Refresh endpoint for web app and mobile apps.
    Accepts refresh token from cookie (web) or request body (mobile).
    Returns new access token.
    """
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        data = request.get_json() or {}
        refresh_token = data.get("refresh_token")

    if not refresh_token:
        return bad_request("refresh token required")

    user = User.check_refresh_token(refresh_token)
    if not user:
        return bad_request("invalid or expired refresh token")

    access_token = user.get_access_token()
    db.session.commit()

    return jsonify({
        "access_token": access_token,
        "user": user.to_dict()
    })


@bp.post("/auth/logout")
@token_auth.login_required
def logout():
    """
    Logout endpoint for web app and mobile apps.
    Revokes refresh token and clears cookie (if present).
    """
    user = token_auth.current_user()
    user.revoke_refresh_token()
    db.session.commit()

    response = jsonify({"message": "logged out"})

    # Clear cookie for web browsers
    response.set_cookie(
        "refresh_token",
        "",
        max_age=0,
        httponly=True,
        secure=True,
        samesite="Lax"
    )

    return response
