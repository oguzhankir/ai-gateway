#!/bin/bash

set -e

echo "Waiting for database to be ready..."
until pg_isready -h postgres -U postgres; do
  sleep 1
done

echo "Running database migrations..."
alembic upgrade head

echo "Initializing database..."
python scripts/init_db.py

echo "Testing provider connections..."
python scripts/test_providers.py

echo "AI Gateway initialization complete!"

