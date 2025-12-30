#!/bin/bash
# Stop the Docker container

echo "🛑 Stopping blocklist analyzer container..."
docker-compose down
echo "✓ Container stopped"
