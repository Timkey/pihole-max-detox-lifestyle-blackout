# Analysis Tool Usage Guide

## Quick Start

The analysis tool examines domain content to identify health hazards, behavioral manipulation, and marketing tactics.

## Basic Usage

```bash
# Default: Analyze 5 domains per category (cached results reused)
./exec/analyze.sh

# Analyze specific number of domains per category
./exec/analyze.sh --sample-size 20

# Analyze ALL domains (WARNING: ~27 minutes for food category alone)
./exec/analyze.sh --all

# Force reanalysis (ignore cache, useful after updating hazard keywords)
./exec/analyze.sh --force

# Analyze only one category
./exec/analyze.sh --category food
./exec/analyze.sh --category cosmetics
./exec/analyze.sh --category conglomerates
```

## Advanced Usage

```bash
# Analyze 50 food domains, forcing fresh analysis
./exec/analyze.sh --category food --sample-size 50 --force

# Full reanalysis of everything (VERY SLOW)
./exec/analyze.sh --all --force

# Quick test run without saving to cache
./exec/analyze.sh --no-cache --sample-size 3
```

## Command Options

| Option | Short | Description |
|--------|-------|-------------|
| `--sample-size N` | `-n` | Number of domains per category (default: 5) |
| `--all` | `-a` | Analyze ALL domains (ignores sample-size) |
| `--force` | `-f` | Ignore cache, reanalyze everything |
| `--category NAME` | `-c` | Only analyze: food, cosmetics, or conglomerates |
| `--no-cache` | | Don't use or save cache (testing mode) |
| `--help` | `-h` | Show help message |

## Performance Guide

| Sample Size | Food Domains | Estimated Time | Use Case |
|------------|--------------|----------------|----------|
| 5 (default) | 5 | ~20 seconds | Quick validation |
| 20 | 20 | ~1 minute | Regular testing |
| 50 | 50 | ~3 minutes | Comprehensive sample |
| 100 | 100 | ~6 minutes | Deep analysis |
| --all | 806 | ~27 minutes | Full coverage |

*Times include 2-second delays between requests to avoid bot detection*

## Cache Behavior

### When Cache is Used (Default)
- Results older than 30 days are re-analyzed
- Only domains without cached results are analyzed
- Speeds up repeat analyses significantly

### When to Use `--force`
- After updating hazard keywords in the script
- When you suspect cached data is incorrect
- After implementing content access improvements
- When testing new analysis logic

### When to Use `--no-cache`
- Testing changes without polluting cache
- One-off analyses that shouldn't be saved
- Comparing results with/without caching

## Output Files

After analysis, results are saved to:

```
research/
├── reports/                              # Interactive HTML visualizations
│   ├── food & delivery_analysis.html
│   ├── cosmetics & beauty_analysis.html
│   └── conglomerates_analysis.html
├── docs/                                 # Markdown reports
│   ├── food & delivery_analysis.md
│   ├── cosmetics & beauty_analysis.md
│   └── conglomerates_analysis.md
├── data/                                 # JSON data for programmatic access
│   ├── food_delivery_data.json
│   ├── cosmetics_beauty_data.json
│   └── conglomerates_data.json
└── cache/
    ├── analysis_cache.json              # Cached analysis results (30-day TTL)
    └── recommendations.json              # Suggested additions/removals
```

## Recommendations

The tool generates recommendations for:

1. **Additions**: Related domains discovered during analysis
2. **Removals**: Domains with low risk scores (<30/100)

Review recommendations:
```bash
cat research/cache/recommendations.json | python3 -m json.tool
```

Apply recommendations:
```bash
./exec/apply-recommendations.sh
```

## Examples

### Daily Quick Check
```bash
# Analyze 10 domains per category, use cache
./exec/analyze.sh --sample-size 10
```

### Weekly Deep Analysis
```bash
# Analyze 50 domains per category, force fresh data
./exec/analyze.sh --sample-size 50 --force
```

### Targeting Problem Category
```bash
# Focus on food delivery, analyze 30 domains
./exec/analyze.sh --category food --sample-size 30
```

### Monthly Full Audit (Slow!)
```bash
# Analyze everything from scratch
./exec/analyze.sh --all --force
# Expected time: ~1-2 hours for all categories
```

## Troubleshooting

### "Failed to access" errors
- Normal for sites with strong bot detection (ubereats, doordash)
- Implement solutions from [CONTENT_ACCESS_SOLUTIONS.md](CONTENT_ACCESS_SOLUTIONS.md)
- Use `--force` after implementing improvements to test

### Low risk scores
- Sites with JavaScript-rendered content return empty HTML
- See [CONTENT_ACCESS_SOLUTIONS.md](CONTENT_ACCESS_SOLUTIONS.md) for Playwright solution
- SEO metadata extraction helps but is limited

### Analysis stops mid-way
- Check if Docker container is running: `docker ps`
- Verify network connectivity: `docker exec pihole-blocklist-analyzer ping -c 1 google.com`
- Check logs: `docker logs pihole-blocklist-analyzer`

### Cache not updating
- Use `--force` to bypass cache
- Delete cache file: `rm research/cache/analysis_cache.json`
- Check cache age in file (30-day expiry)

## Best Practices

1. **Start Small**: Use default `--sample-size 5` for initial testing
2. **Use Cache**: Don't force reanalysis unless needed
3. **Category Focus**: Analyze one category at a time for large samples
4. **Schedule Full Runs**: Run `--all` monthly, not daily
5. **Review Recommendations**: Check before applying blindly
6. **Update Keywords**: Refine hazard keywords based on results
7. **Monitor Performance**: Track success rate and risk scores over time

## Next Steps

1. Review HTML reports in browser: `open research/reports/food\ \&\ delivery_analysis.html`
2. Check recommendations: `cat research/cache/recommendations.json`
3. Apply valid recommendations: `./exec/apply-recommendations.sh`
4. Implement content access improvements for better results
