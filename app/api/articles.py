import sqlalchemy as sa

from app import db, CustomLogger
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import LurnbyValueError

import app.api.helpers.article_query_maker as aqm
from app.api.helpers.query_maker import apply_pagination, get_total_count
from app.api.helpers.add_article_methods import (
    process_manual_entry,
    process_url_entry,
    add_tags,
    process_file,
    process_file_upload,
)
from app.models import Article, Event
from app.models.event import EventName
from app.api.errors import bad_request, error_response
from app.api.helpers.update_tags import update_tags

from flask import jsonify, request, url_for
import json
import traceback
from uuid import UUID


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
    status : article status = defaults to all unarchived
        e.g. read || unread || in_progress || archived
    tag_ids : comma separated list of tag ids
        e.g. 1,5,71
    q : search query. This is applied after filtering by status and tags.
        e.g. hello old friend

    Returns
    -------
    JSON with:
        recent: 3 most recently opened articles
        articles: paginated list of all articles
        has_next: boolean indicating if there's a next page
    """
    try:
        user = token_auth.current_user()

        page = request.args.get("page", "1")
        per_page = request.args.get("per_page", "15")
        status = request.args.get("status", None)
        search_phrase = request.args.get("q", None)
        tag_ids = request.args.get("tag_ids", None)

        # Get recent articles (3 most recently opened)
        recent_articles = aqm.get_recent_articles(user.id, limit=3)
        recent = [article.to_dict() for article in recent_articles]

        # Build main query with SQLAlchemy 2.0 select
        # Use .isnot(True) to include NULL processing values (old articles)
        stmt = sa.select(Article).where(
            Article.user_id == user.id,
            Article.processing.isnot(True),
        )
        stmt = aqm.filter_by_status(stmt, status)
        stmt = aqm.filter_by_tags(stmt, tag_ids)
        stmt = aqm.filter_by_search_phrase(stmt, search_phrase)

        # Get total count before sorting/pagination
        total = get_total_count(stmt)

        stmt = aqm.apply_default_sorting(stmt)

        # Apply pagination
        article_list, has_next = apply_pagination(stmt, page, per_page)
        articles = [article.to_dict() for article in article_list]

        response = jsonify(recent=recent, articles=articles, has_next=has_next, total=total)
        response.status_code = 200
        return response
    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(e)
            return bad_request("Something went wrong.")


""" ######################### """
""" ##     add article     ## """
""" ######################### """


@bp.route("/articles", methods=["POST"])
@token_auth.login_required
def add_article():
    file = request.files.get("file")
    if data := request.form.get("data", {}):
        data = json.loads(data)

    manual_entry = data.get("manual_entry", None)
    url = data.get("url", None)
    upload_file_ext = data.get("upload_file_ext", None)
    tags = data.get("tags", [])
    if not manual_entry and not url and not upload_file_ext and not file:
        return bad_request("No article to create. Check data and try again")

    article = Article(user_id=token_auth.current_user().id, notes=data.get("notes", ""))
    db.session.add(article)
    try:
        if manual_entry:
            article = process_manual_entry(article, manual_entry)

        if url:
            article = process_url_entry(article, url)

        article = add_tags(article=article, user_id=token_auth.current_user().id, tags=tags)

        article.processing = True
        db.session.commit()

        if file:
            response = process_file(article, file, token_auth.current_user())
            return response

        elif upload_file_ext:
            response = process_file_upload(article, upload_file_ext)
            return response

        article.processing = False
        token_auth.current_user().launch_task("set_images_lazy", aid=article.id)
        token_auth.current_user().launch_task("set_absolute_urls", aid=article.id)
        ev = Event.add(EventName.ADDED_ARTICLE, user=token_auth.current_user())
        db.session.add(ev)
        db.session.commit()

        response = jsonify(processing=False, article=article.to_dict())
        response.status_code = 201
        return response

    except Exception as e:
        if article.id:
            db.session.delete(article)
            db.session.commit()
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(e)
            return bad_request("Something went wrong.")


""" ######################### """
""" ##     get article     ## """
""" ######################### """


