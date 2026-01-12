import sqlalchemy as sa

from app.models import Article, Highlight, tags_highlights


def filter_by_status(stmt: sa.Select, status: str) -> sa.Select:
    """Filter highlights by archive status.

    Args:
        stmt: SQLAlchemy select statement
        status: status to filter by (unarchived, archived, all)
    Returns:
        Modified select statement
    """
    if not status or status.lower() == "unarchived":
        stmt = stmt.where(Highlight.archived.is_(False))
    elif status.lower() == "archived":
        stmt = stmt.where(Highlight.archived.is_(True))
    # "all" returns everything, no filter applied

    return stmt


def filter_by_tag_status(stmt: sa.Select, tag_status: str) -> sa.Select:
    """Filter highlights by tag status.

    Uses EXISTS subquery on junction table to determine if highlight has tags.

    Args:
        stmt: SQLAlchemy select statement
        tag_status: 'tagged' or 'untagged'
    Returns:
        Modified select statement
    """
    if not tag_status:
        return stmt

    has_tags_subq = (
        sa.select(tags_highlights.c.highlight_id).where(tags_highlights.c.highlight_id == Highlight.id).exists()
    )

    if tag_status.lower() == "tagged":
        stmt = stmt.where(has_tags_subq)
    elif tag_status.lower() == "untagged":
        stmt = stmt.where(~has_tags_subq)

    return stmt


def filter_by_tags(stmt: sa.Select, tag_ids: str) -> sa.Select:
    """Filter highlights by tag IDs (OR logic - highlights with any of the tags).

    Uses EXISTS subquery to avoid duplicates when a highlight has multiple
    matching tags, which is more compatible with ORDER BY than DISTINCT.

    Args:
        stmt: SQLAlchemy select statement
        tag_ids: comma-separated tag IDs e.g. '1,53,23'
    Returns:
        Modified select statement
    """
    if tag_ids is not None:
        tag_id_list = [int(tag) for tag in tag_ids.split(",")]
        tag_subq = (
            sa.select(tags_highlights.c.highlight_id)
            .where(
                tags_highlights.c.highlight_id == Highlight.id,
                tags_highlights.c.tag_id.in_(tag_id_list),
            )
            .exists()
        )
        stmt = stmt.where(tag_subq)

    return stmt


def filter_by_search_phrase(stmt: sa.Select, search_phrase: str) -> sa.Select:
    """Filter highlights by search phrase (searches text, note, article title).

    Args:
        stmt: SQLAlchemy select statement
        search_phrase: e.g "I like bananas"
    Returns:
        Modified select statement
    """
    if search_phrase is not None:
        stmt = stmt.join(Article, Highlight.article_id == Article.id, isouter=True)
        stmt = stmt.where(
            sa.or_(
                Highlight.text.ilike(f"%{search_phrase}%"),
                Highlight.note.ilike(f"%{search_phrase}%"),
                Article.title.ilike(f"%{search_phrase}%"),
            )
        )

    return stmt


def apply_default_sorting(stmt: sa.Select, created_sort: str = None) -> sa.Select:
    """Apply sorting for highlights list.

    Args:
        stmt: SQLAlchemy select statement
        created_sort: 'asc' or 'desc' (default: desc)
    Returns:
        Modified select statement
    """
    if created_sort and created_sort.lower() == "asc":
        stmt = stmt.order_by(Highlight.created_date.asc())
    else:
        stmt = stmt.order_by(Highlight.created_date.desc())

    return stmt
