#!/bin/bash

# Run migrations; If fail - stop the script
alembic upgrade head || exit 1

python -m gunicorn -w 1 -k uvicorn.workers.UvicornWorker app.asgi:fastapi_app --bind 0.0.0.0:8000 --timeout 300 --log-level debug

exec "$@"
