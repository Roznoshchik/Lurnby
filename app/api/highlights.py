import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from flask import request, jsonify, url_for
import json
import traceback

from app import db, CustomLogger
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request, LurnbyValueError, error_response

import app.api.helpers.highlight_query_maker as hqm
from app.api.helpers.add_highlight_methods import (
    validate_request,
    populate_highlight,
)
from app.api.helpers.query_maker import apply_pagination, get_total_count
from app.api.helpers.update_tags import update_tags
from app.models import Highlight, Event, Tag
from app.models.event import EventName


logger = CustomLogger("API")


@bp.get("/highlights")
@token_auth.login_required
def get_highlights():
    """
    Query args
    ----------
    page : Which page to return from paginated response
        e.g. 1 || 2
    per_page : how many results to show per page default 15
        number e.g 15, 30, 50 || 'all'
    created_sort : optional sorting by created date
        asc || desc
    status : unarchived (default) || archived || all
       if not passed, defaults to unarchived
    tag_ids : comma separated list of tag ids
        e.g. 1,5,71
    tag_status: Tagged || Untagged || all (default)
        defaults to all
    q : search query. This is applied after filtering by status and tags.
        e.g. hello old friend

    Returns
    -------
    JSON with:
        highlights: paginated list of highlights
        has_next: boolean indicating if there's a next page
        total: total highlights in the current query
    """
    try:
        user = token_auth.current_user()

        page = request.args.get("page", "1")
        per_page = request.args.get("per_page", "15")
        search_phrase = request.args.get("q", None)
        created_sort = request.args.get("created_sort")
        status = request.args.get("status", None)
        tag_status = request.args.get("tag_status", None)
        tag_ids = request.args.get("tag_ids", None)

        # Build query with SQLAlchemy 2.0 select
        # Eager load non-archived tags to avoid N+1 queries
        stmt = (
            sa.select(Highlight)
            .where(Highlight.user_id == user.id)
            .options(selectinload(Highlight.tags.and_(Tag.archived.is_(False))))
        )

        # Apply filters
        stmt = hqm.filter_by_status(stmt, status)
        stmt = hqm.filter_by_tag_status(stmt, tag_status)
        stmt = hqm.filter_by_tags(stmt, tag_ids)
        stmt = hqm.filter_by_search_phrase(stmt, search_phrase)

        # Get total count before sorting/pagination
        total = get_total_count(stmt)

        # Apply sorting
        stmt = hqm.apply_default_sorting(stmt, created_sort)

        # Apply pagination
        highlight_list, has_next = apply_pagination(stmt, page, per_page)
        highlights = [highlight.to_dict() for highlight in highlight_list]

        response = jsonify(has_next=has_next, highlights=highlights, total=total)
        response.status_code = 200
        return response
    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong.")


@bp.post("/highlights")
@token_auth.login_required
def create_highlight():
    try:
        user = token_auth.current_user()
        data = json.loads(request.data) if request.data else None
        if not data:
            raise LurnbyValueError("Missing data in payload")

        validate_request(data)
        highlight = Highlight(user_id=user.id)
        db.session.add(highlight)

        highlight = populate_highlight(highlight, data)
        update_tags(
            highlight,
            tag_ids=data.get("tag_ids", []),
            new_tag_names=data.get("new_tag_names", []),
        )

        ev = Event.add(EventName.ADDED_HIGHLIGHT, user=user)
        db.session.add(ev)
        db.session.commit()

        response = jsonify(highlight=highlight.to_dict())
        response.status_code = 201
        return response

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong")


@bp.get("/highlights/<uuid>")
@token_auth.login_required
def get_highlight(uuid):
    try:
        user = token_auth.current_user()
        highlight = db.session.scalars(db.select(Highlight).where(Highlight.uuid == uuid)).first()
        if not highlight or highlight.user_id != user.id:
            return error_response(404, "Resource not found")

        return jsonify(highlight=highlight.to_dict())

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong")


@bp.patch("/highlights/<uuid>")
@token_auth.login_required
def update_highlight(uuid):
    try:
        user = token_auth.current_user()
        highlight = db.session.scalars(db.select(Highlight).where(Highlight.uuid == uuid)).first()
        data = json.loads(request.data)

        if not highlight or highlight.user_id != user.id:
            return error_response(404, "Resource not found")

        for key, value in data.items():
            if key in highlight.fields_that_can_be_updated:
                setattr(highlight, key, value)

        if "tags" in data:
            highlight = update_tags(tag_ids=data["tags"], resource=highlight)

        ev = Event.add(EventName.UPDATED_HIGHLIGHT, user=user)
        db.session.add(ev)
        db.session.commit()

        return jsonify(highlight=highlight.to_dict())

    except json.JSONDecodeError:
        return bad_request("Check data")

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong")


@bp.delete("/highlights/<uuid>")
@token_auth.login_required
def delete_highlight(uuid):
    try:
        user = token_auth.current_user()
        highlight = db.session.scalars(db.select(Highlight).where(Highlight.uuid == uuid)).first()
        if not highlight or highlight.user_id != user.id:
            return error_response(404, "Resource not found")

        highlight.archived = True

        ev = Event.add(EventName.DELETED_HIGHLIGHT, user=user)
        db.session.add(ev)

        db.session.commit()

        return jsonify()

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong")


@bp.route("/highlights/review", methods=["GET"])
@token_auth.login_required
def get_highlights_for_review():
    """
    Query args
    ----------
    per_tier : how many highlights to show per tier, defaults to user review_count field
        number e.g 15, 30, 50
    tag_ids : comma separated list of tag ids for filtering
        e.g. 1,5,71
    """
    try:
        user = token_auth.current_user()

        per_tier = int(request.args.get("per_tier", user.review_count))
        tag_ids = request.args.get("tag_ids")
        if tag_ids:
            tag_ids = [int(tag_id) for tag_id in tag_ids.split(",")]

        response = jsonify(highlights=user.get_highlights_for_review(tag_ids, per_tier))
        response.status_code = 200
        return response
    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        elif isinstance(e, ValueError) and "invalid literal for int()" in str(e):
            return bad_request("Invalid data in params")
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong.")


@bp.route("/highlights/export", methods=["GET"])
@token_auth.login_required
def export_highlights():
    try:
        user = token_auth.current_user()
        search_phrase = request.args.get("q", None)
        status = request.args.get("status", None)
        tag_status = request.args.get("tag_status", None)
        tag_ids = request.args.get("tag_ids", None)
        export_file_ext = request.args.get("export_file_ext", "csv")

        # Build query
        stmt = sa.select(Highlight).where(Highlight.user_id == user.id)
        stmt = hqm.filter_by_status(stmt, status)
        stmt = hqm.filter_by_tag_status(stmt, tag_status)
        stmt = hqm.filter_by_tags(stmt, tag_ids)
        stmt = hqm.filter_by_search_phrase(stmt, search_phrase)

        highlights = list(db.session.scalars(stmt))
        task = user.launch_task("export_highlights", highlights=highlights, ext=export_file_ext)
        ev = Event.add(EventName.EXPORTED_HIGHLIGHTS, user=user)
        db.session.add(ev)
        db.session.commit()

        return jsonify(
            task_id=task.id,
            processing=True,
            location=url_for("api.get_task_status", task_id=task.id),
        )

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong")
