set dotenv-load

client_dir := "client"

# List available recipes
default:
    @just --list

# Install Python and Node dependencies
install:
    pip install -r requirements.txt
    cd {{client_dir}} && npm install

# Build frontend assets with Vite
build:
    @echo "Building assets with Vite..."
    cd {{client_dir}} && npm run build
    @echo "Build complete!"

# Run dev server (Redis, RQ, Vite, Flask)
[no-exit-message]
serve:
    #!/usr/bin/env bash
    RQ_PID=""
    VITE_PID=""

    cleanup() {
        echo ""
        echo "Shutting down..."
        { kill $VITE_PID $RQ_PID 2>/dev/null; wait $VITE_PID $RQ_PID 2>/dev/null; redis-cli shutdown; } 2>/dev/null
        echo "Done."
    }
    trap cleanup EXIT

    # Clean up any orphans from previous runs
    pkill -f "rq worker" 2>/dev/null || true
    redis-cli shutdown 2>/dev/null || true
    sleep 1

    echo "Starting Redis server..."
    redis-server --daemonize yes
    sleep 2

    echo "Starting RQ worker..."
    rq worker lurnby-tasks &
    RQ_PID=$!

    echo "Starting Vite dev server..."
    cd {{client_dir}} && npm start &
    VITE_PID=$!
    sleep 2

    echo "Starting Flask server..."
    FLASK_DEBUG=1 flask run

# Run production server (builds assets first)
[no-exit-message]
serve-prod: build
    #!/usr/bin/env bash
    RQ_PID=""

    cleanup() {
        echo ""
        echo "Shutting down..."
        { kill $RQ_PID 2>/dev/null; wait $RQ_PID 2>/dev/null; redis-cli shutdown; } 2>/dev/null
        echo "Done."
    }
    trap cleanup EXIT

    pkill -f "rq worker" 2>/dev/null || true
    redis-cli shutdown 2>/dev/null || true
    sleep 1

    echo "Starting Redis server..."
    redis-server --daemonize yes
    sleep 2

    echo "Starting RQ worker..."
    rq worker lurnby-tasks &
    RQ_PID=$!

    echo "Starting Flask server in production mode..."
    FLASK_DEBUG=0 flask run

# Format all code (Python + client)
format: format-client format-python

# Format Python files with Black
format-python:
    @echo "Running Black formatter on Python files..."
    black .
    @echo "Python formatting complete!"

# Format client files with Biome
format-client:
    @echo "Running Biome formatter on client files..."
    cd {{client_dir}} && npm run format
    @echo "Client formatting complete!"

# Lint all code (Python + client)
lint: lint-client lint-python

# Lint Python files with Flake8
lint-python:
    @echo "Running Flake8 linter on Python files..."
    flake8 --count --select=E9,F63,F7,F82 --show-source --statistics
    @echo "Checking for style warnings..."
    flake8 --exit-zero
    @echo "Python linting complete!"

# Lint client files with Biome
lint-client:
    @echo "Running Biome linter on client files..."
    cd {{client_dir}} && npm run lint
    @echo "Client linting complete!"

# Run all tests (Python + client)
test: test-python test-client

# Run Python tests with pytest
test-python:
    @echo "Running Python tests with pytest..."
    pytest --durations=0 --durations-min=0.29
    @echo "Python tests complete!"

# Run client tests with Vitest
test-client:
    @echo "Running frontend tests with Vitest..."
    cd {{client_dir}} && npm run test:run
    @echo "Frontend tests complete!"

# Remove build artifacts
clean:
    rm -rf app/static/dist
    rm -rf {{client_dir}}/node_modules/.vite
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
