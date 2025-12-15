from datetime import datetime
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
import sys

from config import Config
from flask import Flask
from flask.logging import default_handler
from flask_cors import CORS
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from redis import Redis
import rq
from sqlalchemy import MetaData
import boto3
from botocore.client import Config as AZConfig


class CustomLogger(logging.Logger):
    def __init__(
        self,
        name: str,
        stream_handler=sys.stdout,
        level=logging.INFO,
        log_format=logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)-8s %(filename)s:%(funcName)s - %(message)s"
        ),
    ):

        super().__init__(name)
        self.setLevel(level)
        console_handler = logging.StreamHandler(stream_handler)
        console_handler.setFormatter(log_format)

        self.addHandler(console_handler)


convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=convention)

db = SQLAlchemy(metadata=metadata)
migrate = Migrate()
login = LoginManager()
login.login_view = "auth.login"
login.login_message = None
mail = Mail()
cors = CORS()
csrf = CSRFProtect()
talisman = Talisman()

my_config = AZConfig(
    region_name="us-east-2",
    signature_version="s3v4",
)


s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    config=my_config,
)
bucket = os.environ.get("AWS_BUCKET")


csp = {
    "default-src": [
        "'self'",
        "'unsafe-inline'",
        "*.getbootsrap.com/*",
        "*.bootstrapcdn.com/*",
        "*.jquery.com/*",
        "*.cloudflare.com/ajax/libs/*",
    ]
}


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.redis = Redis.from_url(app.config["REDIS_URL"])
    app.task_queue = rq.Queue("lurnby-tasks", connection=app.redis)

    @app.before_request
    def before_request_func():
        if current_user.is_authenticated:
            current_user.last_active = datetime.utcnow()
            db.session.commit()

    # Add a variable into the app that can be used in all routes and blueprints
    # This one is so that I can have a now variable that automatically updates the copyright notice at the bottom.
    @app.context_processor
    def inject():
        if os.environ.get("DEV"):
            staging = True
        else:
            staging = False

        return {"now": datetime.utcnow(), "staging": staging}

    cors.init_app(app, resources={r"/app/api/*": {"origins": "*"}})

    db.init_app(app)

    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    talisman.init_app(app, content_security_policy=None)
    csrf.init_app(app)

    from app.errors import bp as errors_bp

    app.register_blueprint(errors_bp, url_prefix="/app")

    from app.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/app/auth")

    from app.main import bp as main_bp

    app.register_blueprint(main_bp, url_prefix="/app")

    from app.settings import bp as settings_bp

    app.register_blueprint(settings_bp, url_prefix="/app")

    from app.api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    csrf.exempt(api_bp)

    from app.content import bp as content_bp

    app.register_blueprint(content_bp, url_prefix="/app")

    from app.dotcom import bp as dotcom_bp

    app.register_blueprint(dotcom_bp)

    from app.assets_blueprint import assets_blueprint

    app.register_blueprint(assets_blueprint)

    if __name__ == "__main__":
        app.run(ssl_context=("cert.pem", "key.pem"))

    # OAuth 2 client setup

    if not app.debug and not app.testing:
        if app.config["MAIL_SERVER"]:
            auth = None
            if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
                auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            secure = None
            if app.config["MAIL_USE_TLS"]:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
                fromaddr="team@lurnby.com",
                toaddrs=app.config["ADMINS"],
                subject="Lurnby Failure",
                credentials=auth,
                secure=secure,
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
            app.logger.removeHandler(default_handler)

    if app.config["LOG_TO_STDOUT"]:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        stream_handler.setFormatter(formatter)
        app.logger.addHandler(stream_handler)
        app.logger.removeHandler(default_handler)
    else:
        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            "logs/lurnby.log", maxBytes=10240, backupCount=10
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("Lurnby")
        app.logger.removeHandler(default_handler)
    return app


from app import models  # noqa : E402, F401
