# Test Mode Guide

## Overview

Test mode allows you to safely experiment with analysis settings, content access strategies, and fixes without affecting production data. This is essential when:

- **Fixing analysis failures** (85% failure rate needs iteration)
- **Testing Playwright settings** (timeout, navigation, threading)
- **Experimenting with User-Agent rotation**
- **Iterating on content access strategies**
- **Testing new features** before production deployment

## Directory Structure

Test mode creates parallel directories that mirror production:

```
research/
├── data/
│   ├── food_delivery_data.json           ← Production data
│   ├── cosmetics_beauty_data.json
│   ├── conglomerates_data.json
│   ├── summary.json
│   └── test/                              ← Test data (isolated)
│       ├── food_delivery_data.json
│       ├── cosmetics_beauty_data.json
│       └── conglomerates_data.json
│
├── cache/
│   ├── analysis_cache.json               ← Production cache
│   └── test/                              ← Test cache (isolated)
│       └── analysis_cache.json
│
├── reports/
│   ├── food & delivery_analysis.html     ← Production reports
│   ├── cosmetics & beauty_analysis.html
│   ├── conglomerates_analysis.html
│   └── test/                              ← Test reports (isolated)
│       ├── food & delivery_analysis.html
│       ├── cosmetics & beauty_analysis.html
│       └── conglomerates_analysis.html
│
└── docs/
    ├── food & delivery_analysis.md       ← Production markdown
    └── test/                              ← Test markdown (isolated)
        └── food & delivery_analysis.md
```

## Usage

### Command Line

All analysis and scoring scripts support `--test` or `-t` flag:

```bash
# Python scripts (inside Docker container)
python3 scripts/analyze_domains.py --test
python3 scripts/recalculate_enabler_scores.py --test
python3 scripts/regenerate_reports.py --test

# Shell wrapper scripts (from host)
./exec/analyze.sh --test
./exec/recalculate-scores.sh --test
./exec/regenerate-reports.sh --test
```

### Combined with Other Flags

```bash
# Test a specific category with small sample
./exec/analyze.sh --test --category food --sample-size 10

# Test parallel processing
./exec/analyze.sh --test --parallel --workers 3

# Force reanalysis in test mode
./exec/analyze.sh --test --force --category food

# Analyze all domains in test mode
./exec/analyze.sh --test --all
```

## Workflow Example

### Scenario: Fixing 85% Analysis Failure Rate

Current problem: 686/806 food domains failed with "threading" errors.

**Step 1: Test fixes on small sample**
```bash
# Modify analyze_domains.py with potential fix
# Test on 10 domains first
./exec/analyze.sh --test --category food --sample-size 10
```

**Step 2: Review test results**
```bash
# Check test reports (won't affect production reports)
open research/reports/test/food\ \&\ delivery_analysis.html

# Examine test data
cat research/data/test/food_delivery_data.json | jq '.[] | select(.error) | .error'
```

**Step 3: Iterate if needed**
```bash
# Try different approach
# Modify code and retest
./exec/analyze.sh --test --force --category food --sample-size 10
```

**Step 4: Scale up testing**
```bash
# Once working, test larger sample
./exec/analyze.sh --test --category food --sample-size 50
```

**Step 5: Deploy to production**
```bash
# When confident, run on production
./exec/analyze.sh --category food --all
```

## Viewing Test Reports

Test reports are isolated in `research/reports/test/`:

```bash
# View test HTML reports
open research/reports/test/food\ \&\ delivery_analysis.html
open research/reports/test/cosmetics\ \&\ beauty_analysis.html
open research/reports/test/conglomerates_analysis.html

# Compare with production
open research/reports/food\ \&\ delivery_analysis.html
```

## Clearing Test Data

Test data is completely isolated from production. Safe to delete:

```bash
# Clear all test data
rm -rf research/data/test/
rm -rf research/cache/test/
rm -rf research/reports/test/
rm -rf research/docs/test/

# Or clear specific category
rm research/data/test/food_delivery_data.json
rm research/cache/test/analysis_cache.json
```

Test directories are automatically recreated on next `--test` run.

## Benefits

✅ **Safe experimentation** - Production data untouched  
✅ **Fast iteration** - Test on small samples first  
✅ **Compare results** - Production vs test reports side-by-side  
✅ **No risk** - Can't corrupt production cache or results  
✅ **Easy cleanup** - Just delete test directories  

## Scripts Supporting Test Mode

- ✅ `analyze_domains.py` - Full analysis with test mode
- ✅ `recalculate_enabler_scores.py` - Score recalculation
- ✅ `regenerate_reports.py` - Report generation
- ⚠️ `apply_recommendations.py` - Not yet (affects blocklists)
- ⚠️ `check_domain_variations.py` - Not yet (uses single cache)
- ⚠️ `add_domain_variations.py` - Not yet (modifies blocklists)

## Testing Strategies

### Fix Threading Errors
```bash
# Test with different Playwright settings
# Modify page.goto() timeout, add delays, etc.
./exec/analyze.sh --test --category food --sample-size 20
```

### Test User-Agent Rotation
```bash
# Add User-Agent rotation logic
# Test on domains that previously failed
./exec/analyze.sh --test --force --category food --sample-size 10
```

### Test Parallel Processing
```bash
# Test different worker counts
./exec/analyze.sh --test --parallel --workers 3 --sample-size 30
./exec/analyze.sh --test --parallel --workers 5 --sample-size 30
./exec/analyze.sh --test --parallel --workers 10 --sample-size 30
```

### Compare Strategies
```bash
# Strategy A in test mode
./exec/analyze.sh --test --category food --sample-size 20

# Modify code for Strategy B
./exec/analyze.sh --test --force --category food --sample-size 20

# Compare reports to see which worked better
diff <(jq '.[] | .error' research/data/test/food_delivery_data.json) \
     <(jq '.[] | .error' research/data/food_delivery_data.json)
```

## Troubleshooting

**Test mode not enabled?**
```bash
# Look for this message when running scripts:
# 🧪 TEST MODE ENABLED
#    Data: /path/to/research/data/test
#    Cache: /path/to/research/cache/test
#    Reports: /path/to/research/reports/test
```

**Test directories not created?**
They're created automatically on first `--test` run. Check:
```bash
ls -la research/data/test/
ls -la research/cache/test/
ls -la research/reports/test/
```

**Accidentally tested in production?**
No worries - test mode is opt-in. Without `--test` flag, production is used.

## Best Practices

1. **Start small** - Test on 5-10 domains first
2. **Compare results** - View test vs production reports
3. **Iterate rapidly** - Use `--force` to retest same domains
4. **Document findings** - Note what worked/failed
5. **Graduate to production** - Only when confident
6. **Keep test data** - Useful for comparison and debugging

## Next Steps

After test mode success:
1. Run full analysis on production: `./exec/analyze.sh --all`
2. Recalculate scores: `./exec/recalculate-scores.sh`
3. Regenerate reports: `./exec/regenerate-reports.sh`
4. Deploy: Commit and push changes
