#!/usr/bin/env python3
"""
Smart domain variation checker with caching and parallel processing
Caches verified domains to avoid repeated DNS lookups
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
        print(f"✓ Cache saved to {self.cache_file}")
    
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
    
    def get_stats(self):
        """Get cache statistics."""
        return {
            'verified': len(self.cache['verified']),
            'not_found': len(self.cache['not_found']),
            'total_cached': len(self.cache['verified']) + len(self.cache['not_found'])
        }


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
        return True
    except:
        cache.mark_not_found(domain_lower)
        return False


def find_variations(base, current_tld, existing_domains, cache):
    """Find valid TLD variations of a base domain."""
    found_variations = []
    dns_checks = 0
    cache_hits = 0
    
    for tld in COMMON_TLDS:
        if tld == current_tld:
            continue
        
        test_domain = f"{base}.{tld}"
        test_www = f"www.{test_domain}"
        
        # Skip if already in existing lists
        if test_domain.lower() in existing_domains:
            continue
        
        # Check if exists (uses cache internally)
        was_cached = cache.is_verified(test_domain) or cache.is_not_found(test_domain)
        
        if domain_exists(test_domain, cache):
            found_variations.append(test_domain)
            
            # Check www variant
            if test_www.lower() not in existing_domains:
                was_www_cached = cache.is_verified(test_www) or cache.is_not_found(test_www)
                if domain_exists(test_www, cache):
                    found_variations.append(test_www)
                if not was_www_cached:
                    dns_checks += 1
        
        if was_cached:
            cache_hits += 1
        else:
            dns_checks += 1
            time.sleep(0.05)  # Rate limit only for actual DNS queries
    
    return found_variations, dns_checks, cache_hits


def scan_file_for_variations(filepath, cache, workers=DEFAULT_WORKERS):
    """Scan a blocklist file and find missing domain variations with parallel processing."""
    print(f"\n{'='*60}")
    print(f"Scanning: {filepath.name}")
    print(f"{'='*60}")
    
    existing_domains = set()
    base_domains = set()
    
    # Collect existing domains
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                existing_domains.add(line.lower())
                result = extract_base_domain(line)
                if result:
                    base, tld = result
                    base_domains.add((base, tld))
    
    print(f"Found {len(existing_domains)} existing domains")
    print(f"Found {len(base_domains)} unique bases to check")
    print(f"⚡ Using {workers} parallel workers\n")
    
    # Check for variations in parallel
    new_domains = []
    checked = set()
    total_dns_checks = 0
    total_cache_hits = 0
    
    def check_base_domain(base_tld_tuple):
        """Check a single base domain for variations."""
        base, tld = base_tld_tuple
        variations, dns_checks, cache_hits = find_variations(base, tld, existing_domains, cache)
        return base, variations, dns_checks, cache_hits
    
    # Process base domains in parallel
    unique_bases = [(base, tld) for base, tld in sorted(base_domains) if base not in checked]
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(check_base_domain, base_tld): base_tld for base_tld in unique_bases}
        
        completed = 0
        for future in as_completed(futures):
            base_tld = futures[future]
            base, _ = base_tld
            checked.add(base)
            completed += 1
            
            try:
                base_name, variations, dns_checks, cache_hits = future.result()
                new_domains.extend(variations)
                total_dns_checks += dns_checks
                total_cache_hits += cache_hits
                
                if variations:
                    print(f"  [{completed}/{len(unique_bases)}] {base_name}.* ✓ Found {len(variations)} new ({dns_checks} DNS, {cache_hits} cached)")
                elif completed % 10 == 0:
                    print(f"  [{completed}/{len(unique_bases)}] Progress...")
            except Exception as e:
                print(f"  {base}.* ✗ Error: {e}")
        else:
            print(f"✗ None ({dns_checks} DNS, {cache_hits} cached)")
    
    print(f"\n📊 Statistics:")
    print(f"   New domains found: {len(new_domains)}")
    print(f"   DNS lookups performed: {total_dns_checks}")
    print(f"   Cache hits: {total_cache_hits}")
    print(f"   Time saved: ~{total_cache_hits * 0.05:.1f}s")
    
    return new_domains


def main():
    """Main function to scan all category files."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Check for domain variations with parallel processing')
    parser.add_argument('--workers', type=int, default=DEFAULT_WORKERS, help='Number of parallel workers')
    args = parser.parse_args()
    
    category_files = ['food.txt', 'cosmetics.txt', 'conglomerates.txt']
    
    # Initialize cache (in lists directory)
    cache = DomainCache(LISTS_DIR / CACHE_FILE)
    stats = cache.get_stats()
    
    print("SMART DOMAIN VARIATION SCANNER (with caching and parallel processing)")
    print(f"Workers: {args.workers}")
    print(f"Cache stats: {stats['verified']} verified, {stats['not_found']} not found")
    print("="*60)
    
    all_findings = {}
    
    for filename in category_files:
        filepath = LISTS_DIR / filename
        if not filepath.exists():
            print(f"⚠️  {filename} not found, skipping...")
            continue
        
        new_domains = scan_file_for_variations(filepath, cache, workers=args.workers)
        
        if new_domains:
            all_findings[filename] = new_domains
    
    # Save cache
    cache.save_cache()
    
    # Print summary
    print(f"\n{'='*60}")
    print("OVERALL SUMMARY")
    print(f"{'='*60}")
    
    if all_findings:
        total_new = sum(len(domains) for domains in all_findings.values())
        print(f"Total new domains found: {total_new}\n")
        
        for filename, domains in all_findings.items():
            print(f"\n{filename}: {len(domains)} new domains")
            for domain in sorted(domains)[:10]:  # Show first 10
                print(f"  - {domain}")
            if len(domains) > 10:
                print(f"  ... and {len(domains) - 10} more")
        
        print("\n" + "="*60)
        print("To add these domains, run: python3 add_domain_variations.py")
    else:
        print("✓ All domain variations already covered!")
    
    # Show updated cache stats
    final_stats = cache.get_stats()
    print(f"\nFinal cache: {final_stats['verified']} verified, {final_stats['not_found']} not found")


if __name__ == '__main__':
    main()
