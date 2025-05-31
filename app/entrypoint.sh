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
wait-for-it --service "$REDIS_LINK"
wait-for-it --service "$RABBIT_LINK"

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

elif [ "$1" == 'worker-beat' ]; then
   echo "Starting Celery beat..."
   exec celery -A celery_app beat -l info

elif [ "$1" == 'worker-scraper-raw-data' ]; then
   echo "Starting Raw Data Scraper Celery worker..."
   exec celery -A celery_app worker -Q scraper.raw-data -l info --concurrency=1 --prefetch-multiplier=1

else
   echo 'No valid argument provided, defaulting to infinite sleep...'
   exec sleep infinity
fi
