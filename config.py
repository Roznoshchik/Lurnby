import os

basedir = os.path.abspath(os.path.dirname(__file__))

from dotenv import load_dotenv
dotenv_path = os.path.join(basedir, '.env')
load_dotenv(dotenv_path)


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Slava-fakes-it-till-he-makes-it'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', None)
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', None)
    GOOGLE_DISCOVERY_URL = ("https://accounts.google.com/.well-known/openid-configuration")