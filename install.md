# Installing locally
To run the following things should be installed on the system.

- Python
- Redis-server
- node (used by ReadabiliPy to access Mozilla's readability.js)
- [just](https://github.com/casey/just) (command runner)

## Installing on a mac
1. Clone the repo
1. `cd` into directory
1. `python3 -m venv venv` // isolates and creates a virtual env
1. `. venv/bin/activate` // activate venv
1. `just install` // installs Python and Node.js dependencies
1. `flask db upgrade` // creates the db
1. `cp .env.example .env` // create env file and edit with your credentials

### Running the development server

```bash
just serve
```
This automatically starts Redis, RQ worker, Vite dev server, and Flask.

For production mode (builds assets first):
```bash
just serve-prod
```

### Other commands
```bash
just              # list all available commands
just test         # run all tests
just test-python  # run Python tests only
just test-client  # run client tests only
just format       # format all code
just lint         # lint all code
just build        # build frontend assets
```

## apis
The app also uses some apis to do what it needs to do.
- amazon s3 for storing images from epubs
- google for auth
- sendgrid for sending emails.

These need to be set in a .env file, see the .env.example file.

Some more details for mac are in [mac-install-notes.md](./mac-install-notes.md).
