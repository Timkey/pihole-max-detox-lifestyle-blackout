#!/usr/bin/env python3
"""
Add verified domain variations to blocklists (with caching and parallel processing)
Automatically appends new domains, using cache to avoid redundant DNS lookups
"""

import socket
import json
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
LISTS_DIR = Path(__file__).parent.parent / 'lists'
CACHE_FILE = '.domain_cache.json'
COMMON_TLDS = [
    'org', 'net', 'co', 'io', 'ai', 'app',
    'co.uk', 'ca', 'us', 'uk', 'biz', 'info', 'dev',
    'co.ca'
]
DEFAULT_WORKERS = 8


class DomainCache:
    """Manages cached domain verification results."""
    
    def __init__(self, cache_file):
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
    
    def _load_cache(self):
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    print(f"✓ Loaded cache with {len(data.get('verified', {}))} verified domains")
                    return data
            except:
                print("⚠️  Cache file corrupted, starting fresh")
        return {'verified': {}, 'not_found': {}, 'last_updated': None}
    
    def save_cache(self):
        """Save cache to file."""
        self.cache['last_updated'] = datetime.now().isoformat()
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def is_verified(self, domain):
        """Check if domain is in verified cache."""
        return domain.lower() in self.cache['verified']
    
    def is_not_found(self, domain):
        """Check if domain was previously checked and not found."""
        return domain.lower() in self.cache['not_found']
    
    def mark_verified(self, domain):
        """Mark domain as verified."""
        self.cache['verified'][domain.lower()] = datetime.now().isoformat()
    
    def mark_not_found(self, domain):
        """Mark domain as not found."""
        self.cache['not_found'][domain.lower()] = datetime.now().isoformat()


def extract_base_domain(domain):
    """Extract the base name without TLD and subdomain."""
    parts = domain.split('.')
    
    # Skip www, api, drive subdomains
    if parts[0] in {'www', 'api', 'drive'}:
        return None
    
    # Handle multi-part TLDs like .co.uk
    if len(parts) >= 3 and parts[-2] in {'co'}:
        base = '.'.join(parts[:-2])
        tld = '.'.join(parts[-2:])
        return base, tld
    elif len(parts) >= 2:
        base = '.'.join(parts[:-1])
        tld = parts[-1]
        return base, tld
    
    return None


def domain_exists(domain, cache):
    """Check if a domain resolves via DNS lookup, using cache."""
    domain_lower = domain.lower()
    
    # Check cache first
    if cache.is_verified(domain_lower):
        return True
    
    if cache.is_not_found(domain_lower):
        return False
    
    # Not in cache, do DNS lookup
    try:
        socket.gethostbyname(domain)
        cache.mark_verified(domain_lower)
        time.sleep(0.05)  # Rate limit
        return True
    except:
        cache.mark_not_found(domain_lower)
        return False


