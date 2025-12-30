#!/bin/bash
# Analyze domains for health/behavioral hazards
# Generates recommendations in research/recommendations.json

set -e

echo "🔍 Analyzing domains..."
docker exec pihole-blocklist-analyzer python3 /workspace/scripts/analyze_domains.py "$@"

echo ""
echo "✓ Analysis complete. Check research/recommendations.json for suggestions."
