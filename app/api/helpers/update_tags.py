from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Article, Tag, tags_articles, tags_highlights


def _create_tags_and_get_ids(new_tag_names, user_id):
    """Creates new tags and returns their IDs.

    If a name already exists, returns its ID (graceful handling).

    Args:
        new_tag_names (list[str]): list of tag names to create
        user_id (int): user ID for ownership

    Returns:
        list[int]: list of tag IDs (newly created + any that already existed)
    """
    if not new_tag_names:
        return []

    names_lower = [n.lower() for n in new_tag_names]

    # Batch check existing
    existing = db.session.scalars(select(Tag).where(Tag.name.in_(names_lower), Tag.user_id == user_id)).all()
    existing_by_name = {t.name: t for t in existing}

    tag_ids = []
    for name in names_lower:
        if name in existing_by_name:
            # Shouldn't happen, but handle gracefully
            tag_ids.append(existing_by_name[name].id)
        else:
            tag = Tag(user_id=user_id, name=name)
            db.session.add(tag)
            db.session.flush()
            tag_ids.append(tag.id)

    return tag_ids


def update_tags(resource, tag_ids=None, new_tag_names=None):
    """Updates an article's or highlight's tags and returns the updated resource.
    Fully replaces the tags on the resource to match the combined tag IDs.

    Works directly with the junction table to avoid unnecessary Tag object queries.

    Args:
        resource (Article or Highlight): resource to update
        tag_ids (list[int]): list of existing tag IDs to assign
        new_tag_names (list[str]): list of new tag names to create and assign

    Returns:
        resource: updated with tags
    """
    new_tag_ids = set(tag_ids or [])

    if new_tag_names:
        new_tag_ids.update(_create_tags_and_get_ids(new_tag_names, resource.user_id))

    # Determine junction table and column names based on resource type
    if isinstance(resource, Article):
        junction = tags_articles
        resource_col = junction.c.article_id
    else:
        junction = tags_highlights
        resource_col = junction.c.highlight_id

    current_tag_ids = set(resource.tag_ids)

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