def add_variations_to_file(filepath, cache, workers=DEFAULT_WORKERS):
    """Add TLD variations to a blocklist file with parallel processing."""
    print(f"\n{'='*60}")
    print(f"Processing: {filepath.name}")
    print(f"{'='*60}")
    
    # Read existing domains and structure
    existing_domains = set()
    blocks = {}
    current_block = None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line_stripped = line.strip()
            
            if line_stripped.startswith('#') and '---' in line_stripped:
                current_block = line_stripped
                if current_block not in blocks:
                    blocks[current_block] = []
            elif line_stripped and not line_stripped.startswith('#'):
                existing_domains.add(line_stripped.lower())
                if current_block:
                    blocks[current_block].append(line_stripped)
    
    print(f"Found {len(existing_domains)} existing domains in {len(blocks)} blocks")
    print(f"⚡ Using {workers} parallel workers")
    
    # Find new variations using parallel processing
    new_domains_by_block = {}
    checked_bases = set()
    total_dns = 0
    total_cache = 0
    
    def check_domain_for_block(block_domain_tuple):
        """Check a domain for variations (parallel worker function)."""
        block_name, domain = block_domain_tuple
        
        # Skip subdomains
        if domain.startswith('www.') or domain.startswith('api.') or domain.startswith('drive.'):
            return block_name, [], 0, 0
        
        result = extract_base_domain(domain)
        if not result:
            return block_name, [], 0, 0
        
        base, current_tld = result
        
        block_variations = []
        dns_lookups = 0
        cache_hits = 0
        
        for tld in COMMON_TLDS:
            if tld == current_tld:
                continue
            
            test_domain = f"{base}.{tld}"
            test_www = f"www.{test_domain}"
            
            # Skip if already exists
            if test_domain.lower() in existing_domains:
                continue
            
            # Check with cache
            was_cached = cache.is_verified(test_domain) or cache.is_not_found(test_domain)
            
            if domain_exists(test_domain, cache):
                block_variations.append(test_domain)
                
                # Add www variant
                if test_www.lower() not in existing_domains:
                    was_www_cached = cache.is_verified(test_www) or cache.is_not_found(test_www)
                    if domain_exists(test_www, cache):
                        block_variations.append(test_www)
                    if not was_www_cached:
                        dns_lookups += 1
            
            if was_cached:
                cache_hits += 1
            else:
                dns_lookups += 1
        
        return block_name, block_variations, dns_lookups, cache_hits
    
    # Prepare work items
    work_items = []
    total_dns = 0
    total_cache = 0
    for block_name, domains in blocks.items():
        new_domains_by_block[block_name] = []
        for domain in domains:
            result = extract_base_domain(domain)
            if result:
                base, _ = result
                if base not in checked_bases:
                    checked_bases.add(base)
                    work_items.append((block_name, domain))
    
    # Process in parallel
    print(f"Checking {len(work_items)} base domains...")
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(check_domain_for_block, item): item for item in work_items}
        
        completed = 0
        for future in as_completed(futures):
            completed += 1
            try:
                block_name, variations, dns, cache_count = future.result()
                if variations:
                    new_domains_by_block[block_name].extend(variations)
                    print(f"  [{completed}/{len(work_items)}] ✓ {len(variations)} new ({dns} DNS, {cache_count} cached)")
                elif completed % 20 == 0:
                    print(f"  [{completed}/{len(work_items)}] Progress...")
                
                total_dns += dns
                total_cache += cache_count
            except Exception as e:
                print(f"  Error: {e}")
    
    # Count new domains
    total_new = sum(len(domains) for domains in new_domains_by_block.values())
    
    if total_new == 0:
        print(f"\n✓ No new variations found")
        return 0
    
    print(f"\nFound {total_new} new domains ({total_dns} DNS lookups, {total_cache} cache hits)")
    
    # Update file
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    current_block = None
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        line_stripped = line.strip()
        
        if line_stripped.startswith('#') and '---' in line_stripped:
            current_block = line_stripped
        elif line_stripped and not line_stripped.startswith('#'):
            # Check if this is the last domain in the block
            is_last_in_block = (
                i + 1 >= len(lines) or
                not lines[i + 1].strip() or
                lines[i + 1].strip().startswith('#')
            )
            
            if is_last_in_block and current_block and current_block in new_domains_by_block:
                new_domains = new_domains_by_block[current_block]
                if new_domains:
                    for new_domain in sorted(set(new_domains), key=str.lower):
                        new_lines.append(f"{new_domain}\n")
                    new_domains_by_block[current_block] = []  # Clear
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✓ Added {total_new} domains to {filepath.name}")
    return total_new


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Add domain variations with parallel processing')
    parser.add_argument('--workers', type=int, default=DEFAULT_WORKERS, help='Number of parallel workers')
    args = parser.parse_args()
    
    category_files = ['food.txt', 'cosmetics.txt', 'conglomerates.txt']
    
    # Initialize cache (in lists directory)
    cache = DomainCache(LISTS_DIR / CACHE_FILE)
    
    print(f"AUTOMATIC DOMAIN VARIATION ADDER (with caching and parallel processing)")
    print(f"Workers: {args.workers}")
    print(f"Adding verified TLD variations to all blocklists\n")
    
    total_added = 0
    
    for filename in category_files:
        filepath = LISTS_DIR / filename
        if not filepath.exists():
            print(f"⚠️  {filename} not found, skipping...")
            continue
        
        added = add_variations_to_file(filepath, cache, workers=args.workers)
        total_added += added
    
    # Save cache
    cache.save_cache()
    
    print(f"\n{'='*60}")
    print(f"COMPLETE")
    print(f"{'='*60}")
    print(f"Total domains added: {total_added}")
    
    if total_added > 0:
        print(f"\nNext steps:")
        print(f"1. Run: python3 generate_ultra.py (update blackout-ultra.txt)")
        print(f"2. Run: python3 analyze_domains.py (update statistics)")
        
        # Auto-update statistics
        try:
            import subprocess
            print(f"\nAuto-updating summary statistics...")
            analyze_script = Path(__file__).parent / 'analyze_domains.py'
            result = subprocess.run(['python3', str(analyze_script), '--update-stats-only'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✓ Statistics updated")
        except:
            pass


if __name__ == '__main__':
    main()
