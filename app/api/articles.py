from http import HTTPStatus
import json
import traceback
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import selectinload
from flask import jsonify, request, url_for

from app import db, CustomLogger
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import LurnbyValueError, bad_request, error_response
from app.api.helpers.query_maker import apply_pagination, get_total_count
from app.api.helpers.update_tags import update_tags
from app.api.helpers.add_article_methods import (
    process_manual_entry,
    process_url_entry,
    process_file_upload,
)
import app.api.helpers.article_query_maker as aqm
from app.models import Article, ArticleChunk, Event, Highlight, Tag
from app.models.event import EventName


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
        total: total articles in the current query
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
        # Eager load tags and highlights to avoid N+1 queries
        stmt = (
            sa.select(Article)
            .where(
                Article.user_id == user.id,
                Article.processing.isnot(True),
            )
            .options(
                selectinload(Article.tags.and_(Tag.archived.is_(False))),
                selectinload(Article.highlights),
            )
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
    data = request.json or {}

    manual_entry = data.get("manual_entry", None)
    url = data.get("url", None)
    upload_file_ext = data.get("upload_file_ext", None)
    filename = data.get("filename", None)
    tag_ids = data.get("tag_ids", [])
    new_tag_names = data.get("new_tag_names", [])
    if not manual_entry and not url and not upload_file_ext:
        return bad_request("No article to create. Check data and try again")

    # Use filename as temporary title for file uploads (will be replaced after processing)
    initial_title = filename if filename else None
    article = Article(
        user_id=token_auth.current_user().id,
        notes=data.get("notes", ""),
        title=initial_title,
    )
    db.session.add(article)
    try:
        if manual_entry:
            article = process_manual_entry(article, manual_entry)

        if url:
            article = process_url_entry(article, url)

        update_tags(article, tag_ids=tag_ids, new_tag_names=new_tag_names)

        article.processing = True
        db.session.commit()

        if upload_file_ext:
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

        with_content = request.args.get("with_content", "").lower() == "true"
        if with_content:
            article._ensure_chunks_built()
        response = jsonify(article=article.to_dict(preview=False, with_content=with_content))
        response.status_code = 200
        return response

    except Exception as e:
        if isinstance(e, LurnbyValueError):
            return bad_request(str(e))
        else:
            logger.error(e)
            return bad_request("Something went wrong.")


""" ############################ """
""" ##     get article chunk  ## """
""" ############################ """


@bp.route("/articles/<article_uuid>/chunks/<int:chunk_idx>", methods=["GET"])
@token_auth.login_required
def get_article_chunk(article_uuid, chunk_idx):
    """Get a specific chunk of an article by index."""
    try:
        stmt = sa.select(Article).where(Article.uuid == UUID(article_uuid))
        article = db.session.scalar(stmt)

        if not article or article.user_id != token_auth.current_user().id:
            return bad_request("The resource can't be found")

        # Build chunks lazily on first access
        article._ensure_chunks_built()

        chunk_stmt = sa.select(ArticleChunk).where(
            ArticleChunk.article_id == article.id,
            ArticleChunk.idx == chunk_idx,
        )
        chunk = db.session.scalar(chunk_stmt)

        if not chunk:
            return error_response(404, f"Chunk {chunk_idx} not found")

        # TODO: Filter highlights by chunk position once model is updated
        highlights = [h.to_dict() for h in article.highlights if not h.archived]

        response = jsonify(
            chunk=chunk.to_dict(),
            highlights=highlights,
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
""" ##     process article    ## """
""" ############################ """


@bp.route("/articles/<article_uuid>/process", methods=["POST"])
@token_auth.login_required
def process_article(article_uuid):
    """
    Build chunks for an unprocessed article and return initial chunks.

    Query params:
        highlight: UUID of highlight to navigate to (optional)

    Returns smart chunk loading based on position:
        - 20-80% within chunk: return just that chunk
        - <20%: return prev + current chunk
        - >80%: return current + next chunk
        - If highlight spans chunks: return both chunks
    """
    try:
        stmt = sa.select(Article).where(Article.uuid == UUID(article_uuid))
        article = db.session.scalar(stmt)

        if not article or article.user_id != token_auth.current_user().id:
            return error_response(HTTPStatus.NOT_FOUND, "Article not found")

        # Build chunks, migrate bookmarks, reanchor highlights
        article._ensure_chunks_built()

        chunk_count = len(article.chunks)
        if chunk_count == 0:
            return error_response(HTTPStatus.INTERNAL_SERVER_ERROR, "Failed to build chunks")

        # Determine starting position
        target_chunk_idx = 0
        offset_within_chunk = 0
        highlight_data = None
        unanchorable = False

        highlight_uuid = request.args.get("highlight")
        if highlight_uuid:
            # Navigate to specific highlight
            stmt = sa.select(Highlight).where(
                Highlight.uuid == UUID(highlight_uuid),
                Highlight.article_id == article.id,
            )
            highlight = db.session.scalar(stmt)
            if highlight:
                highlight_data = highlight.to_dict()
                if highlight.start_chunk is not None:
                    target_chunk_idx = highlight.start_chunk
                    offset_within_chunk = highlight.start or 0
                else:
                    # Highlight couldn't be anchored to chunks
                    unanchorable = True
        else:
            # No highlight - use furthest bookmark if available
            if article.bookmarks and isinstance(article.bookmarks, list):
                furthest = next((b for b in article.bookmarks if b.get("name") == "furthest"), None)
                if furthest and furthest.get("chunk") is not None:
                    target_chunk_idx = furthest["chunk"]
                    offset_within_chunk = furthest.get("offset", 0)
                    print(f"[ProcessArticle] Using furthest bookmark: chunk={target_chunk_idx}, offset={offset_within_chunk}")

        # Get target chunk to calculate position percentage
        target_chunk = article.chunks[target_chunk_idx] if target_chunk_idx < chunk_count else article.chunks[0]
        chunk_text_length = target_chunk.text_length or 1
        position_pct = (offset_within_chunk / chunk_text_length) * 100

        # Determine which chunks to return
        chunk_indices = []
        if highlight_data and not unanchorable:
            # If highlight spans multiple chunks, include both
            start_chunk = highlight_data.get("start_chunk", target_chunk_idx)
            end_chunk = highlight_data.get("end_chunk", start_chunk)
            if end_chunk is not None and end_chunk != start_chunk:
                chunk_indices = list(range(start_chunk, end_chunk + 1))
            elif position_pct < 20 and target_chunk_idx > 0:
                chunk_indices = [target_chunk_idx - 1, target_chunk_idx]
            elif position_pct > 80 and target_chunk_idx < chunk_count - 1:
                chunk_indices = [target_chunk_idx, target_chunk_idx + 1]
            else:
                chunk_indices = [target_chunk_idx]
        elif position_pct < 20 and target_chunk_idx > 0:
            chunk_indices = [target_chunk_idx - 1, target_chunk_idx]
        elif position_pct > 80 and target_chunk_idx < chunk_count - 1:
            chunk_indices = [target_chunk_idx, target_chunk_idx + 1]
        else:
            chunk_indices = [target_chunk_idx]

        # Fetch the chunks
        chunks_stmt = (
            sa.select(ArticleChunk)
            .where(
                ArticleChunk.article_id == article.id,
                ArticleChunk.idx.in_(chunk_indices),
            )
            .order_by(ArticleChunk.idx)
        )
        chunks = db.session.scalars(chunks_stmt).all()

        # Get highlights for these chunks
        highlight_stmt = sa.select(Highlight).where(
            Highlight.article_id == article.id,
            Highlight.archived.is_(False),
            sa.or_(
                Highlight.start_chunk.in_(chunk_indices),
                Highlight.end_chunk.in_(chunk_indices),
            ),
        )
        highlights = [h.to_dict() for h in db.session.scalars(highlight_stmt)]

        response = jsonify(
            article=article.to_dict(preview=False),
            chunks=[c.to_dict() for c in chunks],
            chunk_indices=chunk_indices,
            position={
                "chunk": target_chunk_idx,
                "offset": offset_within_chunk,
            },
            highlight=highlight_data,
            unanchorable=unanchorable,
            highlights=highlights,
        )
        response.status_code = HTTPStatus.OK
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
            article = update_tags(tag_ids=data["tags"], resource=article)

        if "content" in data:
            article.build_chunks()

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
