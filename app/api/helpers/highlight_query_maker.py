from app import db
from app.models import Article, Highlight, tags_highlights
from flask_sqlalchemy import query


def apply_all_filters(query, status, tag_status, tag_ids, search_phrase):
    query = filter_by_status(query, status)
    query = filter_by_tag_status(query, tag_status)
    query = filter_by_tags(query, tag_ids)
    query = filter_by_search_phrase(query, search_phrase)

    return query


def filter_by_status(query: query.Query, status: str):
    """
    Args:
        query (flask_sqlalchemy.query.Query): base query object
        status (string): status to filter by
    Returns:
        query (flask_sqlalchemy.query.Query): updated query object
    """

    if not status or status.lower() == "unarchived":
        query = query.filter_by(archived=False)
    elif status.lower() == "all":
        pass
    elif status.lower() == "archived":
        query = query.filter_by(archived=True)
    return query


def filter_by_tag_status(query: query.Query, tag_status: str):
    """
    Args:
        query (flask_sqlalchemy.query.Query): base query object
        tag_status (string): status to filter by: Tagged || Untagged
    Returns:
        query (flask_sqlalchemy.query.Query): updated query object
    """

    if not tag_status:
        pass
    elif tag_status.lower() == "tagged":
        query = query.filter_by(untagged=False)
    elif tag_status.lower() == "untagged":
        query = query.filter_by(untagged=True)
    return query


def filter_by_tags(query: query.Query, tag_ids: str):
    """
    Args:
        query (flask_sqlalchemy.query.Query): base query object
        tag_ids (string): string of comma separated tag ids e.g. '1,53,23'
    Returns:
        query (flask_sqlalchemy.query.Query): updated query object
    """
    if tag_ids is not None:
        tag_ids = [int(tag) for tag in tag_ids.split(",")]
        join_highlight_id = tags_highlights.c.highlight_id
        join_tag_id = tags_highlights.c.tag_id

        # join tags
        query = query.join(tags_highlights, (join_highlight_id == Highlight.id))
        # apply filter
        query = query.filter(join_tag_id.in_(tag_ids))
    return query


def filter_by_search_phrase(query: query.Query, search_phrase: str):
    """filters by user supplied search phrase

    Args:
        query (flask_sqlalchemy.query.Query): base query object
        search_phrase (str): e.g "I like bananas"
    Returns:
        query (flask_sqlalchemy.query.Query): updated query object
    """
    if search_phrase is not None:
        query = query.outerjoin(Article, Highlight.article_id == Article.id)
        query = query.filter(
            db.or_(
                Highlight.text.ilike(f"%{search_phrase}%"),
                Highlight.note.ilike(f"%{search_phrase}%"),
                Article.title.ilike(f"%{search_phrase}%"),
            )
        )
    return query


def apply_sorting(query: query.Query, created_sort: str):
    """_summary_

    Args:
        query (flask_sqlalchemy.query.Query): base query object
        created_sort (str): Sort by created_date - "asc" or "desc"
    Returns:
        query (flask_sqlalchemy.query.Query): updated query object
    """
    # then prepare to sort
    order = []

    if not created_sort or created_sort.lower() == "desc":
        col = getattr(Highlight, "created_date")
        col = col.desc()
        order.append(col)
    elif created_sort.lower() == "asc":
        col = getattr(Highlight, "created_date")
        col = col.asc()
        order.append(col)

    # apply the sorting
    query = query.order_by(*order)

    return query
