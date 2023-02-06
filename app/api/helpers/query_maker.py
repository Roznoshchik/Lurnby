def apply_pagination(query, page="1", per_page="15"):
    """applies pagination

    Args:
        query (flask_sqlalchemy.query.Query): base query object
        page (str): an int string for which page of results e.g "1"
        per_page (str): "all" or int string e.g "15" or "30"
    Returns:
        query (flask_sqlalchemy.query.Query): updated query object
    """
    # prepare to paginate results
    result_count = query.count()
    if per_page == "all":
        per_page = result_count
    else:
        per_page = int(per_page)

    query = query.paginate(page=int(page), per_page=per_page, error_out=False)

    return query
