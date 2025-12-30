#!/bin/bash
# Apply cached recommendations to blocklists
# Processes research/recommendations.json

set -e

echo "📝 Applying recommendations..."
docker exec -it pihole-blocklist-analyzer python3 /workspace/scripts/apply_recommendations.py "$@"

echo ""
echo "✓ Recommendations applied. Review changes before regenerating ultra list."
