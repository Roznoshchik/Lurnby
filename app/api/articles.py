from app import db, CustomLogger
from app.api import bp
from app.api.auth import token_auth
from app.api.helpers.article_query_maker import (
    filter_by_status,
    filter_by_tags,
    filter_by_search_phrase,
    apply_sorting,
    apply_pagination,
)
from app.api.helpers.add_article_methods import (
    process_manual_entry,
    process_url_entry,
    add_to_tags,
    process_file,
    process_file_upload,
)
from app.models import Article
from app.api.errors import bad_request

from flask import jsonify, request
import json


logger = CustomLogger("API")


""" ########################## """
""" ##     Get articles     ## """
""" ########################## """


@bp.route("/articles", methods=["GET"])
@token_auth.login_required
def get_articles():
    """
    Query args
    ----------
    page : Which page to return from paginated response
        e.g. 1 || 2
    per_page : how many results to show per page default 15
        number e.g 15, 30, 50 || 'all'
    title_sort : optional sorting for the article title
        asc || desc
    opened_sort : optional sorting by last opened date
        asc || desc
    status : article status = defaults to all unarchived
        e.g. read || unread || in_progress || archived
    tag_ids : comma separated list of tag ids
        e.g. 1,5,71
    q : search query. This is applied after filtering by status and tags.
        e.g. hello old friend
    """
    user = token_auth.current_user()

    page = request.args.get("page", "1")
    per_page = request.args.get("per_page", "15")
    title_sort = request.args.get("title_sort", None)
    opened_sort = request.args.get("opened_sort", None)
    status = request.args.get("status", None)
    search_phrase = request.args.get("q", None)
    tag_ids = request.args.get("tag_ids", None)

    # filter query
    query = user.articles.filter_by(processing=False)
    query = filter_by_status(query, status)
    query = filter_by_tags(query, tag_ids)
    query = filter_by_search_phrase(query, search_phrase)
    query = apply_sorting(query, title_sort, opened_sort)
    query = apply_pagination(query, page, per_page)

    has_next = query.has_next if query.has_next else None
    articles = [article.to_dict() for article in query.items]

    response = jsonify(has_next=has_next, articles=articles)
    response.status_code = 200
    return response


""" ######################### """
""" ##     add article     ## """
""" ######################### """


@bp.route("/articles", methods=["POST"])
@token_auth.login_required
def add_article():
    file = request.files.get("file")
    data = json.loads(request.form.get("data"))
    manual_entry = data.get("manual_entry", None)
    url = data.get("url", None)
    file_ext = data.get("file_ext", None)
    tags = data.get("tags", [])

    if not manual_entry and not url and not file_ext and not file:
        return bad_request("No article to create. Check data and try again")

    article = Article(user_id=token_auth.current_user().id, notes=data.get("notes", ""))

    db.session.add(article)

    try:
        if manual_entry:
            article = process_manual_entry(article, manual_entry)

        if url:
            article = process_url_entry(article, url)

        article = add_to_tags(
            article=article, user_id=token_auth.current_user().id, tags=tags
        )

        article.processing = True
        db.session.commit()

        if file:
            response = process_file(article, file, token_auth.current_user())
            return response

        elif file_ext:
            response = process_file_upload(article, file_ext)
            return response

        article.processing = False
        token_auth.current_user().launch_task("set_images_lazy", aid=article.id)
        token_auth.current_user().launch_task("set_absolute_urls", aid=article.id)
        db.session.commit()

        response = jsonify(processing=False, article_id=article.id)
        response.status_code = 201
        return response

    except Exception as e:
        if article.id:
            db.session.delete(article)
            db.session.commit()
        if hasattr(e, "msg"):
            return bad_request(e.msg)
        else:
            logger.error(e)
            return bad_request("Something went wrong.")


""" ################################## """
""" ##     file is uploaded url     ## """
""" ################################## """


@bp.route("/articles/<int:article_id>/uploaded", methods=["GET"])
@token_auth.login_required
def file_uploaded(article_id):
    file_ext = request.args.get("file_ext", None)

    if not file_ext or file_ext != ".epub" or file_ext != ".pdf":
        return bad_request('file_ext query arg should be ".epub" or ".pdf"')

    task = token_auth.current_user().launch_task(
        "bg_add_article", article_id=article_id, file_ext=file_ext, file=None
    )
    response = jsonify(processing=True, task_id=task.id, article_id=article_id)
    response.status_code = 200
    return response
