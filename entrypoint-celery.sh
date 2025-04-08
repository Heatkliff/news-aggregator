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

# Wait for web service to complete migrations
echo "Waiting for web service to complete setup..."
sleep 5
echo "Starting Celery worker..."

# Execute the command passed to docker
exec "$@"
