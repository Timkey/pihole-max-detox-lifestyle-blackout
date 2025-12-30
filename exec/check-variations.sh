#!/bin/bash
# Check for missing TLD variations (.org, .net, .ca, etc.)
# Uses DNS verification with caching

set -e

echo "🔎 Checking domain variations..."
docker exec -it pihole-blocklist-analyzer python3 /workspace/scripts/check_domain_variations.py "$@"
