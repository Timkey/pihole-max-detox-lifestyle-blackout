# Research Directory Structure

Organized analysis outputs and documentation.

## Directory Layout

```
research/
├── reports/          # Interactive HTML reports (published to GitHub Pages)
├── docs/            # Markdown documentation and text reports
├── data/            # JSON data files for programmatic access
├── cache/           # Analysis cache and recommendations
└── README.md        # This file
```

## Contents

### 📊 reports/
**Interactive HTML visualizations**
- `food & delivery_analysis.html` - Food delivery and fast food analysis
- `cosmetics & beauty_analysis.html` - Beauty and cosmetics analysis
- `conglomerates_analysis.html` - Multinational corporation analysis

**Features:**
- Chart.js visualizations (bar charts, doughnut charts)
- Risk score rankings
- Hazard distribution analysis
- Mobile-responsive design
- Hosted on GitHub Pages

### 📝 docs/
**Markdown documentation**
- `food & delivery_analysis.md` - Text-based food analysis report
- `cosmetics & beauty_analysis.md` - Text-based beauty analysis report
- `conglomerates_analysis.md` - Text-based conglomerates report
- `PERFORMANCE_REVIEW.md` - Analysis tool performance evaluation
- `WORKFLOW.md` - Analysis workflow documentation
- `README.md` - Research methodology

### 📦 data/
**JSON data files**
- `food_delivery_data.json` - Raw analysis data for food category
- `cosmetics_beauty_data.json` - Raw analysis data for beauty category
- `conglomerates_data.json` - Raw analysis data for conglomerates

**Structure:**
```json
[
  {
    "domain": "example.com",
    "risk_score": 45,
    "accessible": true,
    "health_hazards": {...},
    "behavioral_hazards": {...},
    "marketing_tactics": {...},
    "seo_metadata": "...",
    "related_domains": [...]
  }
]
```

### 💾 cache/
**Analysis state files**
- `analysis_cache.json` - 30-day cache of domain analyses (avoid re-scraping)
- `recommendations.json` - Pending additions/removals for blocklists

**Cache Structure:**
```json
{
  "analyses": {
    "domain.com": {
      "analyzed_at": "2025-12-30T...",
      "risk_score": 45,
      ...
    }
  }
}
```

**Recommendations Structure:**
```json
{
  "additions": [
    {
      "domain": "new-domain.com",
      "category": "Food & Delivery",
      "reason": "Related service",
      "status": "pending"
    }
  ],
  "removals": [...]
}
```

## Workflow

### Generate Reports
```bash
# Run analysis (creates all files)
exec/analyze.sh

# Generated files:
# - reports/*.html (for GitHub Pages)
# - docs/*.md (for GitHub viewing)
# - data/*.json (for APIs/scripts)
# - cache/*.json (for caching)
```

### Access Reports

**Local:**
```bash
# Open HTML reports
open research/reports/food\ \&\ delivery_analysis.html

# Or use web server
python3 -m http.server 8000
# Visit: http://localhost:8000/research/reports/
```

**GitHub Pages:**
```
https://timkey.github.io/pihole-max-detox-lifestyle-blackout/
```

### Apply Recommendations
```bash
# Review recommendations
cat research/cache/recommendations.json | jq

# Apply changes to blocklists
exec/apply-recommendations.sh

# Regenerate master list
exec/generate-ultra.sh
```

## File Lifecycle

1. **Analysis run** → Creates/updates all files
2. **Cache persists** → Avoids re-analyzing domains (30 days)
3. **Recommendations accumulate** → Until applied or rejected
4. **Reports refresh** → Every analysis run
5. **Commit & push** → Updates GitHub Pages (1-2 min delay)

## Cache Management

```bash
# Clear analysis cache (forces fresh analysis)
rm research/cache/analysis_cache.json

# Clear recommendations
rm research/cache/recommendations.json

# Clear all caches
rm research/cache/*.json
```

## Maintenance

- **Cache:** Clears automatically after 30 days per domain
- **Reports:** Regenerate on each analysis run
- **Data files:** Overwritten on each analysis run
- **Recommendations:** Persist until applied

## Integration

All paths are configured in:
- `scripts/analyze_domains.py`
- `scripts/apply_recommendations.py`

Scripts automatically create directories if missing.
