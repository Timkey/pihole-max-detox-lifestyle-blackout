#!/usr/bin/env python3
"""
Update index.html with latest statistics from summary.json and category data
"""

import json
import re
from pathlib import Path

def calculate_category_stats(data):
    """Calculate statistics for a category's data"""
    accessible = [d for d in data if d.get('accessible')]
    avg_risk = sum(d.get('risk_score', 0) for d in accessible) / len(accessible) if accessible else 0.0
    high_risk = len([d for d in accessible if d.get('risk_score', 0) >= 50])
    
    return {
        'total': len(data),
        'accessible': len(accessible),
        'access_rate': round((len(accessible) / len(data) * 100), 0) if data else 0,
        'avg_risk': round(avg_risk, 1),
        'high_risk': high_risk
    }

def update_index_stats():
    """Embed latest summary.json and category data into index.html"""
    
    # Paths
    script_dir = Path(__file__).parent
    workspace_root = script_dir.parent
    data_dir = workspace_root / 'research' / 'data'
    summary_path = data_dir / 'summary.json'
    index_path = workspace_root / 'index.html'
    
    # Load summary data
    if not summary_path.exists():
        print(f"❌ Summary file not found: {summary_path}")
        return False
    
    with open(summary_path, 'r') as f:
        summary_data = json.load(f)
    
    print(f"✓ Loaded summary data: {summary_data['total_domains']} domains")
    
    # Load category data files
    category_stats = {}
    category_files = {
        'food_delivery': data_dir / 'food_delivery_data.json',
        'cosmetics_beauty': data_dir / 'cosmetics_beauty_data.json',
        'conglomerates': data_dir / 'conglomerates_data.json'
    }
    
    for cat_name, cat_path in category_files.items():
        if cat_path.exists():
            with open(cat_path, 'r') as f:
                cat_data = json.load(f)
            category_stats[cat_name] = calculate_category_stats(cat_data)
            print(f"✓ Loaded {cat_name}: {category_stats[cat_name]['total']} domains")
    
    # Load index.html
    if not index_path.exists():
        print(f"❌ Index file not found: {index_path}")
        return False
    
    with open(index_path, 'r') as f:
        html_content = f.read()
    
    # Create new embedded data blocks
    stats_json = json.dumps(summary_data, indent=2)
    new_stats_block = f"""        const statsData = {stats_json};"""
    
    category_json = json.dumps(category_stats, indent=2)
    new_category_block = f"""        const categoryData = {category_json};"""
    
    # Replace the statsData definition
    pattern = r'const statsData = \{[^}]*(?:\{[^}]*\}[^}]*)*\};'
    if re.search(pattern, html_content):
        html_content = re.sub(pattern, new_stats_block.strip(), html_content)
    
    # Replace or add categoryData definition (insert after statsData)
    category_pattern = r'const categoryData = \{[^}]*(?:\{[^}]*\}[^}]*)*\};'
    if re.search(category_pattern, html_content):
        html_content = re.sub(category_pattern, new_category_block.strip(), html_content)
    else:
        # Insert after statsData
        html_content = html_content.replace(
            new_stats_block,
            f"{new_stats_block}\n\n{new_category_block}"
        )
    
    # Write back to file
    with open(index_path, 'w') as f:
        f.write(html_content)
    
    print(f"✓ Updated {index_path} with latest statistics")
    print(f"  - Total domains: {summary_data['total_domains']}")
    print(f"  - Accessible: {summary_data['accessible_count']} ({summary_data['access_rate']}%)")
    print(f"  - Avg risk: {summary_data['avg_risk_score']}")
    print(f"  - High risk: {summary_data['high_risk_count']}")
    return True

if __name__ == '__main__':
    success = update_index_stats()
    exit(0 if success else 1)
