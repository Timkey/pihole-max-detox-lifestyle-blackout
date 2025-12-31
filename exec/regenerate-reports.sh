#!/bin/bash
# Regenerate HTML and Markdown reports from existing JSON data
# Use after updating JSON files or recalculating scores
#
# Usage:
#   ./regenerate-reports.sh          # Regenerate production reports
#   ./regenerate-reports.sh --test   # Regenerate test reports

set -e

echo "📊 Regenerating reports from JSON data..."
docker exec pihole-blocklist-analyzer python3 /workspace/scripts/regenerate_reports.py "$@"

echo ""
echo "✓ Reports regenerated. Check research/reports/ for updated files."
