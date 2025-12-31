#!/usr/bin/env python3
"""
Update index.html with latest statistics from summary.json
"""

import json
import re
from pathlib import Path

def update_index_stats():
    """Embed latest summary.json data into index.html"""
    
    # Paths
    script_dir = Path(__file__).parent
    workspace_root = script_dir.parent
    summary_path = workspace_root / 'research' / 'data' / 'summary.json'
    index_path = workspace_root / 'index.html'
    
    # Load summary data
    if not summary_path.exists():
        print(f"❌ Summary file not found: {summary_path}")
        return False
    
    with open(summary_path, 'r') as f:
        summary_data = json.load(f)
    
    print(f"✓ Loaded summary data: {summary_data['total_domains']} domains")
    
    # Load index.html
    if not index_path.exists():
        print(f"❌ Index file not found: {index_path}")
        return False
    
    with open(index_path, 'r') as f:
        html_content = f.read()
    
    # Create new embedded data block
    stats_json = json.dumps(summary_data, indent=2)
    new_data_block = f"""        const statsData = {stats_json};"""
    
    # Replace the statsData definition using regex
    pattern = r'const statsData = \{[^}]*(?:\{[^}]*\}[^}]*)*\};'
    
    if re.search(pattern, html_content):
        html_content = re.sub(pattern, new_data_block.strip(), html_content)
        
        # Write back to file
        with open(index_path, 'w') as f:
            f.write(html_content)
        
        print(f"✓ Updated {index_path} with latest statistics")
        print(f"  - Total domains: {summary_data['total_domains']}")
        print(f"  - Accessible: {summary_data['accessible_count']} ({summary_data['access_rate']}%)")
        print(f"  - Avg risk: {summary_data['avg_risk_score']}")
        print(f"  - High risk: {summary_data['high_risk_count']}")
        return True
    else:
        print("❌ Could not find statsData definition in index.html")
        return False

if __name__ == '__main__':
    success = update_index_stats()
    exit(0 if success else 1)
