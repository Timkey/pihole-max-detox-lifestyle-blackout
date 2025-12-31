#!/bin/bash
# Analyze domains for health/behavioral hazards
# Generates recommendations in research/recommendations.json
#
# Usage:
#   ./analyze.sh                     # Default: 5 domains per category
#   ./analyze.sh --sample-size 20    # Analyze 20 domains per category
#   ./analyze.sh --all               # Analyze ALL domains (slow!)
#   ./analyze.sh --force             # Force reanalysis, ignore cache
#   ./analyze.sh --category food     # Only analyze food category
#   ./analyze.sh --all --force       # Full reanalysis of everything
#   ./analyze.sh --test              # Test mode: use research/data/test/ (doesn't affect production)

set -e

echo "🔍 Analyzing domains..."
docker exec pihole-blocklist-analyzer python3 /workspace/scripts/analyze_domains.py "$@"

echo ""
echo "✓ Analysis complete. Check research/recommendations.json for suggestions."
