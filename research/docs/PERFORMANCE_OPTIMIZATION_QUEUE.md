# Performance Optimization Queue

## Priority Queue for Slow-Timeout Domains

### Problem Identified
**Date**: 2026-01-01  
**Issue**: Luxury brand domains (Chanel, Dior, Lancôme, YSL, Bobbi Brown) with aggressive bot protection cause parallel workers to bottleneck during analysis.

**Impact**:
- Each failed domain requires full timeout cycle: HTTP → HTTPS → Playwright → eventual failure
- Timeout duration: 30-60 seconds per domain
- With 5 workers processing ~30 luxury variations simultaneously, overall progress stalls at 43.5% (cosmetics category)
- Workers spend most time waiting on timeout rather than analyzing accessible domains

### Current Behavior
All domains processed in blocklist order, causing workers to simultaneously hit slow-timeout domains and block faster domains from processing.

### Proposed Solution: Smart Worker Queue System

#### 1. Domain Classification
Create a timeout prediction system based on:
- **Historical data**: Track average response times from analysis cache
- **Brand patterns**: Known luxury/high-security brands
- **Bot protection indicators**: Previous Cloudflare/403 responses

#### 2. Priority Queue Implementation
```python
# Pseudocode structure
FAST_QUEUE = []    # Expected < 5s response time
MEDIUM_QUEUE = []  # Expected 5-15s response time  
SLOW_QUEUE = []    # Expected > 15s or known timeout patterns

# Worker assignment
fast_workers = workers[0:3]   # 3 workers for fast domains
slow_workers = workers[3:5]   # 2 dedicated workers for slow domains
```

#### 3. Known Slow Domains Registry
Create `research/data/slow_timeout_domains.json`:
```json
{
  "luxury_brands": [
    "chanel.*",
    "dior.*", 
    "lancome.*",
    "yslbeauty.*",
    "gucci.*",
    "louisvuitton.*"
  ],
  "high_security": [
    "redbull.*",
    "monsterenergy.*",
    "nike.*",
    "adidas.*"
  ],
  "timeout_threshold_seconds": 15,
  "max_slow_worker_ratio": 0.4
}
```

#### 4. Dynamic Rebalancing
- Monitor worker idle time
- If fast queue empty and slow workers busy: reassign fast workers to slow queue
- If slow queue empty: all workers process fast queue

#### 5. Cache Integration
Update `analysis_cache.json` to store timing metadata:
```json
{
  "domain": "chanel.com",
  "risk_score": 71,
  "response_time_seconds": 45.3,
  "timeout_pattern": "playwright_fallback_403",
  "last_analyzed": "2026-01-01T21:45:00Z"
}
```

### Implementation Checklist
- [ ] Add `response_time` tracking to `analyze_domains.py`
- [ ] Create `slow_timeout_domains.json` registry
- [ ] Implement domain classification function
- [ ] Modify `analyze_domains.py` to use priority queues
- [ ] Add worker pool with specialized assignments
- [ ] Update cache schema to include timing metadata
- [ ] Add CLI flag: `--smart-queue` to enable/disable feature
- [ ] Document performance improvements in benchmarks

### Expected Performance Improvement
**Current**: 104 remaining cosmetics domains at ~30s each = ~52 minutes (with 5 workers, accounting for parallelism)  
**With Smart Queue**: 
- Fast domains (70%): ~10 minutes 
- Slow domains (30%): ~30 minutes (parallel processing by dedicated workers)
- **Total**: ~30 minutes (40% improvement)

### Related Files
- `scripts/analyze_domains.py` - Main analysis script
- `research/cache/analysis_cache.json` - Domain cache
- `research/docs/PARALLEL_PROCESSING.md` - Current parallel implementation
- `research/docs/PERFORMANCE_REVIEW.md` - Performance metrics

### Notes
- Smart queue should be opt-in initially via `--smart-queue` flag
- Monitor cache file size growth with additional metadata
- Consider separate cache file for timing data if performance degrades
- Test with smaller sample sets before full deployment
