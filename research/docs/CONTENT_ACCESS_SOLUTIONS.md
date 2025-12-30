# Improving Website Content Access

## Current Issues

1. **JavaScript-rendered sites** - 80% of modern websites (ubereats, doordash, grubhub)
2. **Bot detection** - Cloudflare, reCAPTCHA, rate limiting
3. **Empty content** - text_length: 0 for major platforms
4. **Low risk scores** - Can't analyze what we can't see

## Solutions (Easy → Hard)

### 1. Request Headers Enhancement ⭐ (DONE)
**Status:** Already implemented
- Realistic User-Agent strings
- Accept headers, language preferences
- Connection keep-alive

**Limitations:** Still blocked by many sites

### 2. Request Delays & Retry Logic ⭐⭐ (RECOMMENDED)
**Impact:** Reduces rate-limiting, improves success rate

```python
import time
import random

def fetch_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Random delay between requests (1-3 seconds)
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:  # Rate limited
                wait_time = int(response.headers.get('Retry-After', 60))
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(5 * (attempt + 1))  # Exponential backoff
    return None
```

**Pros:** Simple, free, effective for soft rate limits  
**Cons:** Slower analysis (3-5s per domain instead of 1s)

### 3. Session Cookies & Persistent Connections ⭐⭐
**Impact:** Appears more like real browser

```python
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0...',
    'Accept': 'text/html,...',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
})

# Reuse session across requests
response = session.get(url)
```

**Pros:** Free, reduces bot detection  
**Cons:** Still can't execute JavaScript

### 4. Rotating User Agents ⭐⭐
**Impact:** Avoids pattern detection

```python
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36...',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15...',
]

headers = {'User-Agent': random.choice(USER_AGENTS)}
```

**Pros:** Simple, free  
**Cons:** Limited effectiveness alone

### 5. Selenium/Playwright (JavaScript Execution) ⭐⭐⭐⭐
**Impact:** Solves 80% of modern website issues

**Selenium Setup:**
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def fetch_with_selenium(url):
    options = Options()
    options.add_argument('--headless')  # Run in background
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0...')
    
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    
    # Wait for JavaScript to load
    time.sleep(3)
    
    html = driver.page_source
    driver.quit()
    return html
```

**Playwright Setup (Better):**
```python
from playwright.sync_api import sync_playwright

def fetch_with_playwright(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until='networkidle')
        html = page.content()
        browser.close()
        return html
```

**Pros:** 
- Executes JavaScript
- Renders dynamic content
- Better bot evasion (real browser)

**Cons:**
- Slower (5-10s per domain)
- More resource intensive
- Requires Chrome/Chromium installed
- Higher complexity

**Docker Integration:**
```dockerfile
FROM python:3.11-slim

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install playwright beautifulsoup4 requests
RUN playwright install chromium
RUN playwright install-deps
```

### 6. Proxy Rotation ⭐⭐⭐
**Impact:** Bypasses IP-based blocking

**Free Proxies (unreliable):**
```python
import requests

PROXIES = [
    'http://proxy1.com:8080',
    'http://proxy2.com:8080',
]

proxies = {'http': random.choice(PROXIES), 'https': random.choice(PROXIES)}
response = requests.get(url, proxies=proxies, timeout=10)
```

**Paid Services (reliable):**
- ScraperAPI ($29/mo, 100k requests)
- Bright Data (formerly Luminati)
- Smartproxy
- Oxylabs

**Pros:** Bypasses IP blocks  
**Cons:** Costs money, setup complexity

### 7. Cloud Functions / Distributed Scraping ⭐⭐⭐⭐
**Impact:** Multiple IPs, no local rate limiting

```python
# AWS Lambda, Google Cloud Functions, or Cloudflare Workers
# Each function call = different IP

import boto3

lambda_client = boto3.client('lambda')

def analyze_domain(domain):
    response = lambda_client.invoke(
        FunctionName='scrape-domain',
        InvocationType='RequestResponse',
        Payload=json.dumps({'domain': domain})
    )
    return json.loads(response['Payload'].read())
