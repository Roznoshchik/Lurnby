import sqlalchemy as sa
from flask import request, jsonify
import json
import traceback

from app import db, CustomLogger
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request, LurnbyValueError, error_response
from app.api.helpers.query_maker import apply_pagination, get_total_count
from app.models import Event, Tag
from app.models.associations import tags_highlights, tags_articles
from app.models.event import EventName


logger = CustomLogger("API")


@bp.route("/tags", methods=["GET"])
@token_auth.login_required
def get_tags():
    try:
        page = request.args.get("page", "1")
        per_page = request.args.get("per_page", "150")
        status = request.args.get("status", "unarchived")  # all / archived / unarchived
        search = request.args.get("q", "").strip()

        user = token_auth.current_user()

        # Build query with computed counts
        stmt = (
            sa.select(
                Tag,
                sa.func.count(sa.distinct(tags_highlights.c.highlight_id)).label("h_count"),
                sa.func.count(sa.distinct(tags_articles.c.article_id)).label("a_count"),
            )
            .outerjoin(tags_highlights, tags_highlights.c.tag_id == Tag.id)
            .outerjoin(tags_articles, tags_articles.c.tag_id == Tag.id)
            .where(Tag.user_id == user.id)
            .group_by(Tag.id)
        )

        if status.lower() == "archived":
            stmt = stmt.where(Tag.archived.is_(True))
        elif status.lower() != "all":
            stmt = stmt.where(Tag.archived.is_(False))

        if search:
            stmt = stmt.where(Tag.name.ilike(f"%{search}%"))

        stmt = stmt.order_by(Tag.name.asc())

        # Get total count before pagination
        count_stmt = sa.select(Tag).where(Tag.user_id == user.id)
        if status.lower() == "archived":
            count_stmt = count_stmt.where(Tag.archived.is_(True))
        elif status.lower() != "all":
            count_stmt = count_stmt.where(Tag.archived.is_(False))
        if search:
            count_stmt = count_stmt.where(Tag.name.ilike(f"%{search}%"))
        total = get_total_count(count_stmt)

        rows, has_next = apply_pagination(
            stmt,
            page=page,
            per_page=per_page,
            scalars=False,
        )

        tags = []
        for tag, h_count, a_count in rows:
            tag_dict = tag.to_dict()
            tag_dict["highlight_count"] = h_count
            tag_dict["article_count"] = a_count
            tags.append(tag_dict)

        return jsonify(tags=tags, has_next=has_next, total=total)

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong.")


@bp.route("/tags", methods=["POST"])
@token_auth.login_required
def create_tag():
    try:
        user = token_auth.current_user()
        data = json.loads(request.data) if request.data else None
        if not data or not data.get("name"):
            raise LurnbyValueError("Missing data in payload")

        name = data.get("name").strip()

        # Check if a tag with this name already exists
        existing_tag = Tag.query.filter(
            Tag.user_id == user.id,
            sa.func.lower(Tag.name) == name.lower(),
        ).first()

        if existing_tag:
            if existing_tag.archived:
                # Unarchive the existing tag
                existing_tag.archived = False
                ev = Event.add(EventName.UPDATED_TAG, user=user)
                db.session.add(ev)
                db.session.commit()
                return jsonify(tag=existing_tag.to_dict()), 200
            else:
                raise LurnbyValueError("A tag with this name already exists")

        tag = Tag(user_id=user.id, name=name)
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