@bp.route("/articles/<article_uuid>", methods=["GET"])
@token_auth.login_required
def get_article(article_uuid):
    try:
        article = Article.query.filter_by(uuid=UUID(article_uuid)).first()

        if not article or article.user_id != token_auth.current_user().id:
            return bad_request("The resource can't be found")

        response = jsonify(article=article.to_dict(preview=False))
        response.status_code = 200
        return response

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(e)
            return bad_request("Something went wrong.")


""" ############################ """
""" ##     update article     ## """
""" ############################ """


@bp.route("/articles/<article_uuid>", methods=["PATCH"])
@token_auth.login_required
def update_article(article_uuid):
    try:
        article = Article.query.filter_by(uuid=UUID(article_uuid)).first()

        if not article or article.user_id != token_auth.current_user().id:
            return error_response(404, "The resource can't be found")

        data = json.loads(request.data)
        valid_fields = article.fields_that_can_be_updated

        for key, value in data.items():
            if key in valid_fields:
                setattr(article, key, value)

        if "tags" in data:
            article = update_tags(tags=data["tags"], resource=article)

        ev = Event.add(EventName.UPDATED_ARTICLE, user=token_auth.current_user())
        db.session.add(ev)
        db.session.commit()

        response = jsonify(article=article.to_dict(preview=False))
        response.status_code = 200
        return response

    except json.JSONDecodeError:
        return bad_request("Check data")
    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong.")


""" ############################ """
""" ##     delete article     ## """
""" ############################ """


@bp.route("/articles/<article_uuid>", methods=["DELETE"])
@token_auth.login_required
def delete_article(article_uuid):
    try:
        article = Article.query.filter_by(uuid=UUID(article_uuid)).first()

        if not article or article.user_id != token_auth.current_user().id:
            return bad_request("The resource can't be found")

        db.session.delete(article)
        ev = Event.add(EventName.DELETED_ARTICLE, user=token_auth.current_user())
        db.session.add(ev)
        db.session.commit()

        response = jsonify()
        response.status_code = 200
        return response

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(e)
            return bad_request("Something went wrong.")


""" ################################## """
""" ##     file is uploaded url     ## """
""" ################################## """


@bp.route("/articles/<article_uuid>/uploaded", methods=["GET"])
@token_auth.login_required
def file_uploaded(article_uuid):
    try:
        upload_file_ext = request.args.get("upload_file_ext", None)
        if upload_file_ext and "." not in upload_file_ext:
            upload_file_ext = f".{upload_file_ext}"
        if not upload_file_ext or (upload_file_ext != ".epub" and upload_file_ext != ".pdf"):
            return bad_request('upload_file_ext query arg should be ".epub" or ".pdf"')

        task = token_auth.current_user().launch_task(
            "bg_add_article",
            article_uuid=article_uuid,
            file_ext=upload_file_ext,
            file=None,
        )
        db.session.commit()

        article = Article.query.filter_by(uuid=UUID(article_uuid)).first()
        response = jsonify(
            processing=True,
            task_id=task.id,
            article=article.to_dict(),
            location=url_for("api.get_task_status", task_id=task.id),
        )
        response.status_code = 200
        return response

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(e)
            return bad_request("Something went wrong.")


""" ############################ """
""" ##     export article     ## """
""" ############################ """


@bp.route("/articles/<article_uuid>/export", methods=["GET"])
@token_auth.login_required
def export_article(article_uuid):
    try:
        export_file_ext = request.args.get("export_file_ext", "csv")
        article = Article.query.filter_by(uuid=UUID(article_uuid)).first()
        user = token_auth.current_user()

        if article.user_id != user.id:
            return bad_request("The resource can't be found")

        task = token_auth.current_user().launch_task("export_article", user=user, article=article, ext=export_file_ext)
        ev = Event.add(EventName.EXPORTED_ARTICLE, user=user)
        db.session.add(ev)
        db.session.commit()

        response = jsonify(
            processing=True,
            task_id=task.id,
            location=url_for("api.get_task_status", task_id=task.id),
        )

        return response

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(traceback.print_exc())
            return bad_request("Something went wrong.")
