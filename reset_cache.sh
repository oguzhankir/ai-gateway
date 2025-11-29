#!/bin/bash

# Script to reset only cache (Redis) without touching the database

set -e

echo "🔄 Resetting Redis cache..."

# Check if Redis container is running
if docker-compose ps redis | grep -q "Up"; then
    echo "🗑️  Flushing Redis cache..."
    docker-compose exec -T redis redis-cli FLUSHDB
    echo "✅ Cache cleared!"
else
    echo "⚠️  Redis container is not running. Starting it..."
    docker-compose up -d redis
    sleep 2
    docker-compose exec -T redis redis-cli FLUSHDB
    echo "✅ Cache cleared!"
fi

echo ""
echo "📊 Cache statistics:"
docker-compose exec -T redis redis-cli INFO stats | grep -E "keys|memory"

