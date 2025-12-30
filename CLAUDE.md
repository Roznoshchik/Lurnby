# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lurnby is a personal knowledge practice tool built with Flask that helps users read and remember more through active recall and spaced repetition. It supports web articles and epubs with highlighting, categorization, and review features.

**Tech Stack:**
- Backend: Flask, SQLAlchemy, PostgreSQL, Redis
- Frontend: Preact + Vite (active migration from Jinja2 templates), JavaScript, CSS
- Background Tasks: RQ (Redis Queue)
- External Services: AWS S3 (epub images), Google OAuth, SendGrid (email)
- Deployment: Heroku (via git push using Dockerfile)
- Testing: pytest (backend), Vitest (frontend)

## Development Setup

### Initial Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
. venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies for Preact frontend
cd client && npm install && cd ..

# Setup database
flask db upgrade

# Create .env file from .env.example
cp .env.example .env
# Edit .env with required credentials
```

### Running the Application

**Recommended (one command):**
```bash
# Development mode with HMR
export FLASK_DEBUG=1
flask serve
# This starts: Redis → RQ worker → Vite dev server → Flask

# Production mode (tests built assets)
flask serve --prod
# This starts: Redis → RQ worker → Flask
# Automatically builds assets first
```

**Manual (old method, multiple terminals):**
```bash
# Terminal 1: Flask server
flask run

# Terminal 2: Redis server
redis-server

# Terminal 3: Background task worker
. venv/bin/activate
rq worker lurnby-tasks

# Terminal 4: Vite dev server (for Preact frontend)
cd client && npm start
```

### Testing
```bash
# Run all tests (Python + frontend)
flask test

# Run only Python tests
flask test --python-only

# Run only frontend tests
flask test --client-only

# Run Python tests with coverage
pytest --cov=app

# Run specific test file
pytest tests/api/test_articles.py

# Run frontend tests with UI
cd client && npm run test:ui
```

### Code Quality
```bash
# Format code (both Python and client)
flask format

# Format only Python files
flask format --python-only

# Format only client files
flask format --client-only

# Lint code (both Python and client)
flask lint

# Lint only Python files
flask lint --python-only

# Lint only client files
flask lint --client-only

# Run pre-commit hooks manually
pre-commit run --all-files

# Install pre-commit hooks (runs automatically on commit)
pre-commit install
```

**Flask format and lint commands:**
- Format: Uses Black for Python, Biome for client (JavaScript/JSX)
- Lint: Uses Flake8 for Python, Biome for client
- Automatically excludes ReadabiliPy, migrations, and other configured directories

**Pre-commit hooks include:**
- Flake8 (serious errors only: syntax errors, undefined names)
- Black (manual stage, for checking only)
- Pytest (Python tests)
- Vitest (frontend tests)
- Trailing whitespace, end-of-file-fixer, check-yaml, etc.

## Architecture

### Application Structure

The app uses Flask's application factory pattern with blueprints:

- **`learnbetter.py`**: Entry point that creates the Flask app and registers shell context
- **`config.py`**: Configuration management using environment variables
- **`app/__init__.py`**: Application factory (`create_app()`) and extension initialization
- **`app/models/`**: SQLAlchemy models split into separate files (user.py, article.py, highlight.py, event.py, tag.py, etc.)
- **`app/cli.py`**: Custom Flask CLI commands (serve, build, test)

### Blueprints

1. **`app/auth`**: Authentication routes (login, register, password reset)
2. **`app/main`**: Core user-facing routes for reading, highlighting, and reviewing content
3. **`app/content`**: Content management routes
4. **`app/settings`**: User settings and preferences
5. **`app/api`**: RESTful API endpoints (articles, highlights, tags, users, auth)
6. **`app/client`**: Preact frontend routes (serves client-side rendered pages)
7. **`app/dotcom`**: Marketing/landing page routes
8. **`app/errors`**: Error handlers
9. **`app/assets_blueprint`**: Asset resolution for dev/prod environments

### Key Components

**Background Tasks (`app/tasks.py`):**
- Uses RQ (Redis Queue) for async processing
- Handles epub conversion, PDF imports, exports, and email generation
- Tasks update progress via Redis for UI feedback

**Content Processing:**
- **ReadabiliPy**: Mozilla Readability.js wrapper for extracting clean article content from web pages
- **EbookLib + PyMuPDF**: EPUB and PDF processing
- **BeautifulSoup + lxml**: HTML parsing and manipulation
- Web article text extraction in `app/helpers/pulltext.py`
- EPUB handling in `app/helpers/ebooks.py`
- PDF handling in `app/helpers/pdf.py`

**Review System (`app/helpers/review.py`):**
- Implements spaced repetition for highlights
- `order_highlights()` function determines review order based on intervals

**Export System (`app/export.py`, `app/helpers/export_helpers.py`):**
- Exports user data (highlights, articles) to various formats
- ZIP file generation for bulk exports

### Data Models

Core relationships:
- **User** → Articles (one-to-many)
- **User** → Highlights (one-to-many)
- **User** → Topics (one-to-many, for categorization)
- **User** → Tags (one-to-many)
- **Article** → Highlights (one-to-many)
- **Highlight** ↔ Topics (many-to-many via `highlights_topics`)
- **Article/Highlight** ↔ Tags (many-to-many via `tags_articles`, `tags_highlights`)

Important model features:
- Most models use UUIDs for public-facing IDs while keeping integer primary keys
- Soft deletes for Users (via `deleted` boolean)
- Task model tracks background job progress
- Event model logs user actions for analytics

### Database

- **Development**: PostgreSQL
- **Production**: PostgreSQL
- **Migrations**: Flask-Migrate (Alembic)

Migration commands:
```bash
# Create migration after model changes
flask db migrate -m "description"

