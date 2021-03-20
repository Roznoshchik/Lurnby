from datetime import datetime
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os

from config import Config
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
import boto3


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page'
mail = Mail()
cors = CORS()
csrf = CSRFProtect()
talisman = Talisman()

s3 = boto3.client('s3',
                    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
                    )
bucket = os.environ.get('AWS_BUCKET')


csp = {
    'default-src': [
        '\'self\'',
        '\'unsafe-inline\'',
        '*.getbootsrap.com/*',
        '*.bootstrapcdn.com/*',
        '*.jquery.com/*',
        '*.cloudflare.com/ajax/libs/*'
    ]
}


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    @app.before_request
    def before_request_func():
        if current_user.is_authenticated:
            current_user.last_active = datetime.utcnow()
            db.session.commit()
        else:
            print('not logged in user')

    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    talisman.init_app(app, content_security_policy=None)
    csrf.init_app(app)
   
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    csrf.exempt(api_bp)

    from app.experiments import bp as experiments_bp
    app.register_blueprint(experiments_bp)

    if __name__ == "__main__":
        app.run(ssl_context=('cert.pem', 'key.pem'))

    # OAuth 2 client setup

    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'],
                          app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='Learning App Failure',
                credentials=auth, secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:

            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/learningtool.log',
                                               maxBytes=10240, backupCount=10)
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

            app.logger.setLevel(logging.INFO)
            app.logger.info('Learning tool startup')

    return app


from app import models # noqa : E402, F401
