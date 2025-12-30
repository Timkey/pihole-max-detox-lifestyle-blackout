#!/usr/bin/env python3
"""
Apply Recommendations to Blocklists
Processes cached recommendations for domain additions and removals
"""

import json
from pathlib import Path
from datetime import datetime

# Configuration
LISTS_DIR = Path(__file__).parent.parent / 'lists'
RESEARCH_DIR = Path(__file__).parent.parent / 'research'
RECOMMENDATIONS_FILE = 'recommendations.json'

CATEGORY_MAP = {
    'Food & Delivery': 'food.txt',
    'Cosmetics & Beauty': 'cosmetics.txt',
    'Conglomerates': 'conglomerates.txt'
}


def load_recommendations():
    """Load recommendations from file."""
    rec_file = RESEARCH_DIR / RECOMMENDATIONS_FILE
    if not rec_file.exists():
        print(f"❌ No recommendations file found: {rec_file}")
        print("   Run: python3 analyze_domains.py first")
        return None
    
    with open(rec_file, 'r') as f:
        return json.load(f)


def save_recommendations(recommendations):
    """Save updated recommendations."""
    rec_file = RESEARCH_DIR / RECOMMENDATIONS_FILE
    recommendations['last_updated'] = datetime.now().isoformat()
    with open(rec_file, 'w') as f:
        json.dump(recommendations, f, indent=2)


def load_blocklist(category_file):
    """Load domains from a blocklist file."""
    filepath = LISTS_DIR / category_file
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    domains = set()
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            domains.add(stripped.lower())
    
    return lines, domains


def add_domains_to_list(category_file, domains_to_add):
    """Add domains to a blocklist file."""
    filepath = LISTS_DIR / category_file
    lines, existing_domains = load_blocklist(category_file)
    
    # Find where to insert (end of file, before trailing newlines)
    insert_index = len(lines)
    while insert_index > 0 and not lines[insert_index - 1].strip():
        insert_index -= 1
    
    # Prepare new domains
    new_lines = []
    for domain in domains_to_add:
        if domain.lower() not in existing_domains:
            new_lines.append(f"{domain}\n")
            # Add www variant
            www_domain = f"www.{domain}"
            if www_domain.lower() not in existing_domains:
                new_lines.append(f"{www_domain}\n")
    
    if not new_lines:
        return 0
    
    # Sort new lines
    new_lines.sort(key=str.lower)
    
    # Insert into file
    lines = lines[:insert_index] + new_lines + lines[insert_index:]
    
    # Write back
    with open(filepath, 'w') as f:
        f.writelines(lines)
    
    return len(new_lines)


def remove_domains_from_list(category_file, domains_to_remove):
    """Remove domains from a blocklist file."""
    filepath = LISTS_DIR / category_file
    lines, existing_domains = load_blocklist(category_file)
    
    # Create set of domains to remove (including www variants)
    remove_set = set()
    for domain in domains_to_remove:
        remove_set.add(domain.lower())
        remove_set.add(f"www.{domain}".lower())
    
    # Filter lines
    original_count = len(lines)
    new_lines = []
    removed_count = 0
    
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            if stripped.lower() in remove_set:
                removed_count += 1
                continue  # Skip this line
        new_lines.append(line)
    
    # Write back
    with open(filepath, 'w') as f:
        f.writelines(new_lines)
    
    return removed_count


def show_recommendations(recommendations):
    """Display recommendations for review."""
    print("\n" + "="*60)
    print("PENDING RECOMMENDATIONS")
    print("="*60)
    
    # Additions
    pending_additions = [r for r in recommendations['additions'] if r['status'] == 'pending']
    if pending_additions:
        print(f"\n✚ ADDITIONS ({len(pending_additions)}):\n")
        for rec in pending_additions:
            print(f"  [{rec['category']}] {rec['domain']}")
            print(f"     Reason: {rec['reason']}")
            if rec.get('source'):
                print(f"     Source: {rec['source']}")
            print()
    
    # Removals
    pending_removals = [r for r in recommendations['removals'] if r['status'] == 'pending']
    if pending_removals:
        print(f"\n✖ REMOVALS ({len(pending_removals)}):\n")
        for rec in pending_removals:
            print(f"  [{rec['category']}] {rec['domain']}")
            print(f"     Reason: {rec['reason']}")
            print(f"     Risk Score: {rec['risk_score']}/100")
            print()
    
    return len(pending_additions), len(pending_removals)


