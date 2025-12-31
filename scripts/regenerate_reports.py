#!/usr/bin/env python3
"""
Regenerate HTML and Markdown reports from existing JSON data.
Use this after updating scores without re-scraping.
"""
import json
from pathlib import Path
import sys

# Add parent directory to path and import the functions
sys.path.insert(0, str(Path(__file__).parent))
from analyze_domains import generate_html_report, generate_markdown_report

DATA_DIR = Path('research/data')

def regenerate_reports():
    """Regenerate all reports from JSON data."""
    categories = {
        'food & delivery': 'food_delivery_data.json',
        'cosmetics & beauty': 'cosmetics_beauty_data.json',
        'conglomerates': 'conglomerates_data.json'
    }
    
    print("\n" + "="*70)
    print("REGENERATING REPORTS FROM UPDATED JSON DATA")
    print("="*70 + "\n")
    
    for category_name, filename in categories.items():
        data_file = DATA_DIR / filename
        
        if not data_file.exists():
            print(f"⚠️  {category_name}: Data file not found")
            continue
        
        print(f"📄 {category_name}:")
        
        # Load data
        with open(data_file, 'r') as f:
            results = json.load(f)
        
        # Generate reports
        generate_html_report(category_name, results)
        print(f"   ✓ Generated HTML report")
        
        generate_markdown_report(category_name, results)
        print(f"   ✓ Generated Markdown report")
        print(f"   → {len(results)} domains processed\n")
    
    print("="*70)
    print("✅ ALL REPORTS REGENERATED")
    print("="*70 + "\n")

if __name__ == '__main__':
    regenerate_reports()
