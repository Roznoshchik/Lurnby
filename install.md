# Installing locally
To run the following things should be installed on the system. 

- Python
- Redis-server
- node (used by ReadabiliPy to access Mozilla's readability.js)

## Installing on a mac
1. Clone the repo
1. `cd` into directory
1. `python3 -m venv venv` // isolates and creates a virtual env
1. `. venv/bin/activate` // activate venv
1. `pip install -r requirements.txt` // installs Python requirements
1. `cd client && npm install && cd ..` // installs Node.js requirements for Preact frontend
1. `flask db upgrade` // creates the db
1. `cp .env.example .env` // create env file and edit with your credentials

### Running the development server

**Easy way (recommended):** One command starts everything
```bash
export FLASK_DEBUG=1
flask serve
```
This automatically starts:
- Redis server
- RQ worker (for background tasks)
- Vite dev server (for frontend with HMR)
- Flask server

**Manual way (old):** Multiple terminals
1. Terminal 1: `flask run` // starts the flask server
1. Terminal 2: `redis-server` // start redis server
1. Terminal 3: `. venv/bin/activate && rq worker lurnby-tasks` // start listening for bg tasks
1. Terminal 4: `cd client && npm start` // start Vite dev server

## apis
The app also uses some apis to do what it needs to do. 
- amazon s3 for storing images from epubs
- google for auth
- sendgrid for sending emails.

These need to be set in a .env file, see the .env.example file.

Some more details for mac are in [mac-install-notes.md](./mac-install-notes.md).