# Apply migrations
flask db upgrade

# Rollback
flask db downgrade
```

### Static Assets

Located in `app/static/`:
- Custom JavaScript for text selection, highlighting UI, and sidebar
- SASS stylesheets
- Service worker for PWA functionality
- Third-party libraries (Rangy for text selection)
- `dist/` - Vite build output for Preact frontend (gitignored in dev)

### Preact Frontend Architecture

**Structure:**
- `client/` - Preact source code and Vite configuration
  - `client/static/` - Preact components and entry points
  - `client/vite.config.js` - Build config (outputs to `app/static/dist/`)
  - `client/package.json` - Node.js dependencies
- `app/assets_blueprint.py` - Blueprint for dev/prod asset resolution
  - Dev mode: Proxies to Vite dev server on port 5173 with HMR
  - Prod mode: Serves built files from `app/static/dist/bundled/`
- `app/templates/*.html` - Gradually migrating from Jinja2 to Preact

**Asset Resolution:**
- Templates use `asset('file.ext')` helper function
- Dev: Returns Vite dev server URLs (e.g., `http://localhost:5173/static/dist/main.jsx`)
- Prod: Returns static file URLs from manifest (e.g., `/static/dist/bundled/main-[hash].js`)

**Implemented Pages:**
- Login page (`/client/login`) - Username/password authentication
- Articles page (`/client/articles`) - Article list with stats, filtering planned
- Shared components: Layout, Sidebar, MobileNav, ArticleCard, Button, Icon, Badge, Progress
- Auth system: AuthContext, RequireAuth wrapper, API client with auto-retry
- Design system: Light/dark themes, spacing scale, component library

### Browser Extensions

The `extensions/` directory contains browser extensions for Chrome, Firefox, and Safari that integrate with the API to save articles from the browser.

## Code Patterns

### API Authentication
The API uses modern token-based authentication:
- **Access tokens** (15 min, in-memory) for API requests
- **Refresh tokens** (30 days, HttpOnly cookie) for obtaining new access tokens
- **API tokens** (30 days) for browser extensions (legacy, backward compatible)
- Auth endpoints in `app/api/auth_routes.py` (/auth/login, /auth/refresh, /auth/logout, /auth/google)
- Token validation in `app/api/auth.py` (@token_auth decorator)
- Legacy token support in `app/api/tokens.py`
- Basic auth for initial login, bearer token for all API routes
- CSRF protection disabled for API blueprint

### API Endpoints
Key endpoint patterns:
- `/api/articles` - Get current user's articles (token-based, no user ID needed)
- `/api/highlights` - Get current user's highlights
- `/api/tags` - Get current user's tags
- `/api/user/stats` - Get current user's monthly activity stats
- `/api/users/:id/...` - User-specific operations (requires matching user ID)
- All endpoints use `@token_auth.login_required` and get user from token

### Forms
- WTForms with Flask-WTF for CSRF protection
- Custom validators using WTForms-Components
- Form classes in `forms.py` files within each blueprint

### Error Handling
- Custom error handlers in `app/errors/` blueprint
- JSON responses for API errors
- HTML templates for web errors

### Logging
- Custom logger class (`CustomLogger`) in `app/__init__.py`
- Logs to stdout in production (Heroku-friendly) or rotating files locally
- Error emails via SMTP in production

## Testing

Test structure in `tests/`:
- `tests/api/`: API endpoint tests
- `tests/helpers/`: Helper function tests
- `tests/models/`: Model tests
- `tests/mocks/`: Mock data for tests
- `tests/tasks/`: Background task tests
- `client/static/**/*.test.js`: Frontend unit tests (Vitest)

Python tests use:
- In-memory SQLite database (`sqlite://`)
- `TestConfig` class for test-specific configuration
- Mock objects and patches for external services

