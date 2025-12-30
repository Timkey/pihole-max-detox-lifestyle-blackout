#!/bin/bash
# Regenerate the master blackout-ultra.txt list
# Combines all category files with deduplication

set -e

echo "🔄 Regenerating blackout-ultra.txt..."
docker exec -it pihole-blocklist-analyzer python3 scripts/generate_ultra.py "$@"

echo ""
echo "✓ Master list regenerated. Ready to commit and push."
