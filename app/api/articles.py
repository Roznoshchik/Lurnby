from app import db
from app.api import bp
from app.api.auth import token_auth
# from app.api.errors import bad_request
# from app.main.pulltext import pull_text
from app.models import Article, tags_articles

# from datetime import datetime
from flask import jsonify, request
from sqlalchemy import func

""" ########################## """
""" ##     Get articles     ## """
""" ########################## """


@bp.route('/articles', methods=['GET'])
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

    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', 15)
    title_sort = request.args.get('title_sort', None)
    opened_sort = request.args.get('opened_sort', None)
    status = request.args.get('status', None)
    search = request.args.get('q', None)
    tag_ids = request.args.get('tag_ids', None)

    # get base query
    query = user.articles

    # filter by status
    if not status:
        query = query.filter_by(archived=False)
    elif status.lower() == 'archived':
        query = query.filter_by(archived=True)
    elif status.lower() == 'unread':
        query = query.filter(Article.unread == True, Article.done == False, Article.archived == False)
    elif status.lower() == 'in_progress':
        query = query.filter(Article.unread == False, Article.done == False, Article.archived == False)
    elif status.lower() == 'read':
        query = query.filter(Article.unread == False, Article.done == True, Article.archived == False)

    # filter by tags
    if tag_ids is not None:
        tag_ids = [int(tag) for tag in tag_ids.split(',')]
        join_article_id = tags_articles.c.article_id
        join_tag_id = tags_articles.c.tag_id

        # join tags
        query = query.join(tags_articles, (join_article_id == Article.id))
        # apply filter
        query = query.filter(join_tag_id.in_(tag_ids))

    # then search
    if search is not None:
        query = query.filter(db.or_(
            Article.title.ilike(f'%{search}%'),
            Article.source_url.ilike(f'%{search}%'),
            Article.source.ilike(f'%{search}%'),
            Article.notes.ilike(f'%{search}%'),
            Article.content.ilike(f'%{search}%')  # this might be too much
        ))

    # then prepare to sort
    order = []

    # first sort so read articles are last
    if not title_sort and not opened_sort:
        col = getattr(Article, 'done')
        order.append(col.asc())  # default order that done is last

    # then sort by title
    if title_sort is not None:
        if title_sort.lower() == 'desc':
            col = getattr(Article, 'title')
            col = func.lower(col)  # lowercase title
            col = col.desc()
            order.append(col)
        elif title_sort.lower() == 'asc':
            col = getattr(Article, 'title')
            col = func.lower(col)  # lowercase title
            col = col.asc()
            order.append(col)

    # then sort by date
    if opened_sort is not None:
        if opened_sort.lower() == 'desc':
            col = getattr(Article, 'date_read')
            col = col.desc()
            order.append(col)
        elif opened_sort.lower() == 'asc':
            col = getattr(Article, 'date_read')
            col = col.asc()
            order.append(col)

    # apply the sorting
    query = query.order_by(*order)

    # prepare to paginate results
    result_count = query.count()
    if per_page == 'all':
        per_page = result_count
    else:
        per_page = int(per_page)

    query = query.paginate(page=int(page), per_page=per_page, error_out=False)
    has_next = query.has_next if query.has_next else None
    articles = [article.to_dict() for article in query.items]

    response = jsonify(has_next=has_next, articles=articles)
    response.status_code = 200
    return response
