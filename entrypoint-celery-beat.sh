#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! timeout 1 bash -c "</dev/tcp/$DB_HOST/$DB_PORT"; do
  sleep 0.1
done
echo "PostgreSQL is up and running"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! timeout 1 bash -c "</dev/tcp/$REDIS_HOST/$REDIS_PORT"; do
  sleep 0.1
done
echo "Redis is up and running"

# Wait for celery service to start
echo "Waiting for Celery worker to start..."
sleep 10
echo "Starting Celery beat..."

# Execute the command passed to docker
exec "$@"
