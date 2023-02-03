from app import db
from app.models import Tag


def update_tags(tags, resource):
    """updates an articles or highlights tags and returns the updated resource
    fully replaces the tags on the resource to match the tags list that is passed in.

    Args:
        tags (string[]): list of tag names
        resource (article or highlight object): resource

    Returns:
        article: updated with tags
    """
    resource_tags = resource.tag_list
    for tag_name in resource_tags:
        if tag_name not in tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if tag:
                resource.remove_tag(tag)

    for tag_name in tags:
        if tag_name not in resource_tags:
            tag = Tag.query.filter_by(name=tag_name, user_id=resource.user_id).first()
            if not tag:
                tag = Tag(name=tag_name, user_id=resource.user_id)
                db.session.add(tag)
            resource.add_tag(tag)

    return resource
