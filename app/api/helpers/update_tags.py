from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Article, Tag, tags_articles, tags_highlights


def update_tags(tag_ids, resource):
    """Updates an article's or highlight's tags and returns the updated resource.
    Fully replaces the tags on the resource to match the tag IDs passed in.

    Works directly with the junction table to avoid unnecessary Tag object queries.

    Args:
        tag_ids (int[]): list of tag IDs
        resource (Article or Highlight): resource to update

    Returns:
        resource: updated with tags
    """
    # Determine junction table and column names based on resource type
    if isinstance(resource, Article):
        junction = tags_articles
        resource_col = junction.c.article_id
    else:
        junction = tags_highlights
        resource_col = junction.c.highlight_id

    current_tag_ids = set(resource.tag_ids)
    new_tag_ids = set(tag_ids)

    # Remove tags that are no longer selected (idempotent - no error if not found)
    tags_to_remove = current_tag_ids - new_tag_ids
    if tags_to_remove:
        db.session.execute(junction.delete().where(resource_col == resource.id, junction.c.tag_id.in_(tags_to_remove)))

    # Add newly selected tags (only if they belong to the user)
    # We verify user_id ownership because tag_ids come from user input -
    # without this check, users could add another user's tags to their resources
    tags_to_add = new_tag_ids - current_tag_ids
    if tags_to_add:
        valid_tag_ids = db.session.scalars(
            select(Tag.id).where(Tag.id.in_(tags_to_add), Tag.user_id == resource.user_id)
        ).all()

        for tag_id in valid_tag_ids:
            try:
                with db.session.begin_nested():
                    db.session.execute(junction.insert().values(**{resource_col.name: resource.id, "tag_id": tag_id}))
            except IntegrityError:
                pass  # Tag already exists on resource, skip

    return resource
