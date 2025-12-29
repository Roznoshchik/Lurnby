import uuid

from app import CustomLogger, db  # noqa: F401
import redis  # noqa: F401
import rq  # noqa: F401

logger = CustomLogger("MODELS")
PREFERENCES = '{"font": "sans-serif","color": "light-mode", \
              "size": "4","spacing": "line-height-min"}'


def generate_str_id():
    return uuid.uuid4().hex
