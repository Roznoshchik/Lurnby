import sqlalchemy as sa
from flask import request, jsonify
import json
import traceback

from app import db, CustomLogger
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request, LurnbyValueError, error_response
from app.api.helpers.query_maker import apply_pagination
from app.models import Event, Tag
from app.models.event import EventName


logger = CustomLogger("API")


@bp.route("/tags", methods=["GET"])
@token_auth.login_required
def get_tags():
    try:
        page = request.args.get("page", "1")
        per_page = request.args.get("per_page", "150")
        status = request.args.get("status", "unarchived")  # all / archived / unarchived

        user = token_auth.current_user()

        # Build query with SQLAlchemy 2.0 select
        stmt = sa.select(Tag).where(Tag.user_id == user.id)

        if status.lower() == "archived":
            stmt = stmt.where(Tag.archived.is_(True))
        elif status.lower() != "all":
            stmt = stmt.where(Tag.archived.is_(False))

        stmt = stmt.order_by(Tag.name.asc())

        tag_list, has_next = apply_pagination(stmt, page, per_page)
        tags = [tag.to_dict() for tag in tag_list]

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

        ev = Event.add(EventName.ADDED_TAG, user=user)
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

        ev = Event.add(EventName.UPDATED_TAG, user=user)
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
        ev = Event.add(EventName.DELETED_TAG, user=user)
        db.session.add(ev)

        db.session.commit()

        return jsonify()

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong")
