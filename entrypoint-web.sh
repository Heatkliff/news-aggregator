#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! timeout 1 bash -c "</dev/tcp/$DB_HOST/$DB_PORT"; do
  sleep 0.1
done
echo "PostgreSQL is up and running"

# Apply database migrations
echo "Applying database migrations..."
python manage.py makemigrations
python manage.py migrate

# Added superuser
echo "Creating superuser..."
python manage.py shell << END
from django.contrib.auth import get_user_model
import os

User = get_user_model()

username = os.environ.get("SP_USER_LOGIN")
password = os.environ.get("SP_USER_PASS")

if username and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email="", password=password)
        print(f"Superuser '{username}' created.")
    else:
        print(f"ℹSuperuser '{username}' already exists.")
else:
    print("SP_USER_LOGIN or SP_USER_PASS not set.")
END

# Collect static files (if needed)
# echo "Collecting static files..."
# python manage.py collectstatic --noinput

# Execute the command passed to docker
exec "$@"
