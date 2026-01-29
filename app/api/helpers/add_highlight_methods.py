from uuid import UUID

from app.api.errors import LurnbyValueError
from app.models import Highlight, Article


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
    article_uuid = data.get("article_uuid") or data.get("article_id")
    if article_uuid:
        uuid = UUID(article_uuid)
        article = Article.query.filter_by(uuid=uuid).first()

    if article:
        highlight.article_id = article.id
        highlight.source = article.title

    if data.get("uuid"):
        highlight.uuid = data.get("uuid")

    highlight.text = data.get("text")
    highlight.note = data.get("note")
    highlight.source = data.get("source", highlight.source)
    highlight.start = data.get("start")
    highlight.end = data.get("end")

    if "do_not_review" in data:
        highlight.do_not_review = data.get("do_not_review")

    autogenerate_prompt = data.get("autogenerate_prompt", True)
    if autogenerate_prompt:
        highlight.prompt = highlight.create_prompt()
    elif data.get("prompt"):
        highlight.prompt = data.get("prompt")

    return highlight
