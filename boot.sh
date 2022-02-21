#!/bin/bash
source venv/bin/activate
flask db upgrade
npm install
exec gunicorn -b :5000 --certfile=./certs/cert.pem --keyfile=./certs/key.pem --access-logfile - --error-logfile - learnbetter:app