def apply_additions(recommendations, dry_run=False):
    """Apply addition recommendations."""
    pending = [r for r in recommendations['additions'] if r['status'] == 'pending']
    
    if not pending:
        print("\n✓ No additions to apply")
        return 0
    
    print(f"\n{'='*60}")
    print(f"APPLYING ADDITIONS{' (DRY RUN)' if dry_run else ''}")
    print(f"{'='*60}\n")
    
    # Group by category
    by_category = {}
    for rec in pending:
        category = rec['category']
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(rec['domain'])
    
    total_added = 0
    
    for category, domains in by_category.items():
        category_file = CATEGORY_MAP.get(category)
        if not category_file:
            print(f"⚠️  Unknown category: {category}")
            continue
        
        print(f"Processing {category} ({len(domains)} domains)...")
        
        if not dry_run:
            added_count = add_domains_to_list(category_file, domains)
            print(f"  ✓ Added {added_count} entries to {category_file}")
            total_added += added_count
            
            # Mark as applied
            for rec in recommendations['additions']:
                if rec['status'] == 'pending' and rec['domain'] in domains:
                    rec['status'] = 'applied'
                    rec['applied_at'] = datetime.now().isoformat()
        else:
            print(f"  → Would add {len(domains)} domains to {category_file}")
            for domain in domains[:3]:
                print(f"     - {domain}")
            if len(domains) > 3:
                print(f"     ... and {len(domains) - 3} more")
    
    return total_added


def apply_removals(recommendations, dry_run=False):
    """Apply removal recommendations."""
    pending = [r for r in recommendations['removals'] if r['status'] == 'pending']
    
    if not pending:
        print("\n✓ No removals to apply")
        return 0
    
    print(f"\n{'='*60}")
    print(f"APPLYING REMOVALS{' (DRY RUN)' if dry_run else ''}")
    print(f"{'='*60}\n")
    
    # Group by category
    by_category = {}
    for rec in pending:
        category = rec['category']
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(rec['domain'])
    
    total_removed = 0
    
    for category, domains in by_category.items():
        category_file = CATEGORY_MAP.get(category)
        if not category_file:
            print(f"⚠️  Unknown category: {category}")
            continue
        
        print(f"Processing {category} ({len(domains)} domains)...")
        
        if not dry_run:
            removed_count = remove_domains_from_list(category_file, domains)
            print(f"  ✓ Removed {removed_count} entries from {category_file}")
            total_removed += removed_count
            
            # Mark as applied
            for rec in recommendations['removals']:
                if rec['status'] == 'pending' and rec['domain'] in domains:
                    rec['status'] = 'applied'
                    rec['applied_at'] = datetime.now().isoformat()
        else:
            print(f"  → Would remove {len(domains)} domains from {category_file}")
            for domain in domains[:3]:
                print(f"     - {domain}")
            if len(domains) > 3:
                print(f"     ... and {len(domains) - 3} more")
    
    return total_removed


def main():
    """Main function."""
    import sys
    
    print("APPLY RECOMMENDATIONS")
    print("Process domain additions and removals based on analysis\n")
    
    # Load recommendations
    recommendations = load_recommendations()
    if not recommendations:
        return
    
    # Show what will be done
    addition_count, removal_count = show_recommendations(recommendations)
    
    if addition_count == 0 and removal_count == 0:
        print("✓ No pending recommendations")
        return
    
    # Check for flags
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    skip_prompt = '--yes' in sys.argv or '-y' in sys.argv
    additions_only = '--additions' in sys.argv
    removals_only = '--removals' in sys.argv
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made")
    
    if not skip_prompt and not dry_run:
        print("\n" + "="*60)
        response = input("Apply these recommendations? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Cancelled.")
            return
    
    # Apply recommendations
    total_added = 0
    total_removed = 0
    
    if not removals_only:
        total_added = apply_additions(recommendations, dry_run)
    
    if not additions_only:
        total_removed = apply_removals(recommendations, dry_run)
    
    # Save updated recommendations
    if not dry_run:
        save_recommendations(recommendations)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if dry_run:
        print(f"Would add: {addition_count} domains")
        print(f"Would remove: {removal_count} domains")
        print("\nRun without --dry-run to apply changes")
    else:
        print(f"✓ Added: {total_added} entries")
        print(f"✓ Removed: {total_removed} entries")
        
        if total_added > 0 or total_removed > 0:
            print(f"\nNext steps:")
            print(f"1. Review changes in lists/")
            print(f"2. Run: python3 generate_ultra.py")
            print(f"3. Commit and push changes")


if __name__ == '__main__':
    main()
