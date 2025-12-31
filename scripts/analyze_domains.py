#!/usr/bin/env python3
"""
Domain Content Analysis Tool
Analyzes website content to identify health and behavioral hazards,
validates blocklist inclusion, and discovers related domains to add.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, urljoin
import time
import argparse
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Configuration
LISTS_DIR = Path(__file__).parent.parent / 'lists'
RESEARCH_DIR = Path(__file__).parent.parent / 'research'
REPORTS_DIR = RESEARCH_DIR / 'reports'
DATA_DIR = RESEARCH_DIR / 'data'
CACHE_DIR = RESEARCH_DIR / 'cache'
DOCS_DIR = RESEARCH_DIR / 'docs'
ANALYSIS_CACHE_FILE = 'analysis_cache.json'
RECOMMENDATIONS_FILE = 'recommendations.json'
TIMEOUT = 10
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
USE_PLAYWRIGHT = True  # Enable Playwright fallback for JS-heavy sites
MIN_CONTENT_LENGTH = 500  # Minimum text length to consider content sufficient

# Multiple User-Agent strings for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
]

# Global Playwright instance (reused across requests for performance)
PLAYWRIGHT_INSTANCE = None
BROWSER_INSTANCE = None

# Hazard keyword categories
HEALTH_HAZARDS = {
    'ultra_processed': ['processed', 'artificial', 'preservatives', 'additives', 'high sodium', 'trans fat', 'deep fried'],
    'sugar': ['sugar', 'sweetened', 'syrup', 'candy', 'dessert', 'sweet'],
    'fast_food': ['fast food', 'quick', 'instant', 'ready to eat', 'convenience'],
    'addictive': ['crave', 'craving', 'addictive', 'cant resist', "can't stop"],
    'nutrition_poor': ['empty calories', 'low nutrition', 'junk food']
}

BEHAVIORAL_HAZARDS = {
    'impulsive_ordering': ['order now', 'quick order', 'one-click', 'instant checkout', 'easy ordering', 'tap to order', 'order in minutes'],
    'urgency': ['limited time', 'hurry', 'expires soon', 'last chance', 'today only', 'flash sale', 'act now', 'dont wait'],
    'discounts': ['discount', 'deal', 'save', 'coupon', 'promo', 'offer', 'sale', '% off', 'percent off', 'free delivery fee'],
    'convenience': ['delivered', 'delivery', 'doorstep', 'home delivery', 'free delivery', 'fast delivery', 'door-to-door'],
    'upselling': ['combo', 'meal deal', 'upgrade', 'add-on', 'supersize', 'large', 'bundle', 'more for less'],
    'addiction_language': ['favorite', 'must-have', 'essential', 'trending', 'popular', 'bestseller', 'cant resist', 'craving']
}

MARKETING_TACTICS = {
    'social_proof': ['reviews', 'rated', 'customers love', 'popular choice', 'trending', 'top rated', 'highly rated', 'customer favorite'],
    'scarcity': ['limited', 'exclusive', 'rare', 'while supplies last', 'selling fast', 'low stock', 'almost gone'],
    'fomo': ['dont miss', 'everyone is', 'join millions', 'be the first', 'join now', 'get started', 'sign up'],
    'personalization': ['for you', 'recommended', 'picked for you', 'your favorites', 'just for you', 'tailored']
}


class AnalysisCache:
    """Manages cached analysis results (thread-safe)."""
    
    def __init__(self, cache_file):
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
        self._lock = Lock()  # Thread safety for concurrent writes
    
    def _load_cache(self):
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    print(f"✓ Loaded analysis cache with {len(data.get('analyses', {}))} cached domains")
                    return data
            except:
                print("⚠️  Cache file corrupted, starting fresh")
        return {'analyses': {}, 'last_updated': None}
    
    def save_cache(self):
        """Save cache to file (thread-safe)."""
        with self._lock:
            self.cache['last_updated'] = datetime.now().isoformat()
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
    
    def get_analysis(self, domain):
        """Get cached analysis for domain."""
        return self.cache['analyses'].get(domain)
    
    def is_cached(self, domain, max_age_days=30):
        """Check if domain has recent cached analysis."""
        if domain not in self.cache['analyses']:
            return False
        
        analysis = self.cache['analyses'][domain]
        if 'analyzed_at' not in analysis:
            return False
        
        analyzed_time = datetime.fromisoformat(analysis['analyzed_at'])
        age = datetime.now() - analyzed_time
        return age.days < max_age_days
    
    def store_analysis(self, domain, analysis):
        """Store analysis result (thread-safe)."""
        with self._lock:
            self.cache['analyses'][domain] = analysis


class RecommendationEngine:
    """Manages domain recommendations for additions and removals (thread-safe)."""
    
    def __init__(self, recommendations_file):
        self.rec_file = Path(recommendations_file)
        self.recommendations = self._load_recommendations()
        self._lock = Lock()  # Thread safety for concurrent updates
    
    def _load_recommendations(self):
        """Load recommendations from file."""
        if self.rec_file.exists():
            try:
                with open(self.rec_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'additions': [],
            'removals': [],
            'last_updated': None
        }
    
    def save_recommendations(self):
        """Save recommendations to file (thread-safe)."""
        with self._lock:
            self.recommendations['last_updated'] = datetime.now().isoformat()
            with open(self.rec_file, 'w') as f:
                json.dump(self.recommendations, f, indent=2)
            print(f"\n✓ Recommendations saved to: {self.rec_file}")
    
    def add_addition_recommendation(self, domain, category, reason, source_domain=None):
        """Recommend adding a domain (thread-safe)."""
        # Skip common third-party domains
        skip_domains = {
            'facebook.com', 'twitter.com', 'instagram.com', 'youtube.com',
            'google.com', 'apple.com', 'amazon.com', 'linkedin.com',
            'pinterest.com', 'tiktok.com', 'snapchat.com'
        }
        
        if domain in skip_domains:
            return  # Don't recommend blocking major platforms
        
        rec = {
            'domain': domain,
            'category': category,
            'reason': reason,
            'source': source_domain,
            'detected_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        # Check if already recommended (with lock)
        with self._lock:
            for existing in self.recommendations['additions']:
                if existing['domain'] == domain:
                    return  # Already recommended
            
            self.recommendations['additions'].append(rec)
    
    def add_removal_recommendation(self, domain, category, reason, risk_score):
        """Recommend removing a domain (thread-safe)."""
        # Only recommend removal if we successfully analyzed the domain
        # Don't recommend removal if analysis failed (no content)
        if risk_score is None or risk_score == 0:
            return  # Skip failed analyses
        
        rec = {
            'domain': domain,
            'category': category,
            'reason': reason,
            'risk_score': risk_score,
            'detected_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        # Check if already recommended (with lock)
        with self._lock:
            for existing in self.recommendations['removals']:
                if existing['domain'] == domain:
                    return
            
            self.recommendations['removals'].append(rec)
    
    def get_summary(self):
        """Get recommendations summary."""
        pending_additions = sum(1 for r in self.recommendations['additions'] if r['status'] == 'pending')
        pending_removals = sum(1 for r in self.recommendations['removals'] if r['status'] == 'pending')
        return {
            'additions': pending_additions,
            'removals': pending_removals
        }


class DomainAnalyzer:
    """Analyzes domain content for health and behavioral hazards."""
    
    def __init__(self, domain):
        self.domain = domain
        self.url = f"https://{domain}" if not domain.startswith('http') else domain
        self.content = None
        self.soup = None
        self.analysis = {
            'domain': domain,
            'analyzed_at': datetime.now().isoformat(),
            'accessible': False,
            'health_hazards': {},
            'behavioral_hazards': {},
            'marketing_tactics': {},
            'promoted_products': [],
            'related_domains': [],
            'risk_score': 0,
            'justification': []
        }
    
    def fetch_content(self):
        """Fetch website content with hybrid approach: requests first, Playwright fallback."""
        # Add random delay to avoid rate limiting
        time.sleep(random.uniform(1, 2))
        
        # Try fast method first (requests)
        success = self._fetch_with_requests()
        if success:
            return True
        
        # If requests failed or returned insufficient content, try Playwright
        if USE_PLAYWRIGHT:
            print(f"  → Playwright fallback for {self.domain}...", end=' ')
            return self._fetch_with_playwright()
        
        return False
    
    def _fetch_with_requests(self):
        """Fast fetch using requests library."""
        try:
            # Create session with realistic headers
            session = requests.Session()
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
            
            response = session.get(self.url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
            response.raise_for_status()
            self.content = response.text
            self.soup = BeautifulSoup(self.content, 'html.parser')
            
            # Check if we actually got sufficient content
            for script in self.soup(['script', 'style']):
                script.decompose()
            text = self.soup.get_text(strip=True)
            
            if len(text) < MIN_CONTENT_LENGTH:
                self.analysis['error'] = f'Insufficient content ({len(text)} chars, needs {MIN_CONTENT_LENGTH}+)'
                self.analysis['accessible'] = False
                return False
            
            self.analysis['accessible'] = True
            return True
        except Exception as e:
            self.analysis['error'] = str(e)
            return False
    
    def _fetch_with_playwright(self):
        """Fallback fetch using Playwright for JavaScript-heavy sites."""
        global PLAYWRIGHT_INSTANCE, BROWSER_INSTANCE
        
        try:
            # Initialize Playwright and Browser if needed (reuse for performance)
            if PLAYWRIGHT_INSTANCE is None:
                PLAYWRIGHT_INSTANCE = sync_playwright().start()
                BROWSER_INSTANCE = PLAYWRIGHT_INSTANCE.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
            
            # Create new page
            context = BROWSER_INSTANCE.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={'width': 1920, 'height': 1080},
            )
            page = context.new_page()
            
            # Block images/fonts/media for speed (we only need text)
            page.route('**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,mp4,webm,mp3}', 
                      lambda route: route.abort())
            
            # Navigate and wait for content to load (increased timeout)
            try:
                page.goto(self.url, wait_until='domcontentloaded', timeout=20000)
                # Wait a bit for dynamic content (shorter wait)
                page.wait_for_timeout(3000)
            except PlaywrightTimeout:
                # If networkidle times out, try with just domcontentloaded
                pass
            
            # Extract HTML
            html = page.content()
            
            # Cleanup
            context.close()
            
            # Parse with BeautifulSoup
            self.content = html
            self.soup = BeautifulSoup(self.content, 'html.parser')
            
            # Check content
            for script in self.soup(['script', 'style']):
                script.decompose()
            text = self.soup.get_text(strip=True)
            
            if len(text) < MIN_CONTENT_LENGTH:
                self.analysis['error'] = f'Playwright: Insufficient content ({len(text)} chars)'
                self.analysis['accessible'] = False
                return False
            
            self.analysis['accessible'] = True
            self.analysis['method'] = 'playwright'
            return True
            
        except PlaywrightTimeout:
            self.analysis['error'] = 'Playwright timeout (15s)'
            return False
        except Exception as e:
            self.analysis['error'] = f'Playwright error: {str(e)}'
            return False
    
    def analyze_text_content(self):
        """Extract and analyze text content."""
        if not self.soup:
            return
        
        # Get all visible text
        for script in self.soup(['script', 'style']):
            script.decompose()
        
        text = self.soup.get_text().lower()
        
        # ALSO analyze SEO metadata (more reliable than JS-rendered content)
        seo_text = self._extract_seo_metadata()
        combined_text = text + ' ' + seo_text
        
        # Check for health hazards
        for category, keywords in HEALTH_HAZARDS.items():
            matches = sum(1 for kw in keywords if kw in combined_text)
            if matches > 0:
                self.analysis['health_hazards'][category] = matches
        
        # Check for behavioral hazards
        for category, keywords in BEHAVIORAL_HAZARDS.items():
            matches = sum(1 for kw in keywords if kw in combined_text)
            if matches > 0:
                self.analysis['behavioral_hazards'][category] = matches
        
        # Check for marketing tactics
        for category, keywords in MARKETING_TACTICS.items():
            matches = sum(1 for kw in keywords if kw in combined_text)
            if matches > 0:
                self.analysis['marketing_tactics'][category] = matches
    
    def _extract_seo_metadata(self):
        """Extract SEO metadata that reveals marketing tactics."""
        if not self.soup:
            return ""
        
        metadata_text = []
        
        # Title tag - often has urgency/scarcity language
        title = self.soup.find('title')
        if title:
            metadata_text.append(title.get_text().lower())
        
        # Meta description - marketing copy
        meta_desc = self.soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            metadata_text.append(meta_desc['content'].lower())
        
        # Keywords meta tag (if present)
        meta_keywords = self.soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            metadata_text.append(meta_keywords['content'].lower())
        
        # Open Graph tags - social media marketing
        og_tags = ['og:title', 'og:description', 'og:site_name']
        for tag in og_tags:
            og_meta = self.soup.find('meta', attrs={'property': tag})
            if og_meta and og_meta.get('content'):
                metadata_text.append(og_meta['content'].lower())
        
        # Twitter Card tags
        twitter_tags = ['twitter:title', 'twitter:description']
        for tag in twitter_tags:
            tw_meta = self.soup.find('meta', attrs={'name': tag})
            if tw_meta and tw_meta.get('content'):
                metadata_text.append(tw_meta['content'].lower())
        
        # Structured data (JSON-LD) - product/offer schemas
        json_ld_scripts = self.soup.find_all('script', attrs={'type': 'application/ld+json'})
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                # Extract relevant marketing text from structured data
                if isinstance(data, dict):
                    if '@type' in data:
                        if data['@type'] in ['Product', 'Offer', 'AggregateOffer']:
                            if 'name' in data:
                                metadata_text.append(str(data['name']).lower())
                            if 'description' in data:
                                metadata_text.append(str(data['description']).lower())
                            if 'offers' in data and isinstance(data['offers'], dict):
                                if 'priceValidUntil' in data['offers']:
                                    metadata_text.append('limited time offer')
                        elif data['@type'] == 'Restaurant':
                            if 'name' in data:
                                metadata_text.append(str(data['name']).lower())
                            if 'description' in data:
                                metadata_text.append(str(data['description']).lower())
            except:
                pass  # Invalid JSON-LD, skip
        
        # Store metadata for debugging
        self.analysis['seo_metadata'] = ' '.join(metadata_text)[:500]  # Store sample
        
        return ' '.join(metadata_text)
    
    def extract_products(self):
        """Extract promoted products/services."""
        if not self.soup:
            return
        
        products = []
        
        # Look for product names in various HTML structures
        for selector in ['.product', '.menu-item', '.item', 'h3', 'h4']:
            items = self.soup.select(selector)
            for item in items[:10]:  # Limit to first 10
                text = item.get_text(strip=True)
                if text and len(text) < 100:  # Reasonable product name length
                    products.append(text)
        
        self.analysis['promoted_products'] = products[:15]  # Store max 15
    
    def find_related_domains(self):
        """Extract links to related domains."""
        if not self.soup:
            return
        
        related = set()
        
        for link in self.soup.find_all('a', href=True):
            href = link['href']
            parsed = urlparse(href)
            
            if parsed.netloc and parsed.netloc != self.domain:
                # Clean domain
                domain = parsed.netloc.replace('www.', '')
                if '.' in domain and len(domain) < 50:  # Basic validation
                    related.add(domain)
        
        self.analysis['related_domains'] = sorted(list(related))[:20]  # Max 20
    
    def calculate_risk_score(self):
        """Calculate overall risk score (0-100)."""
        score = 0
        
        # Health hazards (30 points max)
        health_count = sum(self.analysis['health_hazards'].values())
        score += min(health_count * 3, 30)
        
        # Behavioral hazards (40 points max)
        behavior_count = sum(self.analysis['behavioral_hazards'].values())
        score += min(behavior_count * 4, 40)
        
        # Marketing tactics (30 points max)
        marketing_count = sum(self.analysis['marketing_tactics'].values())
        score += min(marketing_count * 3, 30)
        
        self.analysis['risk_score'] = min(score, 100)
    
    def generate_justification(self):
        """Generate human-readable justification for blocking."""
        reasons = []
        
        if self.analysis['health_hazards']:
            hazards = ', '.join(self.analysis['health_hazards'].keys())
            reasons.append(f"Promotes health hazards: {hazards}")
        
        if self.analysis['behavioral_hazards']:
            hazards = ', '.join(self.analysis['behavioral_hazards'].keys())
            reasons.append(f"Uses behavioral manipulation: {hazards}")
        
        if self.analysis['marketing_tactics']:
            tactics = ', '.join(self.analysis['marketing_tactics'].keys())
            reasons.append(f"Employs aggressive marketing: {tactics}")
        
        if self.analysis['risk_score'] > 70:
            reasons.append("HIGH RISK: Multiple concerning patterns detected")
        elif self.analysis['risk_score'] > 40:
            reasons.append("MODERATE RISK: Several concerning patterns detected")
        
        self.analysis['justification'] = reasons
    
    def analyze(self):
        """Run complete analysis."""
        print(f"Analyzing {self.domain}...", end=' ')
        
        if not self.fetch_content():
            print("❌ Failed to access")
            return self.analysis
        
        self.analyze_text_content()
        self.extract_products()
        self.find_related_domains()
        self.calculate_risk_score()
        self.generate_justification()
        
        print(f"✓ Risk Score: {self.analysis['risk_score']}/100")
        return self.analysis


def load_domains_from_list(category_file):
    """Load domains from a blocklist file."""
    filepath = LISTS_DIR / category_file
    domains = []
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments, empty lines, www/api subdomains
            if line and not line.startswith('#'):
                if not line.startswith('www.') and not line.startswith('api.') and not line.startswith('drive.'):
                    domains.append(line)
    
    return domains


def analyze_domain_worker(domain, cache, force_reanalysis, category_name, recommendations, existing_domains):
    """Worker function for parallel domain analysis (thread-safe)."""
    # Check cache first (unless force reanalysis)
    if cache and cache.is_cached(domain) and not force_reanalysis:
        result = cache.get_analysis(domain)
        print(f"{domain}... ✓ Using cached analysis")
    else:
        analyzer = DomainAnalyzer(domain)
        result = analyzer.analyze()
        
        if cache:
            cache.store_analysis(domain, result)  # Thread-safe
    
    # Process recommendations (thread-safe)
    if recommendations and result['accessible']:
        # Check if domain should be removed (low risk score)
        if result['risk_score'] < 30:
            recommendations.add_removal_recommendation(
                domain,
                category_name,
                f"Low risk score ({result['risk_score']}/100), may not warrant blocking",
                result['risk_score']
            )
        
        # Check for related domains to add
        for related_domain in result.get('related_domains', [])[:5]:  # Top 5 only
            # Check if it's not already in any list
            if existing_domains and related_domain not in existing_domains:
                recommendations.add_addition_recommendation(
                    related_domain,
                    category_name,
                    f"Found via {domain} analysis, appears to be related service",
                    domain
                )
    
    return result


def analyze_category(category_name, category_file, sample_size=5, cache=None, recommendations=None, existing_domains=None, force_reanalysis=False, parallel=False, max_workers=5):
    """Analyze a sample of domains from a category.
    
    Args:
        category_name: Name of the category
        category_file: Filename of the blocklist
        sample_size: Number of domains to analyze (-1 for all)
        cache: AnalysisCache instance
        recommendations: RecommendationEngine instance
        existing_domains: Set of domains already in blocklists
        force_reanalysis: Ignore cache
        parallel: Enable parallel processing
        max_workers: Number of concurrent threads (default 5)
    """
    print(f"\n{'='*60}")
    print(f"Analyzing Category: {category_name}")
    print(f"{'='*60}")
    
    domains = load_domains_from_list(category_file)
    print(f"Found {len(domains)} unique base domains")
    
    if cache and not force_reanalysis:
        cached_count = sum(1 for d in domains if cache.is_cached(d))
        print(f"Cached: {cached_count}, Need analysis: {len(domains) - cached_count}")
    elif force_reanalysis:
        print(f"🔄 Force reanalysis mode: ignoring cache")
    
    if sample_size == -1:
        print(f"Analyzing ALL {len(domains)} domains...\n")
        sample_size = len(domains)
    else:
        print(f"Analyzing up to {sample_size} domains...\n")
    
    # Limit to sample size
    domains_to_analyze = domains[:sample_size]
    
    if parallel:
        print(f"⚡ Parallel mode: {max_workers} workers\n")
        results = analyze_parallel(
            domains_to_analyze,
            cache,
            force_reanalysis,
            category_name,
            recommendations,
            existing_domains,
            max_workers
        )
    else:
        results = analyze_sequential(
            domains_to_analyze,
            cache,
            force_reanalysis,
            category_name,
            recommendations,
            existing_domains
        )
    
    return results


def analyze_sequential(domains, cache, force_reanalysis, category_name, recommendations, existing_domains):
    """Sequential domain analysis (original method)."""
    results = []
    
    for domain in domains:
        result = analyze_domain_worker(
            domain,
            cache,
            force_reanalysis,
            category_name,
            recommendations,
            existing_domains
        )
        results.append(result)
    
    return results


def analyze_parallel(domains, cache, force_reanalysis, category_name, recommendations, existing_domains, max_workers):
    """Parallel domain analysis using ThreadPoolExecutor."""
    results = []
    completed = 0
    total = len(domains)
    
    # Use ThreadPoolExecutor for concurrent analysis
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_domain = {
            executor.submit(
                analyze_domain_worker,
                domain,
                cache,
                force_reanalysis,
                category_name,
                recommendations,
                existing_domains
            ): domain
            for domain in domains
        }
        
        # Process completed tasks as they finish
        for future in as_completed(future_to_domain):
            domain = future_to_domain[future]
            try:
                result = future.result()
                results.append(result)
                completed += 1
                
                # Progress indicator
                if completed % 10 == 0 or completed == total:
                    print(f"Progress: {completed}/{total} domains analyzed ({completed/total*100:.1f}%)")
                    
            except Exception as e:
                print(f"❌ Error analyzing {domain}: {e}")
                # Create error result
                results.append({
                    'domain': domain,
                    'analyzed_at': datetime.now().isoformat(),
                    'accessible': False,
                    'error': str(e),
                    'risk_score': 0
                })
    
    return results


def generate_html_report(category_name, results):
    """Generate interactive HTML report with embedded data."""
    report_path = REPORTS_DIR / f"{category_name.lower()}_analysis.html"
    
    # Data file path (relative to report) - still save JSON for external access
    data_filename = f"{category_name.lower().replace(' & ', '_').replace(' ', '_')}_data.json"
    
    # Embed data directly in HTML to avoid CORS issues
    import json
    embedded_data = json.dumps(results, indent=2)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{category_name} - Analysis Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .nav-bar {{
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .nav-links {{
            display: flex;
            gap: 15px;
        }}
        .nav-link {{
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 500;
            transition: background 0.3s;
        }}
        .nav-link:hover {{
            background: #764ba2;
        }}
        .nav-link.home {{
            background: #27ae60;
        }}
        .nav-link.home:hover {{
            background: #229954;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            position: relative;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .header .timestamp {{
            opacity: 0.9;
            font-size: 0.9em;
        }}
        .controls {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .controls h3 {{
            margin-top: 0;
        }}
        .filter-group {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 10px;
        }}
        .filter-btn {{
            padding: 8px 16px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
        }}
        .filter-btn:hover {{
            background: #f0f0ff;
        }}
        .filter-btn.active {{
            background: #667eea;
            color: white;
        }}
        .search-box {{
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            margin-bottom: 10px;
        }}
        .search-box:focus {{
            outline: none;
            border-color: #667eea;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .chart-container h2 {{
            margin-top: 0;
            color: #333;
        }}
        .chart-wrapper {{
            position: relative;
            height: 400px;
        }}
        .domain-list {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .domain-list h2 {{
            margin-top: 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .domain-count {{
            font-size: 0.6em;
            color: #666;
            font-weight: normal;
        }}
        .domain-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .domain-item:hover {{
            background: #f9f9f9;
        }}
        .domain-item:last-child {{
            border-bottom: none;
        }}
        .domain-name {{
            font-weight: 500;
            color: #333;
            flex: 1;
        }}
        .domain-details {{
            display: none;
            padding: 15px;
            background: #f5f5f5;
            margin-top: 10px;
            border-radius: 5px;
            font-size: 0.9em;
        }}
        .domain-details.show {{
            display: block;
        }}
        .hazard-tags {{
            display: flex;
            gap: 5px;
            flex-wrap: wrap;
            margin: 10px 0;
        }}
        .hazard-tag {{
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            background: #e3f2fd;
            color: #1976d2;
        }}
        .hazard-tag.health {{ background: #ffebee; color: #c62828; }}
        .hazard-tag.behavioral {{ background: #fff3e0; color: #e65100; }}
        .hazard-tag.marketing {{ background: #e8f5e9; color: #2e7d32; }}
        .risk-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            color: white;
            margin-left: 10px;
        }}
        .risk-high {{ background: #e74c3c; }}
        .risk-medium {{ background: #f39c12; }}
        .risk-low {{ background: #27ae60; }}
        .risk-none {{ background: #95a5a6; }}
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .loading {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
        .error {{
            background: #ffebee;
            color: #c62828;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        @media (max-width: 768px) {{
            .grid-2 {{ grid-template-columns: 1fr; }}
            .nav-bar {{ flex-direction: column; gap: 10px; }}
            .nav-links {{ width: 100%; justify-content: center; }}
        }}
    </style>
</head>
<body>
    <nav class="nav-bar">
        <div class="nav-links">
            <a href="../../index.html" class="nav-link home">🏠 Home</a>
            <a href="food & delivery_analysis.html" class="nav-link">Food & Delivery</a>
            <a href="cosmetics & beauty_analysis.html" class="nav-link">Cosmetics</a>
            <a href="conglomerates_analysis.html" class="nav-link">Conglomerates</a>
        </div>
    </nav>

    <div class="header">
        <h1>{category_name} - Content Analysis</h1>
        <p class="timestamp" id="timestamp">Loading...</p>
    </div>

    <div id="loading" class="loading">
        <h2>Loading analysis data...</h2>
        <p>Please wait while we fetch the results</p>
    </div>

    <div id="error" class="error" style="display: none;">
        <h2>Error Loading Data</h2>
        <p id="error-message"></p>
    </div>

    <div id="content" style="display: none;">
        <div class="controls">
            <h3>Filter Domains</h3>
            <input type="text" class="search-box" id="searchBox" placeholder="Search domains...">
            <div class="filter-group">
                <button class="filter-btn active" data-filter="all">All Domains</button>
                <button class="filter-btn" data-filter="high">High Risk (50+)</button>
                <button class="filter-btn" data-filter="medium">Medium Risk (30-49)</button>
                <button class="filter-btn" data-filter="low">Low Risk (< 30)</button>
                <button class="filter-btn" data-filter="failed">Failed Access</button>
            </div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="totalDomains">0</div>
                <div class="stat-label">Domains Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="accessibleDomains">0</div>
                <div class="stat-label">Successfully Accessed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="avgRisk">0</div>
                <div class="stat-label">Average Risk Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="highRiskDomains">0</div>
                <div class="stat-label">High Risk Domains</div>
            </div>
        </div>

        <div class="grid-2">
            <div class="chart-container">
                <h2>Health Hazards Detected</h2>
                <div class="chart-wrapper">
                    <canvas id="healthChart"></canvas>
                </div>
            </div>
            <div class="chart-container">
                <h2>Behavioral Manipulation</h2>
                <div class="chart-wrapper">
                    <canvas id="behavioralChart"></canvas>
                </div>
            </div>
        </div>

        <div class="chart-container">
            <h2>Marketing Tactics Distribution</h2>
            <div class="chart-wrapper">
                <canvas id="marketingChart"></canvas>
            </div>
        </div>

        <div class="chart-container">
            <h2>Risk Score Distribution</h2>
            <div class="chart-wrapper">
                <canvas id="riskChart"></canvas>
            </div>
        </div>

        <div class="domain-list">
            <h2>Domain Details <span class="domain-count" id="domainCount"></span></h2>
            <div id="domainListContainer"></div>
        </div>
    </div>

    <script>
        let allData = [];
        let currentFilter = 'all';
        let searchQuery = '';

        // Embedded data to avoid CORS issues when opening locally
        allData = {embedded_data};
        
        // Initialize page immediately with embedded data
        document.addEventListener('DOMContentLoaded', () => {{
            document.getElementById('loading').style.display = 'none';
            document.getElementById('content').style.display = 'block';
            initializePage(allData);
        }});

        function initializePage(data) {{
            // Update timestamp
            if (data.length > 0 && data[0].analyzed_at) {{
                const date = new Date(data[0].analyzed_at);
                document.getElementById('timestamp').textContent = 
                    `Generated: ${{date.toLocaleString()}}`;
            }}

            // Calculate stats
            const accessible = data.filter(d => d.accessible);
            const avgRisk = accessible.length > 0
                ? (accessible.reduce((sum, d) => sum + d.risk_score, 0) / accessible.length).toFixed(1)
                : 0;
            const highRisk = accessible.filter(d => d.risk_score > 50).length;

            document.getElementById('totalDomains').textContent = data.length;
            document.getElementById('accessibleDomains').textContent = accessible.length;
            document.getElementById('avgRisk').textContent = avgRisk;
            document.getElementById('highRiskDomains').textContent = highRisk;

            // Aggregate hazards
            const healthHazards = {{}};
            const behavioralHazards = {{}};
            const marketingTactics = {{}};

            accessible.forEach(result => {{
                Object.entries(result.health_hazards || {{}}).forEach(([key, val]) => {{
                    healthHazards[key] = (healthHazards[key] || 0) + val;
                }});
                Object.entries(result.behavioral_hazards || {{}}).forEach(([key, val]) => {{
                    behavioralHazards[key] = (behavioralHazards[key] || 0) + val;
                }});
                Object.entries(result.marketing_tactics || {{}}).forEach(([key, val]) => {{
                    marketingTactics[key] = (marketingTactics[key] || 0) + val;
                }});
            }});

            // Create charts
            createHealthChart(healthHazards);
            createBehavioralChart(behavioralHazards);
            createMarketingChart(marketingTactics);
            createRiskChart(accessible);

            // Render domain list
            renderDomainList(data);

            // Setup filters
            document.querySelectorAll('.filter-btn').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    currentFilter = btn.dataset.filter;
                    renderDomainList(data);
                }});
            }});

            // Setup search
            document.getElementById('searchBox').addEventListener('input', (e) => {{
                searchQuery = e.target.value.toLowerCase();
                renderDomainList(data);
            }});
        }}

        function createHealthChart(data) {{
            const ctx = document.getElementById('healthChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: Object.keys(data),
                    datasets: [{{
                        label: 'Occurrences',
                        data: Object.values(data),
                        backgroundColor: 'rgba(231, 76, 60, 0.7)',
                        borderColor: 'rgba(231, 76, 60, 1)',
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }}
                }}
            }});
        }}

        function createBehavioralChart(data) {{
            const ctx = document.getElementById('behavioralChart').getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: Object.keys(data),
                    datasets: [{{
                        data: Object.values(data),
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.7)',
                            'rgba(54, 162, 235, 0.7)',
                            'rgba(255, 206, 86, 0.7)',
                            'rgba(75, 192, 192, 0.7)',
                            'rgba(153, 102, 255, 0.7)',
                            'rgba(255, 159, 64, 0.7)'
                        ]
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false
                }}
            }});
        }}

        function createMarketingChart(data) {{
            const ctx = document.getElementById('marketingChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: Object.keys(data),
                    datasets: [{{
                        label: 'Occurrences',
                        data: Object.values(data),
                        backgroundColor: 'rgba(52, 152, 219, 0.7)',
                        borderColor: 'rgba(52, 152, 219, 1)',
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {{ legend: {{ display: false }} }}
                }}
            }});
        }}

        function createRiskChart(data) {{
            const ctx = document.getElementById('riskChart').getContext('2d');
            const sorted = data.sort((a, b) => b.risk_score - a.risk_score).slice(0, 15);
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: sorted.map(d => d.domain),
                    datasets: [{{
                        label: 'Risk Score',
                        data: sorted.map(d => d.risk_score),
                        backgroundColor: sorted.map(d => 
                            d.risk_score > 50 ? 'rgba(231, 76, 60, 0.7)' :
                            d.risk_score > 30 ? 'rgba(243, 156, 18, 0.7)' :
                            'rgba(46, 204, 113, 0.7)'
                        ),
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{ beginAtZero: true, max: 100 }}
                    }},
                    plugins: {{ legend: {{ display: false }} }}
                }}
            }});
        }}

        function filterDomains(data) {{
            let filtered = data;

            // Apply risk filter
            if (currentFilter === 'high') {{
                filtered = filtered.filter(d => d.accessible && d.risk_score >= 50);
            }} else if (currentFilter === 'medium') {{
                filtered = filtered.filter(d => d.accessible && d.risk_score >= 30 && d.risk_score < 50);
            }} else if (currentFilter === 'low') {{
                filtered = filtered.filter(d => d.accessible && d.risk_score < 30);
            }} else if (currentFilter === 'failed') {{
                filtered = filtered.filter(d => !d.accessible);
            }}

            // Apply search filter
            if (searchQuery) {{
                filtered = filtered.filter(d => d.domain.toLowerCase().includes(searchQuery));
            }}

            return filtered;
        }}

        function renderDomainList(data) {{
            const filtered = filterDomains(data);
            const container = document.getElementById('domainListContainer');
            document.getElementById('domainCount').textContent = `(${{filtered.length}} domains)`;

            container.innerHTML = filtered.map((domain, index) => {{
                const riskClass = domain.risk_score >= 50 ? 'risk-high' :
                                 domain.risk_score >= 30 ? 'risk-medium' :
                                 domain.risk_score > 0 ? 'risk-low' : 'risk-none';
                
                let hazardTags = '';
                if (domain.accessible) {{
                    const health = Object.keys(domain.health_hazards || {{}}).map(h => 
                        `<span class="hazard-tag health">${{h}}</span>`
                    ).join('');
                    const behavioral = Object.keys(domain.behavioral_hazards || {{}}).map(h => 
                        `<span class="hazard-tag behavioral">${{h}}</span>`
                    ).join('');
                    const marketing = Object.keys(domain.marketing_tactics || {{}}).map(h => 
                        `<span class="hazard-tag marketing">${{h}}</span>`
                    ).join('');
                    
                    if (health || behavioral || marketing) {{
                        hazardTags = `<div class="hazard-tags">${{health}}${{behavioral}}${{marketing}}</div>`;
                    }}
                }}

                const detailsHtml = domain.accessible ? `
                    <div class="domain-details" id="details-${{index}}">
                        ${{hazardTags}}
                        ${{domain.justification && domain.justification.length > 0 ? `
                            <strong>Justification:</strong>
                            <ul>${{domain.justification.map(j => `<li>${{j}}</li>`).join('')}}</ul>
                        ` : ''}}
                        ${{domain.method ? `<p><em>Analysis method: ${{domain.method}}</em></p>` : ''}}
                    </div>
                ` : `
                    <div class="domain-details" id="details-${{index}}">
                        <p><strong>Error:</strong> ${{domain.error || 'Unknown error'}}</p>
                    </div>
                `;

                return `
                    <div class="domain-item" onclick="toggleDetails(${{index}})">
                        <span class="domain-name">${{domain.domain}}</span>
                        <span class="risk-badge ${{riskClass}}">${{domain.risk_score}}/100</span>
                    </div>
                    ${{detailsHtml}}
                `;
            }}).join('');
        }}

        function toggleDetails(index) {{
            const details = document.getElementById(`details-${{index}}`);
            details.classList.toggle('show');
        }}
    </script>
</body>
</html>
"""
    
    
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    print(f"✓ HTML Report saved to: {report_path}")
    return report_path


