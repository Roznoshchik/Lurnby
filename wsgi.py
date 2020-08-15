#from app import app
from flask import current_app


if __name__ == "__main__":
    #app.run()
    current_app._get_current_object().run()