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
python manage.py migrate

# Collect static files (if needed)
# echo "Collecting static files..."
# python manage.py collectstatic --noinput

# Execute the command passed to docker
exec "$@"