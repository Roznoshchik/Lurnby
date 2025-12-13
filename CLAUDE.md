# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lurnby is a personal knowledge practice tool built with Flask that helps users read and remember more through active recall and spaced repetition. It supports web articles and epubs with highlighting, categorization, and review features.

**Tech Stack:**
- Backend: Flask, SQLAlchemy, PostgreSQL, Redis
- Frontend: Jinja2 templates, JavaScript, SASS
- Background Tasks: RQ (Redis Queue)
- External Services: AWS S3 (epub images), Google OAuth, SendGrid (email)

## Development Setup

### Initial Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
. venv/bin/activate

# Install dependencies
pip install -r requirements.txt
npm install

# Setup database
flask db upgrade

# Create .env file from .env.example
cp .env.example .env
# Edit .env with required credentials
```

### Running the Application
```bash
# Terminal 1: Flask server
flask run

# Terminal 2: Redis server
redis-server

# Terminal 3: Background task worker
. venv/bin/activate
rq worker lurnby-tasks
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/api/test_articles.py

# Run tests with verbose output
pytest -v
```

### Code Quality
```bash
# Lint with flake8
flake8

# Format with black
black .
```

## Architecture

### Application Structure

The app uses Flask's application factory pattern with blueprints:

- **`learnbetter.py`**: Entry point that creates the Flask app and registers shell context
- **`config.py`**: Configuration management using environment variables
- **`app/__init__.py`**: Application factory (`create_app()`) and extension initialization
- **`app/models.py`**: SQLAlchemy models (User, Article, Highlight, Topic, Tag, Task, etc.)

### Blueprints

1. **`app/auth`**: Authentication routes (login, register, password reset)
2. **`app/main`**: Core user-facing routes for reading, highlighting, and reviewing content
3. **`app/content`**: Content management routes
4. **`app/settings`**: User settings and preferences
5. **`app/api`**: RESTful API endpoints (articles, highlights, tags, users)
6. **`app/dotcom`**: Marketing/landing page routes
7. **`app/errors`**: Error handlers

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

- **Development**: SQLite (`app.db`)
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

### Browser Extensions

The `extensions/` directory contains browser extensions for Chrome, Firefox, and Safari that integrate with the API to save articles from the browser.

## Code Patterns

### API Authentication
The API uses token-based authentication:
- Token generation/validation in `app/api/auth.py` and `app/api/tokens.py`
- Basic auth for token endpoint, bearer token for API routes
- CSRF protection disabled for API blueprint

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

Tests use:
- In-memory SQLite database (`sqlite://`)
- `TestConfig` class for test-specific configuration
- Mock objects and patches for external services

## Environment Variables

Required for full functionality (see `.env.example`):
- `SECRET_KEY`: Flask session security
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`: OAuth
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_BUCKET`: S3 storage
- `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`: SendGrid email
- `SERVER_NAME`: For generating URLs in background tasks

## Common Gotchas

1. **PostgreSQL URL format**: The config automatically converts `postgres://` to `postgresql://` for SQLAlchemy compatibility
2. **Node.js required**: ReadabiliPy requires Node.js >=11.0.0 for the jsdom dependency
3. **Redis required**: Background tasks require Redis server to be running
4. **Migrations**: The app excludes ReadabiliPy and other directories from flake8 checks
5. **CSRF**: API routes are exempt from CSRF protection, but web routes require CSRF tokens
6. **Boolean comparisons**: Some files have flake8 exceptions for explicit boolean comparisons (E712) where they're intentional

## Code comments
Obvious comments are not necessary and should only be added sparingly and if its necessary to understand what is happening.

## Commit messages
Don't include attribution to Claude Code

## Working state
Explore the .local file for files of the following format
claude-progress-*.md
claude-tasks-*.json

The * should usually be some ticket number or task-name - sometimes this can be pulled from the branch name.

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
