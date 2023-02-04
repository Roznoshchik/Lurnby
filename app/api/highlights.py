from flask import request, jsonify, url_for
import json
import traceback
from uuid import UUID

from app import db, CustomLogger
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request, LurnbyValueError, error_response

import app.api.helpers.highlight_query_maker as hqm
from app.api.helpers.add_highlight_methods import (
    validate_request,
    add_tags,
    populate_highlight,
)
from app.api.helpers.query_maker import apply_pagination
from app.api.helpers.update_tags import update_tags
from app.models import Article, Highlight, Event


logger = CustomLogger("API")


@bp.route("/highlights", methods=["GET"])
@token_auth.login_required
def get_highlights():
    """
    Query args
    ----------
    page : Which page to return from paginated response
        e.g. 1 || 2
    per_page : how many results to show per page default 15
        number e.g 15, 30, 50 || 'all'
    article_id: id of the article for which highlights should be returned
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
    """
    try:
        user = token_auth.current_user()

        page = request.args.get("page", "1")
        per_page = request.args.get("per_page", "15")
        article_id = request.args.get("article_id", None)
        search_phrase = request.args.get("q", None)
        created_sort = request.args.get("created_sort")
        status = request.args.get("status", None)
        tag_status = request.args.get("tag_status", None)
        tag_ids = request.args.get("tag_ids", None)

        # filter query
        article = (
            Article.query.filter_by(uuid=UUID(article_id)).first()
            if article_id
            else None
        )
        if article:
            query = Article.highlights
        else:
            query = user.highlights

        query = hqm.apply_all_filters(query, status, tag_status, tag_ids, search_phrase)
        query = hqm.apply_sorting(query, created_sort)
        query = apply_pagination(query, page, per_page)

        has_next = query.has_next if query.has_next else None
        highlights = [highlight.to_dict() for highlight in query.items]

        response = jsonify(has_next=has_next, highlights=highlights)
        response.status_code = 200
        return response
    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong.")


@bp.route("/highlights", methods=["POST"])
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
        highlight = add_tags(highlight, data.get("tags", []))

        ev = Event.add("added highlight", user=user)
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


@bp.route("/highlights/<uuid>", methods=["PATCH"])
@token_auth.login_required
def update_highlight(uuid):
    try:
        user = token_auth.current_user()
        highlight = Highlight.query.filter_by(uuid=uuid).first()
        data = json.loads(request.data)

        if not highlight or highlight.user_id != user.id:
            return error_response(404, "Resource not found")

        for key, value in data.items():
            if key in highlight.fields_that_can_be_updated:
                setattr(highlight, key, value)

        if "tags" in data:
            highlight = update_tags(tags=data["tags"], resource=highlight)

        ev = Event.add("updated highlight", user=user)
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


@bp.route("/highlights/export", methods=["GET"])
@token_auth.login_required
def export_highlights():
    try:
        user = token_auth.current_user()
        article_id = request.args.get("article_id", None)
        search_phrase = request.args.get("q", None)
        status = request.args.get("status", None)
        tag_status = request.args.get("tag_status", None)
        tag_ids = request.args.get("tag_ids", None)
        export_file_ext = request.args.get("export_file_ext", "csv")

        # filter query
        article = (
            Article.query.filter_by(uuid=UUID(article_id)).first()
            if article_id
            else None
        )
        if article:
            highlights = Article.highlights
        else:
            highlights = user.highlights

        highlights = hqm.apply_all_filters(
            highlights, status, tag_status, tag_ids, search_phrase
        )
        task = user.launch_task(
            "export_highlights", highlights, file_ext=export_file_ext
        )
        ev = Event.add("Exported highlights", user=user)
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
