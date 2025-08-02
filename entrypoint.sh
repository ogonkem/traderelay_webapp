#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! pg_isready -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER}; do
    sleep 2
done

echo "Waiting for RabbitMQ..."
while ! nc -z ${RABBITMQ_HOST} ${RABBITMQ_PORT}; do
    sleep 2
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@traderelay.com')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
EOF

echo "Collecting static files..."
python manage.py collectstatic --noinput

exec "$@"