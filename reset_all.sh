#!/bin/bash

# Script to completely reset the AI Gateway:
# - Stops all containers
# - Removes all containers
# - Removes all volumes (database, Redis, etc.)
# - Removes all networks
# - Rebuilds and starts fresh

set -e

echo "⚠️  WARNING: This will DELETE ALL DATA including database, cache, and volumes!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

echo ""
echo "🛑 Stopping containers..."
docker-compose down

echo ""
echo "🗑️  Removing volumes..."
docker-compose down -v

echo ""
echo "🧹 Cleaning up Docker resources..."
docker system prune -f

echo ""
echo "📦 Rebuilding containers..."
docker-compose build --no-cache

echo ""
echo "🚀 Starting fresh containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "🔄 Running database migrations..."
docker-compose exec -T backend alembic upgrade head

echo ""
echo "✅ Reset complete! All data has been cleared."
echo ""
echo "📊 Check service status:"
docker-compose ps

