# Statistics Harmonization - Complete

## Overview
All domain-related statistics are now harmonized across the project with DNS verification tracking, parallel processing support, and bi-directional enabler scoring.

## New Features ✨

### Bi-Directional Enabler Scoring
Implemented comprehensive enabler detection that tracks both directions of relationships:

#### 1. Outbound (Parent → Child)
- **Purpose**: Detect platforms linking TO high-risk domains
- **Threshold**: Risk score ≥ 50
- **Bonus**: +5 points per high-risk link (max +20)
- **Example**: Platform linking to multiple high-risk brands

#### 2. Inbound (Child → Parent) ✨ NEW
- **Purpose**: Detect platforms that high-risk domains link TO
- **Threshold**: Risk score ≥ 20 (lower to catch more facilitators)
- **Bonus**: sum(facilitator_risk_scores) / 10 (max +30)
- **Example**: Delivery platform mentioned by many restaurants

#### Combined Scoring
- **Maximum bonus**: +50 points (20 outbound + 30 inbound)
- **Use case**: Delivery platforms get penalized for enabling access to unhealthy food brands
- **Data fields**:
  - `high_risk_links`: Array of domains this domain links to (≥50 risk)
  - `facilitated_domains`: Array of domains linking to this domain (≥20 risk)
  - `enabler_risk_bonus`: Total bonus from both directions

#### Fast Recalculation
**Script**: `scripts/recalculate_enabler_scores.py`
- Recalculates scores without re-scraping websites
- Uses existing `related_domains` data from JSON files
- Builds reverse index (mentioned_by dictionary)
- Updates all domains in seconds vs 80-minute full reanalysis

**Example Results**:
- deliveroo.co.uk: 36 → 48 (+12 from 3 facilitators)
- ubereats.com: 0 → 5 (+5 from 1 facilitator)
- wendys.com: 51 → 61 (+5 outbound + +5 inbound)

### Interactive HTML Reports ✨ NEW
Enhanced report generation with:

#### Features
- **Dynamic JSON Loading**: Reports try to fetch fresh JSON first, fallback to embedded data
- **Mobile Responsive**: Optimized for phones, tablets, and desktops
- **Interactive Charts**: All charts update when filters change
- **Sorting Controls**: Score ↓↑, A-Z sorting for domain lists
- **Collapsible Sections**: Failed analysis section folds to avoid obscuring main content
- **Failed Analysis Tracking**: 
  - Categorized error display (Timeout, Insufficient Content, Threading, DNS, SSL, etc.)
  - Doughnut chart showing error distribution
  - Scrollable error list with truncated messages

#### Chart Types
- Health Hazards: Bar chart
- Behavioral Hazards: Doughnut chart
- Marketing Tactics: Horizontal bar chart
- Risk Score Distribution: Top 15 domains bar chart
- Failed Analysis: Doughnut chart (error categories)

#### Mobile Optimizations
- Viewport-aware layouts (≤768px tablet, ≤480px mobile)
- Touch-friendly buttons (16px min font, 44px min height)
- Single-column layouts on small screens
- Horizontal scroll for sort buttons
- Word wrapping for long domain names

### Report Regeneration ✨ NEW
**Script**: `scripts/regenerate_reports.py`
- Generates HTML and Markdown reports from existing JSON data
- No web scraping required
- Updates all three category reports
- Useful after score recalculation or data updates

## Centralized Statistics (summary.json)

The `research/data/summary.json` file now includes:

### 1. Analysis Statistics
- **total_domains**: Total domains analyzed across all categories
- **accessible_count**: Domains successfully accessed during analysis
- **avg_risk_score**: Average risk score of accessible domains
- **access_rate**: Percentage of domains successfully accessed
- **high_risk_count**: Number of domains with risk score ≥ 50

### 2. Category Breakdown
- **cosmetics_beauty**: Count of cosmetics domains analyzed
- **food_delivery**: Count of food/delivery domains analyzed  
- **conglomerates**: Count of conglomerate domains analyzed

### 3. DNS Verification Statistics ✨ NEW
- **verified_domains**: Domains confirmed via DNS lookup
- **unverified_domains**: Domains that failed DNS verification
- **total_dns_checked**: Total domains checked via DNS
- **last_dns_check**: Timestamp of last DNS verification run

### 4. Blocklist Statistics ✨ NEW
- **food**: Domain count in lists/food.txt
- **cosmetics**: Domain count in lists/cosmetics.txt
- **conglomerates**: Domain count in lists/conglomerates.txt
- **blackout-ultra**: Total count in lists/blackout-ultra.txt

## Parallel Processing Support ✨ NEW

### Updated Scripts with Parallel Processing:

