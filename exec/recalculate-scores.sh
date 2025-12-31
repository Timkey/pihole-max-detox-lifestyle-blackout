#!/bin/bash
# Recalculate enabler scores from existing JSON data
# Much faster than full reanalysis - doesn't re-scrape domains
#
# Usage:
#   ./recalculate-scores.sh          # Update production scores
#   ./recalculate-scores.sh --test   # Update test data scores

set -e

echo "🔢 Recalculating enabler scores..."
docker exec pihole-blocklist-analyzer python3 /workspace/scripts/recalculate_enabler_scores.py "$@"

echo ""
echo "✓ Scores recalculated. Run ./regenerate-reports.sh to update HTML/Markdown reports."
