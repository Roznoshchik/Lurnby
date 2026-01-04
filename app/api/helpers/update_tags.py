from sqlalchemy import select

from app import db
from app.models import Tag


def update_tags(tag_ids, resource):
    """Updates an article's or highlight's tags and returns the updated resource.
    Fully replaces the tags on the resource to match the tag IDs passed in.

    Args:
        tag_ids (int[]): list of tag IDs
        resource (Article or Highlight): resource to update

    Returns:
        resource: updated with tags
    """
    current_tag_ids = resource.tag_ids

    # Remove tags that are no longer selected
    for tag_id in current_tag_ids:
        if tag_id not in tag_ids:
            tag = db.session.get(Tag, tag_id)
            if tag:
                resource.remove_tag(tag)

    # Add newly selected tags
    for tag_id in tag_ids:
        if tag_id not in current_tag_ids:
            stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == resource.user_id)
            tag = db.session.execute(stmt).scalar()
            if tag:
                resource.add_tag(tag)

    return resource
