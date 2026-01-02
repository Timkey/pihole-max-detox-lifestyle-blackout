# Parallel Processing Issues & Fixes

## Issues Identified (2026-01-01)

### 1. Thread-Local Playwright Resource Leaks
**Problem**: Each worker thread creates Playwright/Chromium instances that are never cleaned up.
- `get_playwright_instances()` creates per-thread instances
- `cleanup_playwright()` only cleans main thread
- With 5-10 workers = 5-10 orphaned processes
- After multiple runs, container runs out of resources

**Fix Required**:
```python
# Add cleanup callback to ThreadPoolExecutor
def analyze_parallel(domains, cache, force_reanalysis, category_name, recommendations, existing_domains, max_workers):
    results = []
    completed = 0
    total = len(domains)
    
    def worker_cleanup():
        """Cleanup function called by each worker thread on exit."""
        if hasattr(_thread_local, 'browser'):
            try:
                _thread_local.browser.close()
            except:
                pass
        if hasattr(_thread_local, 'playwright'):
            try:
                _thread_local.playwright.stop()
            except:
                pass
    
    # Pass 1: Base scoring
    print("Pass 1/2: Analyzing base risk scores...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        try:
            # Submit tasks...
            # ... (existing code) ...
        finally:
            # Cleanup all worker threads
            cleanup_futures = []
            for _ in range(max_workers):
                cleanup_futures.append(executor.submit(worker_cleanup))
            # Wait for cleanup
            for future in cleanup_futures:
                try:
                    future.result(timeout=5)
                except:
                    pass
```

### 2. Context Leaks on Timeout/Exception
**Problem**: `context.close()` not called in all exception paths.

**Fix Required**:
```python
def _fetch_with_playwright(self):
    """Fallback fetch using Playwright for JavaScript-heavy sites."""
    playwright, browser = get_playwright_instances()
    context = None
    
    try:
        context = browser.new_context(...)
        page = context.new_page()
        
        # ... existing code ...
        
    except Exception as e:
        # ... error handling ...
    finally:
        # ALWAYS cleanup context
        if context:
            try:
                context.close()
            except:
                pass
```

### 3. Aggressive Timeout Accumulation
**Problem**: Luxury domains (Chanel, Dior, etc.) with bot protection cause all 5 workers to simultaneously hit 60s timeout walls, blocking progress.

**Fix Required**: Implement timeout budget per domain
```python
MAX_TIMEOUT_PER_DOMAIN = 20  # seconds

def _fetch_with_playwright(self):
    start_time = time.time()
    
    try:
        # Reduce per-stage timeouts
        response = page.goto(self.url, wait_until='domcontentloaded', timeout=8000)  # 8s instead of 15s
        
        # Check elapsed time
        elapsed = time.time() - start_time
        if elapsed > MAX_TIMEOUT_PER_DOMAIN:
            raise TimeoutError(f"Total timeout budget exceeded ({elapsed:.1f}s)")
        
        # Reduce wait times
        page.wait_for_timeout(1000)  # 1s instead of 2s
        
    except PlaywrightTimeout:
        elapsed = time.time() - start_time
        self.analysis['error'] = f'Timeout after {elapsed:.1f}s'
        return False
```

### 4. No Early Exit for Known Bot-Protected Domains
**Problem**: Every TLD variation (.com, .uk, .ca, etc.) of bot-protected brands tries full timeout cycle.

**Fix Required**: Cache bot protection patterns
```python
# In AnalysisCache class
def is_bot_protected_pattern(self, domain):
    """Check if domain matches known bot protection patterns."""
    base_domain = domain.split('.')[0]
    
    # Check cache for similar domains with bot protection
    for cached_domain, cached_data in self.cache.items():
        if cached_domain.startswith(base_domain):
            error = cached_data.get('error', '')
            if any(x in error.lower() for x in ['403', 'forbidden', 'cloudflare', 'bot protection', 'certificate']):
                return True
    return False

# In analyze_domain_worker
def analyze_domain_worker(domain, cache, force_reanalysis, ...):
    # Check if domain matches bot-protected pattern
    if cache and cache.is_bot_protected_pattern(domain):
        result = {
            'domain': domain,
            'analyzed_at': datetime.now().isoformat(),
            'accessible': False,
            'error': 'Skipped: Known bot protection pattern',
            'risk_score': 0
        }
        print(f"{domain}... ⚡ Skipping (bot protection pattern)")
        cache.store_analysis(domain, result)
        return result
```

### 5. Resource Exhaustion from Multiple Restarts
**Problem**: Killing and restarting analysis multiple times leaves orphaned processes.

**Evidence**:
```bash
root  10695  ... python3 analyze_domains.py --all --parallel --workers 5  # Started 2025
root  11520  ... python3 analyze_domains.py --all --parallel --workers 5  # Restart 1
root  15038  ... python3 analyze_domains.py --all --parallel --workers 10 # Restart 2
```

**Fix Required**: Add signal handlers for clean shutdown
```python
import signal
import sys

def signal_handler(sig, frame):
    """Handle SIGTERM/SIGINT gracefully."""
    print("\n\n⚠️  Received shutdown signal, cleaning up...")
    
    # Cleanup all thread-local Playwright instances
    cleanup_playwright()
    
    # Force close any ThreadPoolExecutor threads
    # (Python will handle this, but we log it)
    print("✓ Playwright instances closed")
    print("✓ Threads will terminate")
    
    sys.exit(0)

# In main()
def main():
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # ... existing code ...
    finally:
        cleanup_playwright()
```

## Implementation Priority

1. **CRITICAL - Context Cleanup in finally block**: Prevents context leaks (immediate)
2. **CRITICAL - Worker thread Playwright cleanup**: Prevents process accumulation (immediate)
3. **HIGH - Signal handlers**: Clean shutdown on Ctrl+C or kill (next update)
4. **HIGH - Bot protection pattern cache**: Avoid redundant timeouts (next update)  
5. **MEDIUM - Timeout budget per domain**: Fail faster on bot protection (next update)

## Testing Plan

1. Add logging to track:
   - Thread creation/destruction
   - Playwright instance lifecycle
   - Context creation/cleanup
   - Active browser processes

2. Run analysis with `--sample-size 20` including luxury brands

3. Monitor container processes:
   ```bash
   docker exec pihole-blocklist-analyzer ps aux | grep -E "python3|playwright|chromium" | wc -l
   ```

4. Should see process count stable (not growing)

## Performance Impact

**Before fixes**:
- 5 workers × leaked Playwright = resource exhaustion
- Luxury brands: 60s × 5 workers = 300s total bottleneck
- Container OOM after 2-3 restarts

**After fixes**:
- Stable resource usage
- Bot-protected domains: skip after first failure = ~5s × 30 = 150s
- **50% faster on bot-protected categories**
- Clean restarts possible

## Related Files

- `scripts/analyze_domains.py` - Main implementation
- `research/docs/PERFORMANCE_OPTIMIZATION_QUEUE.md` - Worker queue strategy
- `research/docs/PARALLEL_PROCESSING.md` - Current parallel implementation docs
