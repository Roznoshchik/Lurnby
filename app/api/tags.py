from flask import request, jsonify
import json
import traceback

from app import db, CustomLogger
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request, LurnbyValueError, error_response
from app.api.helpers.query_maker import apply_pagination
from app.models import Event, Tag


logger = CustomLogger("API")


@bp.route("/tags", methods=["GET"])
@token_auth.login_required
def get_tags():
    try:
        page = request.args.get("page", "1")
        per_page = request.args.get("per_page", "150")
        status = request.args.get("status", "unarchived")  # all / archived / unarchived

        user = token_auth.current_user()
        query = user.tags

        if status.lower() == "all":
            pass
        elif status.lower() == "archived":
            query = query.filter_by(archived=True)
        else:
            query = query.filter_by(archived=False)

        query = apply_pagination(query, page, per_page)
        has_next = query.has_next if query.has_next else None
        tags = [tag.to_dict() for tag in query.items]

        return jsonify(tags=tags, has_next=has_next)

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong.")


@bp.route("/tags", methods=["POST"])
@token_auth.login_required
def tag():
    try:
        user = token_auth.current_user()
        data = json.loads(request.data) if request.data else None
        if not data or not data.get("name"):
            raise LurnbyValueError("Missing data in payload")

        tag = Tag(user_id=user.id, name=data.get("name"))
        if uuid := data.get("uuid"):
            tag.uuid = uuid
        db.session.add(tag)

        ev = Event.add("added tag", user=user)
        db.session.add(ev)
        db.session.commit()

        response = jsonify(tag=tag.to_dict())
        response.status_code = 201
        return response

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong")


@bp.route("/tags/<uuid>", methods=["GET"])
@token_auth.login_required
def get_tag(uuid):
    try:
        user = token_auth.current_user()
        tag = Tag.query.filter_by(uuid=uuid).first()
        if not tag or tag.user_id != user.id:
            return error_response(404, "Resource not found")

        return jsonify(tag=tag.to_dict())

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong")


@bp.route("/tags/<uuid>", methods=["PATCH"])
@token_auth.login_required
def update_tag(uuid):
    try:
        user = token_auth.current_user()
        tag = Tag.query.filter_by(uuid=uuid).first()
        data = json.loads(request.data)

        if not tag or tag.user_id != user.id:
            return error_response(404, "Resource not found")

        for key, value in data.items():
            if key in tag.fields_that_can_be_updated:
                setattr(tag, key, value)

        ev = Event.add("updated tag", user=user)
        db.session.add(ev)
        db.session.commit()

        return jsonify(tag=tag.to_dict())

    except json.JSONDecodeError:
        return bad_request("Check data")

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong")


@bp.route("/tags/<uuid>", methods=["DELETE"])
@token_auth.login_required
def delete_tag(uuid):
    try:
        user = token_auth.current_user()
        tag = Tag.query.filter_by(uuid=uuid).first()
        if not tag or tag.user_id != user.id:
            return error_response(404, "Resource not found")

        db.session.delete(tag)
        ev = Event.add("deleted tag", user=user)
        db.session.add(ev)

        db.session.commit()

        return jsonify()

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong")
