from flask import request, jsonify
import json
import traceback
from uuid import UUID

from app import db, CustomLogger
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request, LurnbyValueError

import app.api.helpers.highlight_query_maker as hqm
from app.api.helpers.add_highlight_methods import verify_non_existing_highlight
from app.api.helpers.query_maker import apply_pagination
from app.models import Article, Highlight


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

        query = hqm.filter_by_status(query, status)
        query = hqm.filter_by_status(query, status)
        query = hqm.filter_by_tag_status(query, tag_status)
        query = hqm.filter_by_tags(query, tag_ids)
        query = hqm.filter_by_search_phrase(query, search_phrase)
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


@token_auth.login_required
@bp.route("/highlights", methods=["POST"])
def create_highlight():
    try:
        user = token_auth.current_user()
        data = json.loads(request.data) if request.data else None
        if not data:
            raise LurnbyValueError("Missing data in payload")

        verify_non_existing_highlight(data)

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong")
