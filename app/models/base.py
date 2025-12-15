import base64

from app import db, login, CustomLogger
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask import current_app, url_for
from flask_login import UserMixin, current_user
import jwt
import json
import uuid
import os
import random
import re
import redis
import rq
from sqlalchemy import desc, func, Index
from sqlalchemy_utils import UUIDType
import string
from time import time
import traceback
from werkzeug.security import generate_password_hash, check_password_hash


logger = CustomLogger("MODELS")
PREFERENCES = '{"font": "sans-serif","color": "light-mode", \
              "size": "4","spacing": "line-height-min"}'


def generate_str_id():
    return uuid.uuid4().hex
