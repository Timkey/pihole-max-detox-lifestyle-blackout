# Analysis Performance Review - Dec 30, 2025

## Recent Improvements ✨

### SEO Metadata Analysis (ADDED)
**Solution for JS-rendered sites:** Extract marketing language from HTML metadata
- Title tags, meta descriptions, Open Graph tags
- Twitter Cards, JSON-LD structured data
- Works even when page body is empty (JS-rendered)

**Results:**
```
ubereats.com: 4/100 → 7/100 (text: 0 chars, SEO: 500 chars)
postmates.com: 15/100 → 18/100 (detected FOMO + convenience tactics)
grubhub.com: Now detects behavioral patterns from meta tags alone
```

**What it captures:**
- Urgency language in titles ("Order Now", "Fast Delivery")
- Discount messaging in descriptions
- Social proof from structured data (ratings, reviews)
- Product schema reveals pricing tactics

## Issues Identified

### 1. Bot Detection / JS-Rendered Content ❌
**Problem:** Major domains block scrapers or use JavaScript rendering
- ubereats.com, doordash.com, nestle.com return minimal/empty HTML
- BeautifulSoup can't execute JavaScript
- Results in artificially low risk scores (4/100)
- Major platforms incorrectly flagged for removal

**Fix Applied:**
- ✅ Better User-Agent (Chrome 120 on macOS)
- ✅ Content validation (reject if <100 chars)
- ⚠️ Still limited without JS execution engine

### 2. False Positive Recommendations ⚠️
**Problem:** Suggests blocking major third-party platforms
- uber.com, itunes.apple.com, play.google.com in food category
- Too broad - breaks unrelated services

**Fix Applied:**
- ✅ Blocklist for common platforms (Facebook, Google, Apple, Amazon)
- ✅ Filters obvious false positives

### 3. Performance Issues 🐌
**Stats:**
- Time: 49 seconds for 15 domains (5 per category)
- Coverage: 15/1101 domains = 1.4%
- Full analysis: ~1 hour estimated

**Current Settings:**
- Sample size: 5 domains per category
- Food: 5/806 analyzed (0.6%)
- Cosmetics: 5/96 analyzed (5.2%)
- Conglomerates: 5/199 analyzed (2.5%)

### 4. Low Risk Score Issues 📊
**Problem:** Failed analyses → score=0 → removal recommended

**Fix Applied:**
- ✅ Skip removal recommendations for score=0 or None
- ✅ Only recommend removal with valid analysis data

## Recommendations

### Immediate (Done ✅)
- ✅ Better User-Agent headers
- ✅ Content validation
- ✅ Filter common platforms
- ✅ Skip invalid removal recommendations

### Short Term (To Do)
- ⚠️ Increase sample size to 20-50 per category
- ⚠️ Add retry logic with delays
- ⚠️ Manual whitelist for "definitely block" domains
- ⚠️ Reduce cache validity (7 days for failures vs 30 days for success)

### Long Term (Future)
- 🔮 Selenium/Playwright for JS sites
- 🔮 Alternative analysis methods (DNS, app stores, reviews)
- 🔮 Machine learning model

## Current Tool Status

**Working:**
- Cache system
- Related domain detection
- Hazard keyword matching
- Report generation

**Limited:**
- JS-rendered sites (80% of modern web)
- Accurate risk scoring
- Scalability (hours for full run)

## Usage Recommendations

```bash
# Use for discovery, not automation
exec/analyze.sh

# Review recommendations.json
# - Check additions (filter false positives)
# - Ignore removals (unreliable)
# - Use reports for justifications

# Manually add valid domains
# Then regenerate
exec/generate-ultra.sh
```

## Test Results

```
Food: 806 domains → 5 analyzed
- 1 failed (doordash.com - bot detection)
- 4 low scores (JS-rendered content)

Cosmetics: 96 domains → 5 analyzed  
- 3 failed (fake TLDs)
- 2 successful

Conglomerates: 199 domains → 5 analyzed
- 4 failed (aggressive bot blocking)
- 1 successful
```

## Conclusion

Tool is **useful for**:
- ✅ Finding related domains/subdomains
- ✅ Avoiding redundant analysis (caching)
- ✅ Generating documentation

**Limited by**:
- ❌ JavaScript rendering requirement
- ❌ Bot detection systems
- ❌ Performance at scale

**Use as discovery tool with manual review, not automated decision-making.**
