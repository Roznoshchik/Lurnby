import sqlalchemy as sa

from app import db


def get_total_count(stmt: sa.Select) -> int:
    """Get total count for a select statement."""
    count_stmt = stmt.with_only_columns(sa.func.count()).order_by(None)
    return db.session.scalar(count_stmt)


def apply_pagination(
    stmt: sa.Select,
    page: str = "1",
    per_page: str = "15",
    *,
    scalars: bool = True,
) -> tuple[list, bool]:

    page_num = int(page)

    if per_page == "all":
        if scalars:
            items = list(db.session.scalars(stmt))
        else:
            items = list(db.session.execute(stmt))
        return items, False

    per_page_num = int(per_page)
    offset = (page_num - 1) * per_page_num

    paginated_stmt = stmt.offset(offset).limit(per_page_num + 1)

    if scalars:
        items = list(db.session.scalars(paginated_stmt))
    else:
        items = list(db.session.execute(paginated_stmt))

    has_next = len(items) > per_page_num
    if has_next:
        items = items[:per_page_num]

    return items, has_next