#### 1. `check_domain_variations.py`
- **Purpose**: Scan for missing TLD variations
- **Usage**: `python3 check_domain_variations.py --workers 8`
- **Default Workers**: 8
- **Features**:
  - Parallel DNS lookups with ThreadPoolExecutor
  - Real-time progress reporting
  - Cache-aware processing (skips already verified domains)

#### 2. `add_domain_variations.py`
- **Purpose**: Add verified TLD variations to blocklists
- **Usage**: `python3 add_domain_variations.py --workers 8`
- **Default Workers**: 8
- **Features**:
  - Parallel DNS verification
  - Automatic blocklist updating
  - Auto-triggers statistics update after completion

#### 3. `analyze_domains.py`
- **Purpose**: Main domain content analysis
- **Usage**: `./exec/analyze.sh --category <cat> --workers 8 --parallel`
- **Features**:
  - Parallel domain analysis (existing feature)
  - Now generates comprehensive summary.json
  - Includes DNS and blocklist statistics
  - Auto-updates index.html after completion

## Index.html Display

The main index page now displays:
- **Analyzed Domains**: Total domains processed
- **Average Risk Score**: Average hazard score
- **Access Success Rate**: % of accessible domains
- **High Risk Domains**: Count of high-risk domains
- **DNS Verified**: Total domains verified via DNS ✨ NEW
- **Total Blocklisted**: Sum of all blocklist entries ✨ NEW

## Automatic Updates

### Workflow
1. Run any analysis script → Generates/updates JSON data
2. `analyze_domains.py` → Calls `generate_summary_stats()`
3. Summary stats → Aggregates all data sources:
   - Analysis JSON files (`*_data.json`)
   - DNS cache (`.domain_cache.json`)
   - Blocklist files (`*.txt`)
4. `update_index.py` → Embeds summary.json into index.html
5. Index displays → All statistics visible to user

### Manual Statistics Update
```bash
# Run analysis on any category to trigger update
./exec/analyze.sh --category food --sample-size 10

# Or manually update statistics
python3 scripts/update_index.py
```

## Performance Optimizations

### Parallel Processing Benefits
- **DNS Verification**: 8 workers can check ~400 domains/minute
- **Domain Analysis**: 8 workers can analyze 50-100 domains/minute
- **Cache Hit Rate**: ~70-90% for repeated runs (saves significant time)

### Scaling Recommendations
- Small datasets (< 100 domains): 4 workers
- Medium datasets (100-500): 8 workers
- Large datasets (500+): 8-16 workers
- Network-limited environments: 4-6 workers

## Data Flow Diagram

```
[Domain Lists]          [Analysis Cache]        [DNS Cache]
    ↓                         ↓                      ↓
    ├─ food.txt              ├─ analysis_cache.json ├─ .domain_cache.json
    ├─ cosmetics.txt         └─ recommendations.json└─ verified/not_found
    ├─ conglomerates.txt
    └─ blackout-ultra.txt
         ↓                         ↓                      ↓
    [analyze_domains.py] ← [check_domain_variations.py]
              ↓                    
    [*_data.json files]           
              ↓
    [generate_summary_stats()]
              ↓
    [summary.json] ← Aggregates all sources
              ↓
    [update_index.py]
              ↓
    [index.html] ← statsData embedded
```

## Script Interdependencies

### Primary Scripts
1. **analyze_domains.py**: Master analyzer + stats generator
2. **update_index.py**: Embeds stats into HTML
3. **check_domain_variations.py**: Finds new TLD variations
4. **add_domain_variations.py**: Adds verified variations
5. **generate_ultra.py**: Combines all lists

### Execution Order (Full Workflow)
```bash
# 1. Analyze domains
./exec/analyze.sh --category all --workers 8 --parallel

# 2. Check for new variations (optional)
python3 scripts/check_domain_variations.py --workers 8

# 3. Add verified variations (optional)
python3 scripts/add_domain_variations.py --workers 8

# 4. Regenerate ultra list
python3 scripts/generate_ultra.py

# 5. Re-analyze to update stats
./exec/analyze.sh --category all --workers 8 --parallel

# Statistics are automatically updated throughout this process
```

## Cache Management

### DNS Cache (`.domain_cache.json`)
- Location: `lists/.domain_cache.json`
- Contains: Verified and unverified domain records
- TTL: Permanent (manual cleanup if needed)
- Purpose: Avoid redundant DNS lookups

### Analysis Cache (`analysis_cache.json`)
- Location: `research/cache/analysis_cache.json`
- Contains: Domain analysis results (risk scores, hazards, etc.)
- TTL: 30 days (configurable)
- Purpose: Speed up repeated analyses

## Future Enhancements

- [ ] Real-time statistics dashboard
- [ ] Historical trend tracking
- [ ] Automated DNS cache cleanup (age-based)
- [ ] Webhook notifications on high-risk domain discovery
- [ ] API endpoint for statistics access
- [ ] Automated blocklist updates based on analysis scores

## Last Updated
2025-12-31
