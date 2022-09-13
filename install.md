# Installing locally
To run the following things should be installed on the system. 

- Python
- Redis-server
- node (used by ReadabiliPy to access Mozilla's readability.js)

## Installing on a mac
1. Clone the repo
1. cd into directory
1. python3 -m venv venv // isolates and creates a virtual env
1. . venv/bin/activate // activate venv
1. pip install -r requirements.txt // installs requirements
1. npm install // installs node requirements
1. flask db upgrade // creates the db
1. flask run // starts the flask server
1. open new terminal tab
1. redis-server // start redis server
1. open new terminal tab
1. . venv/bin/activate // activate venv
1. rq worker lurnby-tasks // start listening for bg tasks

## apis
The app also uses some apis to do what it needs to do. 
- amazon s3 for storing images from epubs
- google for auth
- sendgrid for sending emails.

These need to be set in a .env file, see the .env.example file.

Some more details for mac are in [mac-install-notes.md](./mac-install-notes.md).

