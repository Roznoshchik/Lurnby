import sqlalchemy as sa

from app import db
from app.models import Article, tags_articles


def filter_by_status(stmt: sa.Select, status: str) -> sa.Select:
    """Filter articles by status.

    Args:
        stmt: SQLAlchemy select statement
        status: status to filter by (archived, unread, in_progress, read)
    Returns:
        Modified select statement
    """
    if not status:
        stmt = stmt.where(Article.archived == False)
    elif status.lower() == "archived":
        stmt = stmt.where(Article.archived == True)
    elif status.lower() == "unread":
        stmt = stmt.where(
            Article.unread == True,
            Article.done == False,
            Article.archived == False,
        )
    elif status.lower() == "in_progress":
        stmt = stmt.where(
            Article.unread == False,
            Article.done == False,
            Article.archived == False,
        )
    elif status.lower() == "read":
        stmt = stmt.where(
            Article.unread == False,
            Article.done == True,
            Article.archived == False,
        )

    return stmt


def filter_by_tags(stmt: sa.Select, tag_ids: str) -> sa.Select:
    """Filter articles by tag IDs (OR logic - articles with any of the tags).

    Uses EXISTS subquery to avoid duplicates when an article has multiple
    matching tags, which is more compatible with ORDER BY than DISTINCT.

    Args:
        stmt: SQLAlchemy select statement
        tag_ids: comma-separated tag IDs e.g. '1,53,23'
    Returns:
        Modified select statement
    """
    if tag_ids is not None:
        tag_id_list = [int(tag) for tag in tag_ids.split(",")]
        # Use EXISTS subquery to avoid DISTINCT/ORDER BY conflict
        tag_subq = (
            sa.select(tags_articles.c.article_id)
            .where(
                tags_articles.c.article_id == Article.id,
                tags_articles.c.tag_id.in_(tag_id_list),
            )
            .exists()
        )
        stmt = stmt.where(tag_subq)

    return stmt


def filter_by_search_phrase(stmt: sa.Select, search_phrase: str) -> sa.Select:
    """Filter articles by search phrase (searches title, source, source_url, notes).

    Args:
        stmt: SQLAlchemy select statement
        search_phrase: e.g "I like bananas"
    Returns:
        Modified select statement
    """
    if search_phrase is not None:
        stmt = stmt.where(
            sa.or_(
                Article.title.ilike(f"%{search_phrase}%"),
                Article.source_url.ilike(f"%{search_phrase}%"),
                Article.source.ilike(f"%{search_phrase}%"),
                Article.notes.ilike(f"%{search_phrase}%"),
            )
        )

    return stmt


def apply_default_sorting(stmt: sa.Select) -> sa.Select:
    """Apply default sorting for articles list.

    Sort order:
    1. article_created_date DESC (newest first)
    2. Status priority: in_progress (0) → unread (1) → done (2)
    3. title ASC (alphabetical)

    Args:
        stmt: SQLAlchemy select statement
    Returns:
        Modified select statement
    """
    status_order = sa.case(
        (sa.and_(Article.done == False, Article.unread == False), 0),  # in_progress
        (Article.unread == True, 1),  # unread
        else_=2,  # done
    )

    stmt = stmt.order_by(
        Article.article_created_date.desc(),
        status_order.asc(),
        sa.func.lower(Article.title).asc(),
    )

    return stmt


def get_recent_articles(user_id: int, limit: int = 3) -> list[Article]:
    """Get most recently opened articles.

    Args:
        user_id: User ID
        limit: Number of articles to return (default 3)
    Returns:
        List of Article objects
    """
    stmt = (
        sa.select(Article)
        .where(
            Article.user_id == user_id,
            Article.processing == False,
            Article.archived == False,
            Article.date_read.isnot(None),
        )
        .order_by(Article.date_read.desc())
        .limit(limit)
    )

    return list(db.session.scalars(stmt))
