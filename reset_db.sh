#!/bin/bash

# Script to reset only the database (keeps cache)

set -e

echo "⚠️  WARNING: This will DELETE ALL DATABASE DATA!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

echo ""
echo "🛑 Stopping backend..."
docker-compose stop backend

echo ""
echo "🗑️  Dropping and recreating database..."
docker-compose exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS ai_gateway;"
docker-compose exec -T postgres psql -U postgres -c "CREATE DATABASE ai_gateway;"

echo ""
echo "🚀 Starting backend..."
docker-compose start backend

echo ""
echo "⏳ Waiting for backend to be ready..."
sleep 5

echo ""
echo "🔄 Running database migrations..."
docker-compose exec -T backend alembic upgrade head

echo ""
echo "🔄 Initializing database (creating admin user)..."
docker-compose exec -T backend python3 -m app.scripts.init_db

echo ""
echo "✅ Database reset complete!"

