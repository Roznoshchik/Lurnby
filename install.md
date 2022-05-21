# Installing locally
To run the following things should be installed on the system. 

- Python
- Redis-server
- node (used by ReadabiliPy to access Mozilla's readability.js)

## Installing on a mac
1. Clone the repo
2. cd into directory
3. python3 -m venv venv // isolates and creates a virtual env
4. . venv/bin/activate // activate venv
5. pip install -r requirements.txt // installs requirements
6. flask db upgrade // creates the db
7. flask run // starts the flask server
8. open new terminal tab
0. redis-server // start redis server
10. open new terminal tab
11. . venv/bin/activate // activate venv
12. rq worker lurnby-tasks // start listening for bg tasks

## apis
The app also uses some apis to do what it needs to do. 
- amazon s3 for storing images from epubs
- google for auth
- sendgrid for sending emails.

These need to be set in a .env file, see the .env.example file. 