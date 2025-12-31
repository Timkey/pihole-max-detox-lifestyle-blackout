#!/usr/bin/env python3
"""
Regenerate HTML and Markdown reports from existing JSON data.
Use this after updating scores without re-scraping.
"""
import json
import argparse
from pathlib import Path
import sys

# Add parent directory to path and import the functions
sys.path.insert(0, str(Path(__file__).parent))
from analyze_domains import generate_html_report, generate_markdown_report

# Paths
RESEARCH_DIR = Path(__file__).parent.parent / 'research'
DATA_DIR = RESEARCH_DIR / 'data'
TEST_DATA_DIR = DATA_DIR / 'test'
REPORTS_DIR = RESEARCH_DIR / 'reports'
TEST_REPORTS_DIR = REPORTS_DIR / 'test'
DOCS_DIR = RESEARCH_DIR / 'docs'
TEST_DOCS_DIR = DOCS_DIR / 'test'

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
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Regenerate HTML and Markdown reports from existing JSON data'
    )
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Test mode: use separate test directories for data/reports (doesn\'t affect production)'
    )
    
    args = parser.parse_args()
    
    # Set directories based on test mode
    global DATA_DIR
    if args.test:
        DATA_DIR = TEST_DATA_DIR
        TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
        TEST_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        TEST_DOCS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"🧪 TEST MODE ENABLED")
        print(f"   Data: {DATA_DIR}")
        print(f"   Reports: {TEST_REPORTS_DIR}\n")
        
        # Update the analyze_domains module to use test directories
        import analyze_domains
        analyze_domains.DATA_DIR = TEST_DATA_DIR
        analyze_domains.REPORTS_DIR = TEST_REPORTS_DIR
        analyze_domains.DOCS_DIR = TEST_DOCS_DIR
    
    regenerate_reports()
