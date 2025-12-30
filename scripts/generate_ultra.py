#!/usr/bin/env python3
"""
Generate blackout-ultra.txt from category files
Combines all domains from food.txt, cosmetics.txt, and conglomerates.txt
Maintains category blocks and sorts domains alphabetically within each block
"""

import os
from pathlib import Path
import re

# Configuration
LISTS_DIR = Path(__file__).parent.parent / 'lists'
CATEGORY_FILES = ['food.txt', 'cosmetics.txt', 'conglomerates.txt']
OUTPUT_FILE = 'blackout-ultra.txt'
HEADER = """# BLACKOUT-ULTRA.TXT - MAX-DETOX-LIFESTYLE-BLACKOUT v1.0
# Master blocklist - includes ALL domains from all categories
#
# This is the "nuclear option" - blocks everything in one list
# Add this list to Pi-hole:
# https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/lists/blackout-ultra.txt
#
# CATEGORIES INCLUDED:
# - Food delivery & fast food (food.txt)
# - Beauty & cosmetics (cosmetics.txt)
# - Major conglomerates (conglomerates.txt)
"""


def extract_blocks_with_domains(filepath):
    """Extract blocks with their headers and domains from a file."""
    blocks = []
    current_block = None
    current_domains = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip()
                
                # Check if it's a block header (e.g., # --- SECTION NAME ---)
                if line.startswith('#') and '---' in line:
                    # Save previous block if it exists
                    if current_block and current_domains:
                        blocks.append({
                            'header': current_block,
                            'domains': sorted(set(current_domains), key=str.lower)
                        })
                    # Start new block
                    current_block = line
                    current_domains = []
                elif line and not line.startswith('#'):
                    # It's a domain
                    current_domains.append(line)
            
            # Save last block
            if current_block and current_domains:
                blocks.append({
                    'header': current_block,
                    'domains': sorted(set(current_domains), key=str.lower)
                })
    except FileNotFoundError:
        print(f"Warning: {filepath} not found, skipping...")
    
    return blocks


def generate_ultra_file():
    """Generate the blackout-ultra.txt file from all category files."""
    all_blocks = []
    total_domains = 0
    seen_domains = set()  # Track domains globally to detect duplicates
    duplicate_count = 0
    
    print(f"Generating {OUTPUT_FILE}...")
    print(f"Working directory: {LISTS_DIR}")
    
    # Extract blocks from each category file
    for category_file in CATEGORY_FILES:
        filepath = LISTS_DIR / category_file
        print(f"Reading {category_file}...")
        blocks = extract_blocks_with_domains(filepath)
        
        domain_count = sum(len(block['domains']) for block in blocks)
        print(f"  Found {len(blocks)} blocks with {domain_count} domains")
        total_domains += domain_count
        all_blocks.extend(blocks)
    
    # Check for cross-block duplicates
    print(f"\nChecking for duplicates across all blocks...")
    for block in all_blocks:
        for domain in block['domains']:
            domain_lower = domain.lower()
            if domain_lower in seen_domains:
                duplicate_count += 1
                print(f"  Duplicate found: {domain}")
            seen_domains.add(domain_lower)
    
    unique_domain_count = len(seen_domains)
    
    print(f"\nTotal blocks: {len(all_blocks)}")
    print(f"Total domains (with duplicates): {total_domains}")
    print(f"Unique domains: {unique_domain_count}")
    if duplicate_count > 0:
        print(f"⚠️  Duplicates found: {duplicate_count} (domains appear in multiple blocks)")
    else:
        print(f"✓ No duplicates detected")
    
    # Write to output file
    output_path = LISTS_DIR / OUTPUT_FILE
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(HEADER)
        
        for block in all_blocks:
            f.write('\n' + block['header'] + '\n')
            for domain in block['domains']:
                f.write(domain + '\n')
    
    print(f"\n✓ Successfully generated {OUTPUT_FILE}")
    print(f"  Output: {output_path}")
    print(f"  Output: {output_path}")


if __name__ == '__main__':
    generate_ultra_file()
