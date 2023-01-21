from app import db
from app.models import Article, tags_articles
from sqlalchemy import func


def filter_by_status(query, status):
  """
  Args:
      query (flask_sqlalchemy.query.Query): base query object
      status (string): status to filter by
  Returns:
      query (flask_sqlalchemy.query.Query): updated query object
  """
  
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

  return query


def filter_by_tags(query, tag_ids):
  """
  Args:
      query (flask_sqlalchemy.query.Query): base query object
      tag_ids (string): string of comma separated tag ids e.g. '1,53,23'
  Returns:
      query (flask_sqlalchemy.query.Query): updated query object
  """
  if tag_ids is not None:
    tag_ids = [int(tag) for tag in tag_ids.split(',')]
    join_article_id = tags_articles.c.article_id
    join_tag_id = tags_articles.c.tag_id

    # join tags
    query = query.join(tags_articles, (join_article_id == Article.id))
    # apply filter
    query = query.filter(join_tag_id.in_(tag_ids))

  return query


def filter_by_search_phrase(query, search_phrase):
  """filters by user supplied search phrase

  Args:
      query (flask_sqlalchemy.query.Query): base query object
      search_phrase (str): e.g "I like bananas"
  Returns:
      query (flask_sqlalchemy.query.Query): updated query object
  """
  if search_phrase is not None:
    query = query.filter(db.or_(
        Article.title.ilike(f'%{search_phrase}%'),
        Article.source_url.ilike(f'%{search_phrase}%'),
        Article.source.ilike(f'%{search_phrase}%'),
        Article.notes.ilike(f'%{search_phrase}%'),
        Article.content.ilike(f'%{search_phrase}%')  # this might be too much
    ))

  return query

def apply_sorting(query, title_sort, opened_sort):
  """_summary_

  Args:
      query (flask_sqlalchemy.query.Query): base query object
      title_sort (str): Sort alphabetically by article title - "asc" or "desc"
      opened_sort (str): Sort by last opened - "asc" or "desc"
  Returns:
      query (flask_sqlalchemy.query.Query): updated query object
  """
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

  return query

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
  if per_page == 'all':
      per_page = result_count
  else:
      per_page = int(per_page)

  query = query.paginate(page=int(page), per_page=per_page, error_out=False)

  return query