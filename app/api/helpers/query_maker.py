import sqlalchemy as sa

from app import db


def apply_pagination(stmt: sa.Select, page: str = "1", per_page: str = "15") -> tuple[list, bool]:
    """Apply pagination to a select statement.

    Args:
        stmt: SQLAlchemy select statement
        page: page number as string e.g "1"
        per_page: "all" or int string e.g "15" or "30"
    Returns:
        Tuple of (items list, has_next boolean)
    """
    page_num = int(page)

    if per_page == "all":
        items = list(db.session.scalars(stmt))
        return items, False

    per_page_num = int(per_page)
    offset = (page_num - 1) * per_page_num

    # Get one extra to check if there's a next page
    paginated_stmt = stmt.offset(offset).limit(per_page_num + 1)
    items = list(db.session.scalars(paginated_stmt))

    has_next = len(items) > per_page_num
    if has_next:
        items = items[:per_page_num]

    return items, has_next
