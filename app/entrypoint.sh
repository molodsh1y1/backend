#!/usr/bin/env bash
set -e

trap 'echo "Stopping container..."; exit 0' SIGTERM

prepare_app() {
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
    echo "Applying migrations..."
    python manage.py migrate
}

wait-for-it --service "$POSTGRES_LINK"

if [ "$1" == 'backend' ]; then
   prepare_app

   echo "Starting Gunicorn in server mode with 4 threads workers..."

   exec gunicorn wsgi:application \
        --workers 4 \
        --threads 16 \
        --worker-class gthread \
        --bind 0.0.0.0:8000 \
        --timeout 600 \
        --log-level info \
        --graceful-timeout 600

elif [ "$1" == 'backend-local' ]; then
   prepare_app

   echo "Starting Gunicorn in local development mode with 1 sync worker..."

   exec gunicorn wsgi:application \
       --workers 1 \
       --reload \
       --worker-class sync \
       --bind 0.0.0.0:8000 \
       --timeout 600 \
       --log-level info \
       --graceful-timeout 600

elif [ "$1" == 'websocket' ]; then
   echo "Websocket startup..."

   exec daphne ws:application \
        -b 0.0.0.0 -p 8000

elif [ "$1" == 'test' ]; then
   exec pytest

else
   echo 'No valid argument provided, defaulting to infinite sleep...'
   exec sleep infinity
fi
