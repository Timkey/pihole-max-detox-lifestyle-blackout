#!/bin/bash
# Add verified TLD variations to category lists
# Automatically updates food.txt, cosmetics.txt, conglomerates.txt

set -e

echo "➕ Adding verified domain variations..."
docker exec -it pihole-blocklist-analyzer python3 /workspace/scripts/add_domain_variations.py "$@"

echo ""
echo "✓ Variations added. Review lists/ directory for changes."