def generate_summary_stats():
    """Generate summary statistics from all JSON data files"""
    try:
        all_data = []
        categories = {}
        
        # Load all JSON data files
        for json_file in DATA_DIR.glob('*_data.json'):
            with open(json_file, 'r') as f:
                data = json.load(f)
                all_data.extend(data)
                # Extract category name from filename
                cat_name = json_file.stem.replace('_data', '')
                categories[cat_name] = len(data)
        
        if not all_data:
            return
        
        # Calculate aggregate statistics
        total = len(all_data)
        accessible = [d for d in all_data if d.get('accessible', False)]
        accessible_count = len(accessible)
        
        avg_risk = sum(d.get('risk_score', 0) for d in accessible) / accessible_count if accessible_count > 0 else 0
        access_rate = (accessible_count / total * 100) if total > 0 else 0
        high_risk = sum(1 for d in accessible if d.get('risk_score', 0) >= 50)
        
        # Load DNS verification stats from cache if available
        dns_stats = {}
        lists_dir = Path(__file__).parent.parent / 'lists'
        dns_cache_file = lists_dir / '.domain_cache.json'
        if dns_cache_file.exists():
            try:
                with open(dns_cache_file, 'r') as f:
                    cache_data = json.load(f)
                    dns_stats = {
                        'verified_domains': len(cache_data.get('verified', {})),
                        'unverified_domains': len(cache_data.get('not_found', {})),
                        'total_dns_checked': len(cache_data.get('verified', {})) + len(cache_data.get('not_found', {})),
                        'last_dns_check': cache_data.get('last_updated')
                    }
            except Exception as e:
                print(f"Note: Could not load DNS cache stats: {e}")
        
        # Calculate blocklist statistics
        blocklist_stats = {}
        for list_file in ['food.txt', 'cosmetics.txt', 'conglomerates.txt', 'blackout-ultra.txt']:
            list_path = lists_dir / list_file
            if list_path.exists():
                with open(list_path, 'r') as f:
                    domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    blocklist_stats[list_file.replace('.txt', '')] = len(domains)
        
        summary = {
            'total_domains': total,
            'accessible_count': accessible_count,
            'avg_risk_score': round(avg_risk, 1),
            'access_rate': round(access_rate, 0),
            'high_risk_count': high_risk,
            'categories': categories,
            'dns_verification': dns_stats,
            'blocklists': blocklist_stats,
            'generated_at': datetime.now().isoformat()
        }
        
        # Save summary JSON file
        summary_path = DATA_DIR / 'summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✓ Summary statistics saved to: {summary_path}")
        
        # Auto-update index.html with latest stats
        try:
            import subprocess
            update_script = Path(__file__).parent / 'update_index.py'
            if update_script.exists():
                result = subprocess.run(['python3', str(update_script)], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print("✓ Index.html automatically updated with latest stats")
        except Exception as e:
            print(f"Note: Could not auto-update index.html: {e}")
            print("      Run: python3 scripts/update_index.py")
            
    except Exception as e:
        print(f"Warning: Could not generate summary stats: {e}")


def generate_markdown_report(category_name, results):
    """Generate markdown research report."""
    report_path = DOCS_DIR / f"{category_name.lower()}_analysis.md"
    
    with open(report_path, 'w') as f:
        f.write(f"# {category_name} - Content Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Domains Analyzed:** {len(results)}\n\n")
        
        # Summary statistics
        accessible_results = [r for r in results if r['accessible']]
        avg_risk = sum(r['risk_score'] for r in accessible_results) / len(accessible_results) if accessible_results else 0
        accessible_count = len(accessible_results)
        
        f.write("## Summary\n\n")
        f.write(f"- **Accessible domains:** {accessible_count}/{len(results)}\n")
        f.write(f"- **Average Risk Score:** {avg_risk:.1f}/100\n\n")
        
        # Hazard clusters
        f.write("## Hazard Clusters\n\n")
        
        all_health = {}
        all_behavioral = {}
        all_marketing = {}
        
        for result in results:
            if not result['accessible']:
                continue
            
            for hazard, count in result['health_hazards'].items():
                all_health[hazard] = all_health.get(hazard, 0) + count
            
            for hazard, count in result['behavioral_hazards'].items():
                all_behavioral[hazard] = all_behavioral.get(hazard, 0) + count
            
            for tactic, count in result['marketing_tactics'].items():
                all_marketing[tactic] = all_marketing.get(tactic, 0) + count
        
        f.write("### Health Hazards\n\n")
        for hazard, count in sorted(all_health.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- **{hazard}**: {count} occurrences\n")
        
        f.write("\n### Behavioral Hazards\n\n")
        for hazard, count in sorted(all_behavioral.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- **{hazard}**: {count} occurrences\n")
        
        f.write("\n### Marketing Tactics\n\n")
        for tactic, count in sorted(all_marketing.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- **{tactic}**: {count} occurrences\n")
        
        # Individual domain analysis
        f.write("\n## Individual Domain Analysis\n\n")
        
        for result in results:
            f.write(f"### {result['domain']}\n\n")
            
            if not result['accessible']:
                f.write(f"❌ **Not accessible:** {result.get('error', 'Unknown error')}\n\n")
                continue
            
            f.write(f"**Risk Score:** {result['risk_score']}/100\n\n")
            
            if result['justification']:
                f.write("**Justification for Blocking:**\n\n")
                for reason in result['justification']:
                    f.write(f"- {reason}\n")
                f.write("\n")
            
            if result['promoted_products']:
                f.write("**Sample Products/Services:**\n\n")
                for product in result['promoted_products'][:5]:
                    f.write(f"- {product}\n")
                f.write("\n")
            
            if result['related_domains']:
                f.write("**Related Domains Found:**\n\n")
                for domain in result['related_domains'][:10]:
                    f.write(f"- `{domain}`\n")
                f.write("\n")
            
            f.write("---\n\n")
    
    print(f"\n✓ Report saved to: {report_path}")


def main():
    """Main analysis function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Analyze domain content for health and behavioral hazards',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Analyze 5 domains per category (default)
  %(prog)s --sample-size 10          # Analyze 10 domains per category
  %(prog)s --all                     # Analyze ALL domains (slow)
  %(prog)s --force                   # Ignore cache, reanalyze everything
  %(prog)s --category food           # Only analyze food category
  %(prog)s --all --force             # Full reanalysis of everything
        """
    )
    parser.add_argument(
        '--sample-size', '-n',
        type=int,
        default=5,
        help='Number of domains to analyze per category (default: 5)'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Analyze ALL domains in each category (ignores --sample-size)'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force reanalysis, ignore existing cache'
    )
    parser.add_argument(
        '--category', '-c',
        choices=['food', 'cosmetics', 'conglomerates'],
        help='Only analyze specific category'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching entirely (same as --force but don\'t save results)'
    )
    parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='Enable parallel processing for faster analysis'
    )
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=5,
        help='Number of concurrent workers for parallel mode (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Determine sample size
    sample_size = -1 if args.all else args.sample_size
    force_reanalysis = args.force or args.no_cache
    use_cache = not args.no_cache
    parallel = args.parallel
    max_workers = args.workers
    
    print("DOMAIN CONTENT ANALYSIS TOOL")
    print("="*60)
    print(f"Sample size: {'ALL' if sample_size == -1 else sample_size} domains per category")
    print(f"Cache mode: {'DISABLED' if args.no_cache else 'FORCE REANALYSIS' if args.force else 'ENABLED'}")
    print(f"Processing mode: {'PARALLEL (' + str(max_workers) + ' workers)' if parallel else 'SEQUENTIAL'}")
    if args.category:
        print(f"Category filter: {args.category}")
    print("="*60)
    print()
    
    # Ensure directories exist
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize cache and recommendations
    cache = AnalysisCache(CACHE_DIR / ANALYSIS_CACHE_FILE) if use_cache else None
    recommendations = RecommendationEngine(CACHE_DIR / RECOMMENDATIONS_FILE)
    
    # Load all existing domains to avoid duplicate recommendations
    all_existing_domains = set()
    category_files = ['food.txt', 'cosmetics.txt', 'conglomerates.txt']
    for cat_file in category_files:
        domains = load_domains_from_list(cat_file)
        all_existing_domains.update(domains)
    
    # Define all categories
    all_categories = [
        ('Food & Delivery', 'food.txt', 'food'),
        ('Cosmetics & Beauty', 'cosmetics.txt', 'cosmetics'),
        ('Conglomerates', 'conglomerates.txt', 'conglomerates')
    ]
    
    # Filter by category if specified
    if args.category:
        categories = [(name, file, key) for name, file, key in all_categories if key == args.category]
    else:
        categories = all_categories
    
    for category_name, category_file, _ in categories:
        results = analyze_category(
            category_name, 
            category_file, 
            sample_size=sample_size,
            cache=cache,
            recommendations=recommendations,
            existing_domains=all_existing_domains,
            force_reanalysis=force_reanalysis,
            parallel=parallel,
            max_workers=max_workers
        )
        generate_markdown_report(category_name, results)
        generate_html_report(category_name, results)
        
        # Save JSON for programmatic access
        json_path = DATA_DIR / f"{category_name.lower().replace(' & ', '_').replace(' ', '_')}_data.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✓ Data saved to: {json_path}")
    
    # Save cache and recommendations
    if cache:
        cache.save_cache()
    recommendations.save_recommendations()
    
    # Generate summary statistics for index page
    generate_summary_stats()
    
    # Cleanup Playwright resources
    cleanup_playwright()
    
    # Show summary
    rec_summary = recommendations.get_summary()
    
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"HTML Reports: {REPORTS_DIR}")
    print(f"Markdown Docs: {DOCS_DIR}")
    print(f"JSON Data: {DATA_DIR}")
    
    if rec_summary['additions'] > 0 or rec_summary['removals'] > 0:
        print(f"\n📋 RECOMMENDATIONS:")
        print(f"   Additions: {rec_summary['additions']} new domains to consider")
        print(f"   Removals: {rec_summary['removals']} domains with low risk scores")
        print(f"\n   Review: {CACHE_DIR / RECOMMENDATIONS_FILE}")
        print(f"   Apply: python3 apply_recommendations.py")
    
    print("\nUse these reports to:")
    print("- Validate blocklist inclusion decisions")
    print("- Identify new domains to add (check 'Related Domains')")
    print("- Refine hazard detection keywords")
    print("- Generate justifications for Pi-hole users")


def cleanup_playwright():
    """Cleanup Playwright resources."""
    global PLAYWRIGHT_INSTANCE, BROWSER_INSTANCE
    if BROWSER_INSTANCE:
        try:
            BROWSER_INSTANCE.close()
        except:
            pass
    if PLAYWRIGHT_INSTANCE:
        try:
            PLAYWRIGHT_INSTANCE.stop()
        except:
            pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        cleanup_playwright()
    except Exception as e:
        print(f"\n\nError: {e}")
        cleanup_playwright()
        raise
