from uuid import UUID

from app import db
from app.api.errors import LurnbyValueError
from app.models import Highlight, Tag, Article


def validate_request(data: dict):
    """Checks if data has a uuid or id included
    and verifies that an existing highlight with
    that data doesn't exist

    Args:
        data (dict): new highlight payload
    """

    if "uuid" in data:
        highlight = Highlight.query.filter_by(uuid=data["uuid"]).first()
        if highlight:
            raise LurnbyValueError("Highlight exists, use update methods instead.")
    if "text" not in data:
        raise LurnbyValueError("Text is a required field")


def populate_highlight(highlight, data: dict):
    """Adds payload data to highlight

    Args:
        highlight (app.models.Highlight): new highlight instance
        data (dict): payload sent from client with highlight data

    Returns:
        highlight(app.models.Highlight): updated highlight
    """
    article = None
    if "article_id" in data:
        uuid = UUID(data.get("article_id"))
        article = Article.query.filter_by(uuid=uuid).first()

    if article:
        highlight.article_id = article.id
        highlight.source = article.title

    if data.get("uuid"):
        highlight.uuid = data.get("uuid")

    highlight.text = data.get("text")
    highlight.note = data.get("note")
    highlight.source = data.get("source", highlight.source)
    highlight.prompt = highlight.create_prompt()

    return highlight


def add_tags(highlight, tags=[]):
    """creates tags if they don't exist and adds them to the highlight

    Args:
        highlight (class 'app.models.Highlight'): Instantiated highlight
        user_id (int): id for the current user
        tags (list): list of tag names. Defaults to [].

    Returns:
        highlight (class 'app.models.highlight'): Updated with tags
    """

    for tag_name in tags:
        tag = Tag.query.filter_by(name=tag_name.lower(), user_id=highlight.user_id).first()
        if not tag:
            tag = Tag(user_id=highlight.user_id, name=tag_name.lower())
            db.session.add(tag)

        highlight.add_tag(tag)

    return highlight