```

**Pros:** Distributed, scalable, different IPs  
**Cons:** AWS costs, complexity, cold starts

### 8. API Integrations (When Available) ⭐⭐⭐⭐⭐
**Impact:** Official data, no scraping needed

Examples:
- **Yelp API** - Restaurant data, reviews, ratings
- **OpenFoodFacts API** - Nutrition data for food products
- **Brandfetch API** - Company branding, descriptions
- **Clearbit API** - Company information

```python
# Example: OpenFoodFacts
import requests

def get_product_info(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    response = requests.get(url)
    return response.json()
```

**Pros:** Legal, fast, structured data  
**Cons:** Limited coverage, API keys, rate limits

## Recommended Implementation Priority

### Phase 1: Quick Wins (Week 1)
✅ Already done: Better headers, content validation  
🔲 Add: Request delays (1-3s random)  
🔲 Add: Retry logic with exponential backoff  
🔲 Add: Session persistence  
🔲 Add: User-agent rotation

**Expected improvement:** 20-30% more successful scrapes

### Phase 2: JavaScript Support (Week 2-3)
🔲 Add Playwright to Docker container  
🔲 Fallback logic: Try requests first, use Playwright if empty content  
🔲 Update analyze_domains.py with dual-mode fetching

**Expected improvement:** 60-80% more successful scrapes

### Phase 3: Advanced (Future)
🔲 Proxy rotation (if still hitting blocks)  
🔲 API integrations where available  
🔲 Distributed cloud scraping (if scaling needed)

## Code Implementation

### Hybrid Approach (Recommended)

```python
def fetch_content(self):
    """Fetch website content with fallback to Playwright."""
    # Try fast method first (requests)
    html = self._fetch_with_requests()
    
    if html and len(html) > 500:  # Got meaningful content
        self.content = html
        self.soup = BeautifulSoup(html, 'html.parser')
        return True
    
    # Fallback to JavaScript-enabled browser
    print("⚠️  Empty content, trying Playwright...")
    html = self._fetch_with_playwright()
    
    if html:
        self.content = html
        self.soup = BeautifulSoup(html, 'html.parser')
        return True
    
    return False

def _fetch_with_requests(self):
    """Fast method using requests."""
    try:
        time.sleep(random.uniform(1, 2))  # Polite delay
        response = requests.get(self.url, headers=self.headers, timeout=10)
        return response.text if response.status_code == 200 else None
    except:
        return None

def _fetch_with_playwright(self):
    """Slower method with JavaScript support."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url, wait_until='networkidle', timeout=15000)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        print(f"Playwright failed: {e}")
        return None
```

### Configuration Toggle

```python
# config at top of file
USE_PLAYWRIGHT_FALLBACK = True  # Enable/disable JS rendering
REQUEST_DELAY = (1, 3)  # Min/max delay in seconds
MAX_RETRIES = 3
```

## Performance Impact

| Method | Speed | Success Rate | Cost | Complexity |
|--------|-------|--------------|------|------------|
| Current | 1s/domain | 20% | Free | ✅ Low |
| + Delays | 3s/domain | 40% | Free | ✅ Low |
| + Playwright | 8s/domain | 85% | Free | ⚠️ Medium |
| + Proxies | 5s/domain | 90% | $$ | ⚠️ Medium |
| + Cloud | 3s/domain | 95% | $$$ | ❌ High |

## Legal & Ethical Considerations

- ✅ **Public data only** - Don't scrape private/login-required content
- ✅ **Respect robots.txt** - Check before scraping
- ✅ **Rate limiting** - Don't overwhelm servers
- ✅ **Terms of Service** - Some sites prohibit scraping
- ✅ **Use APIs when available** - Preferred method

## Next Steps

1. **Immediate:** Implement request delays and retry logic (easy, free)
2. **This week:** Add Playwright fallback for JS sites (medium effort, big impact)
3. **Later:** Consider proxies only if still heavily blocked
4. **Future:** Explore APIs for specific domains (Yelp, etc.)

Would you like me to implement any of these solutions?
