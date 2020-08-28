import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os

from oauthlib.oauth2 import WebApplicationClient


from config import Config
from flask import Flask, request, current_app
from flask_cors import CORS
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman



db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view='auth.login'
login.login_message = 'Please log in to access this page'
mail = Mail()
cors = CORS()
talisman = Talisman()

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
    
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    talisman.init_app(app, content_security_policy=None)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')


    if __name__ == "__main__":
        app.run(ssl_context=('cert.pem', 'key.pem'))

    # OAuth 2 client setup
    #client = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])

    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost = (app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='Learning App Failure',
                credentials=auth, secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/learningtool.log', maxBytes=10240, backupCount=10)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Learning tool startup')
    
    return app

from app import models

