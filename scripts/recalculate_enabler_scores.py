#!/usr/bin/env python3
"""
Recalculate enabler scores using existing data without re-scraping websites.
This is much faster than full reanalysis since we already have related_domains.
"""

import json
import argparse
from pathlib import Path

# Paths
RESEARCH_DIR = Path(__file__).parent.parent / 'research'
DATA_DIR = RESEARCH_DIR / 'data'
TEST_DATA_DIR = DATA_DIR / 'test'

def recalculate_scores(category_file):
    """Recalculate enabler scores for a category using existing data."""
    
    file_path = DATA_DIR / category_file
    print(f"\n{'='*70}")
    print(f"Recalculating: {category_file}")
    print('='*70)
    
    # Load existing data
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    print(f"✓ Loaded {len(data)} domains")
    
    # Build domain scores map
    domain_scores = {item['domain']: item.get('risk_score', 0) for item in data}
    
    # Build reverse index: which domains are mentioned by others
    mentioned_by = {}
    for item in data:
        if item.get('accessible') and item.get('related_domains'):
            for related_domain in item.get('related_domains', []):
                if related_domain not in mentioned_by:
                    mentioned_by[related_domain] = []
                mentioned_by[related_domain].append({
                    'domain': item['domain'],
                    'risk_score': item.get('risk_score', 0)
                })
    
    print(f"✓ Built reverse index with {len(mentioned_by)} mentioned domains")
    
    # Recalculate enabler bonuses
    updates = 0
    facilitators_found = 0
    
    for item in data:
        high_risk_links = []
        facilitated_domains = []
        
        # RELATIONSHIP 1: Parent → Child (outbound links to high-risk)
        if item.get('accessible') and item.get('related_domains'):
            for related_domain in item.get('related_domains', []):
                related_score = domain_scores.get(related_domain, 0)
                if related_score >= 50:  # High risk threshold
                    high_risk_links.append({
                        'domain': related_domain,
                        'risk_score': related_score
                    })
        
        # RELATIONSHIP 2: Child → Parent (inbound links from others)
        if item['domain'] in mentioned_by:
            for mentioner in mentioned_by[item['domain']]:
                # Lower threshold (20) to catch more restaurants
                if mentioner['risk_score'] >= 20:
                    facilitated_domains.append(mentioner)
        
        # Calculate combined enabler bonus
        old_bonus = item.get('enabler_risk_bonus', 0)
        enabler_bonus = 0
        
        # Bonus from linking TO high-risk domains (Parent → Child)
        if high_risk_links:
            enabler_bonus += min(len(high_risk_links) * 5, 20)
        
        # Bonus from being linked BY other domains (Child → Parent)
        if facilitated_domains:
            # Each facilitated domain contributes: (its_risk_score / 10) points, max 30 total
            facilitator_bonus = min(sum(d['risk_score'] for d in facilitated_domains) // 10, 30)
            enabler_bonus += facilitator_bonus
            if facilitator_bonus > 0:
                facilitators_found += 1
        
        # Apply bonus if changed
        if enabler_bonus != old_bonus:
            old_score = item.get('risk_score', 0) - old_bonus  # Remove old bonus
            item['enabler_risk_bonus'] = enabler_bonus
            item['high_risk_links'] = high_risk_links
            item['facilitated_domains'] = facilitated_domains
            item['risk_score'] = min(old_score + enabler_bonus, 100)
            
            # Update justification
            if 'justification' not in item:
                item['justification'] = []
            
            # Clear old enabler justifications
            item['justification'] = [j for j in item['justification'] 
                                     if not j.startswith('ENABLER') and not j.startswith('FACILITATOR') 
                                     and not j.startswith('  →') and not j.startswith('  ←')]
            
            # Add new justifications
            if high_risk_links:
                item['justification'].insert(0, f"ENABLER (Outbound): Links to {len(high_risk_links)} high-risk domain(s) (+{min(len(high_risk_links) * 5, 20)} points)")
                for link in high_risk_links[:3]:
                    item['justification'].insert(1, f"  → Facilitates: {link['domain']} (risk: {link['risk_score']})")
            
            if facilitated_domains:
                facilitator_bonus = min(sum(d['risk_score'] for d in facilitated_domains) // 10, 30)
                item['justification'].insert(0, f"FACILITATOR (Inbound): Used by {len(facilitated_domains)} domain(s) (+{facilitator_bonus} points)")
                for domain in sorted(facilitated_domains, key=lambda x: x['risk_score'], reverse=True)[:3]:
                    item['justification'].insert(1, f"  ← Enables: {domain['domain']} (risk: {domain['risk_score']})")
            
            updates += 1
            if enabler_bonus > old_bonus:
                print(f"  ↑ {item['domain']}: +{enabler_bonus} (+{enabler_bonus - old_bonus} more)")
    
    # Save updated data
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Updated {updates} domains")
    print(f"✓ Found {facilitators_found} facilitator relationships (new!)")
    print(f"✓ Saved to {file_path.name}")
    
    return updates, facilitators_found


if __name__ == '__main__':
    print("\n╔═══════════════════════════════════════════════════════════════════╗")
    print("║  RECALCULATING ENABLER SCORES (no re-scraping needed)            ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Recalculate enabler scores using existing data'
    )
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Test mode: use separate test directories for data (doesn\'t affect production)'
    )
    
    args = parser.parse_args()
    
    # Set data directory based on test mode
    global DATA_DIR
    if args.test:
        DATA_DIR = TEST_DATA_DIR
        TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
        print(f"🧪 TEST MODE ENABLED")
        print(f"   Data: {DATA_DIR}\n")
    
    categories = [
        'food_delivery_data.json',
        'cosmetics_beauty_data.json',
        'conglomerates_data.json'
    ]
    
    total_updates = 0
    total_facilitators = 0
    
    for category in categories:
        updates, facilitators = recalculate_scores(category)
        total_updates += updates
        total_facilitators += facilitators
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print('='*70)
    print(f"  Total domains updated: {total_updates}")
    print(f"  Total facilitators found: {total_facilitators}")
    print(f"\n✅ All scores recalculated successfully!")
    print(f"\nNext step: Run python3 scripts/update_index.py to update summary.json")
