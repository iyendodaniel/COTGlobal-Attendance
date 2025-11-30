#!/bin/bash
set -e

echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput --clear 2>/dev/null || true

echo "==> Starting Gunicorn server..."
exec gunicorn cotglobal_attendance.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 4 \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance

