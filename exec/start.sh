#!/bin/bash
# Start the Docker container with external DNS

set -e

echo "🚀 Starting blocklist analyzer container..."

# Check if Docker daemon is running
if ! docker ps &> /dev/null; then
    echo "⚠️  Docker is not running. Starting..."
    if command -v colima &> /dev/null; then
        colima start --mount /Volumes/mnt:w --mount-type virtiofs
    else
        echo "❌ Please start Docker manually"
        exit 1
    fi
fi

# Start container
docker-compose up -d

# Verify DNS configuration
echo ""
echo "✓ Container started"
echo ""
echo "DNS Configuration:"
docker exec pihole-blocklist-analyzer cat /etc/resolv.conf | grep nameserver

echo ""
echo "Ready! Run exec/full-workflow.sh or individual scripts in exec/"
