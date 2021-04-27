web: flask db upgrade; gunicorn learnbetter:app npm start
worker: rq worker -u $REDIS_URL lurnby-tasks