import os
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from oauthlib.oauth2 import WebApplicationClient

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)

if __name__ == "__main__":
    app.run(ssl_context=('cert.pem', 'key.pem'))

# OAuth 2 client setup
client = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])


from app import routes, models

