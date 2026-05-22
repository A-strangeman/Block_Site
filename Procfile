web: gunicorn -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:$PORT --workers 3
worker: rq worker default -u $REDIS_URL