Frontend tests use:
- Vitest with happy-dom
- @testing-library/preact for component testing

**CI/CD:**
- GitHub Actions workflow (`.github/workflows/run_tests.yml`)
- Runs on push/PR to main branch
- Python job: pytest + flake8 on Python 3.12 with PostgreSQL
- Node job: Vitest on Node 22
- Both jobs run in parallel

## Environment Variables

Required for full functionality (see `.env.example`):
- `SECRET_KEY`: Flask session security
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`: OAuth
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_BUCKET`: S3 storage
- `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`: SendGrid email
- `SERVER_NAME`: For generating URLs in background tasks

## Deployment

**Platform:** Heroku

**Method:** Git push deployment using Dockerfile
```bash
git push heroku main
```

The app uses a Dockerfile for containerized deployment. Heroku builds and deploys the container automatically on push to the `main` branch.

**Important for Preact frontend:**
- Production builds must be generated before deployment
- Vite build output (`app/static/dist/`) should be committed or built during deployment
- Set `FLASK_DEBUG=0` in production environment variables

## Common Gotchas

1. **PostgreSQL URL format**: The config automatically converts `postgres://` to `postgresql://` for SQLAlchemy compatibility
2. **Node.js required**: ReadabiliPy requires Node.js >=11.0.0 for the jsdom dependency
3. **Redis required**: Background tasks require Redis server to be running
4. **Migrations**: The app excludes ReadabiliPy and other directories from flake8 checks
5. **CSRF**: API routes are exempt from CSRF protection, but web routes require CSRF tokens
6. **Boolean comparisons**: Some files have flake8 exceptions for explicit boolean comparisons (E712) where they're intentional
7. **Vite build artifacts**: The `app/static/dist/` directory is in `.gitignore` to avoid committing build artifacts during development

## Code comments
Obvious comments are not necessary and should only be added sparingly and if its necessary to understand what is happening.

## Commit messages
NO attribution to Claude code
NO Generated by Claude code

commit messages should largely focus on what was added / removed
but they should be about the strategic and functional changes
they shouldn't include random comments or the micro details of every file change

## Working state
Explore the .local file for files of the following format
Check the branch name
then check
claude-progress-<branch name>.md
claude-tasks-<branch name>.json

If not found, look for any files in there and ask me which ones to use

### No working state
If I say create task - <TASK NAME>
Then we should create new files with that task name.

You should also then ask me for a description of the task. And then we should discuss until we agree on the highlevel steps for the todo list and then you create one with the following structure.

This is the structure of the claude-tasks-*.json file
[
  {
    "category": "functional",
    "description": "New chat button creates a fresh conversation",
    "steps": [
      "Navigate to main interface",
      "Click the 'New Chat' button",
      "Verify a new conversation is created",
      "Check that chat area shows welcome state",
      "Verify conversation appears in sidebar"
    ],
    "relevant_files": [
      "app/api/articles.py#236-250",
      "app/api/highlights.py#112-150"
    ],
    "passes": false
  }

]

The progress file is just a summary of the work that we did.

### Existing working state
I will say Status <task name> - look for files for that task and get the status of the work done. If it doesn't exist - create the files and per the instructions above.

**important** - only work on a single task at a time

Once the task is done, we commit the code.
