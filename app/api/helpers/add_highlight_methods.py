from app.api.errors import LurnbyValueError
from app.models import Highlight


def verify_non_existing_highlight(data: dict):
    """Checks if data has a uuid or id included
    and verifies that an existing highlight with
    that data doesn't exist

    Args:
        data (dict): new highlight payload
    """

    if "id" in data:
        highlight = Highlight.query.filter_by(id=data["id"]).first()
        if highlight:
            raise LurnbyValueError("Highlight exists, use update methods instead.")
    elif "uuid" in data:
        highlight = Highlight.query.filter_by(uuid=data["uuid"]).first()
        if highlight:
            raise LurnbyValueError("Highlight exists, use update methods instead.")
