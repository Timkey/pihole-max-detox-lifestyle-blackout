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
    """Manages cached analysis results."""
    
    def __init__(self, cache_file):
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
    
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
        """Save cache to file."""
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
        """Store analysis result."""
        self.cache['analyses'][domain] = analysis


class RecommendationEngine:
    """Manages domain recommendations for additions and removals."""
    
    def __init__(self, recommendations_file):
        self.rec_file = Path(recommendations_file)
        self.recommendations = self._load_recommendations()
    
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
        """Save recommendations to file."""
        self.recommendations['last_updated'] = datetime.now().isoformat()
        with open(self.rec_file, 'w') as f:
            json.dump(self.recommendations, f, indent=2)
        print(f"\n✓ Recommendations saved to: {self.rec_file}")
    
    def add_addition_recommendation(self, domain, category, reason, source_domain=None):
        """Recommend adding a domain."""
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
        
        # Check if already recommended
        for existing in self.recommendations['additions']:
            if existing['domain'] == domain:
                return  # Already recommended
        
        self.recommendations['additions'].append(rec)
    
    def add_removal_recommendation(self, domain, category, reason, risk_score):
        """Recommend removing a domain."""
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
        
        # Check if already recommended
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
        """Fetch website content with better bot evasion."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            response = requests.get(self.url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
            response.raise_for_status()
            self.content = response.text
            self.soup = BeautifulSoup(self.content, 'html.parser')
            
            # Check if we actually got content
            text = self.soup.get_text(strip=True)
            if len(text) < 100:
                self.analysis['error'] = 'Insufficient content (possible bot detection or JS-rendered page)'
                self.analysis['accessible'] = False
                return False
            
            self.analysis['accessible'] = True
            return True
        except Exception as e:
            self.analysis['error'] = str(e)
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


def analyze_category(category_name, category_file, sample_size=5, cache=None, recommendations=None, existing_domains=None):
    """Analyze a sample of domains from a category."""
    print(f"\n{'='*60}")
    print(f"Analyzing Category: {category_name}")
    print(f"{'='*60}")
    
    domains = load_domains_from_list(category_file)
    print(f"Found {len(domains)} unique base domains")
    
    if cache:
        cached_count = sum(1 for d in domains if cache.is_cached(d))
        print(f"Cached: {cached_count}, Need analysis: {len(domains) - cached_count}")
    
    print(f"Analyzing up to {sample_size} domains...\n")
    
    results = []
    analyzed_count = 0
    
    # Analyze sample
    for domain in domains:
        if analyzed_count >= sample_size:
            break
        
        # Check cache first
        if cache and cache.is_cached(domain):
            print(f"{domain}... ✓ Using cached analysis")
            result = cache.get_analysis(domain)
            results.append(result)
        else:
            analyzer = DomainAnalyzer(domain)
            result = analyzer.analyze()
            results.append(result)
            
            if cache:
                cache.store_analysis(domain, result)
            
            analyzed_count += 1
            time.sleep(2)  # Rate limiting
        
        # Process recommendations
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
    
    return results


def generate_html_report(category_name, results):
    """Generate interactive HTML report with charts."""
    report_path = REPORTS_DIR / f"{category_name.lower()}_analysis.html"
    
    # Prepare data
    accessible = [r for r in results if r['accessible']]
    avg_risk = sum(r['risk_score'] for r in accessible) / len(accessible) if accessible else 0
    
    # Aggregate hazards
    health_hazards = {}
    behavioral_hazards = {}
    marketing_tactics = {}
    
    for result in accessible:
        for hazard, count in result.get('health_hazards', {}).items():
            health_hazards[hazard] = health_hazards.get(hazard, 0) + count
        for hazard, count in result.get('behavioral_hazards', {}).items():
            behavioral_hazards[hazard] = behavioral_hazards.get(hazard, 0) + count
        for tactic, count in result.get('marketing_tactics', {}).items():
            marketing_tactics[tactic] = marketing_tactics.get(tactic, 0) + count
    
    # Sort domains by risk score
    top_risks = sorted(accessible, key=lambda x: x['risk_score'], reverse=True)[:10]
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{category_name} - Analysis Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
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
        .domain-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #eee;
        }}
        .domain-item:last-child {{
            border-bottom: none;
        }}
        .domain-name {{
            font-weight: 500;
            color: #333;
        }}
        .risk-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            color: white;
        }}
        .risk-high {{ background: #e74c3c; }}
        .risk-medium {{ background: #f39c12; }}
        .risk-low {{ background: #27ae60; }}
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        @media (max-width: 768px) {{
            .grid-2 {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{category_name} - Content Analysis</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{len(results)}</div>
            <div class="stat-label">Domains Analyzed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len(accessible)}</div>
            <div class="stat-label">Successfully Accessed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{avg_risk:.1f}</div>
            <div class="stat-label">Average Risk Score</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{len([r for r in accessible if r['risk_score'] > 50])}</div>
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
        <h2>Top Risk Scores</h2>
        <div class="chart-wrapper">
            <canvas id="riskChart"></canvas>
        </div>
    </div>

    <div class="domain-list">
        <h2>Highest Risk Domains</h2>
        {''.join([f'''
        <div class="domain-item">
            <span class="domain-name">{r['domain']}</span>
            <span class="risk-badge {'risk-high' if r['risk_score'] > 50 else 'risk-medium' if r['risk_score'] > 30 else 'risk-low'}">{r['risk_score']}/100</span>
        </div>
        ''' for r in top_risks])}
    </div>

    <script>
        // Health Hazards Chart
        new Chart(document.getElementById('healthChart'), {{
            type: 'bar',
            data: {{
                labels: {list(health_hazards.keys())},
                datasets: [{{
                    label: 'Occurrences',
                    data: {list(health_hazards.values())},
                    backgroundColor: 'rgba(231, 76, 60, 0.7)',
                    borderColor: 'rgba(231, 76, 60, 1)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});

        // Behavioral Hazards Chart
        new Chart(document.getElementById('behavioralChart'), {{
            type: 'doughnut',
            data: {{
                labels: {list(behavioral_hazards.keys())},
                datasets: [{{
                    data: {list(behavioral_hazards.values())},
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

        // Marketing Tactics Chart
        new Chart(document.getElementById('marketingChart'), {{
            type: 'bar',
            data: {{
                labels: {list(marketing_tactics.keys())},
                datasets: [{{
                    label: 'Occurrences',
                    data: {list(marketing_tactics.values())},
                    backgroundColor: 'rgba(52, 152, 219, 0.7)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});

        // Risk Scores Chart
        new Chart(document.getElementById('riskChart'), {{
            type: 'bar',
            data: {{
                labels: {[r['domain'] for r in top_risks]},
                datasets: [{{
                    label: 'Risk Score',
                    data: {[r['risk_score'] for r in top_risks]},
                    backgroundColor: {[f"'rgba(231, 76, 60, 0.7)'" if r['risk_score'] > 50 else f"'rgba(243, 156, 18, 0.7)'" if r['risk_score'] > 30 else "'rgba(46, 204, 113, 0.7)'" for r in top_risks]},
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    print(f"✓ HTML Report saved to: {report_path}")
    return report_path


def generate_markdown_report(category_name, results):
    """Generate markdown research report."""
    report_path = DOCS_DIR / f"{category_name.lower()}_analysis.md"
    
    with open(report_path, 'w') as f:
        f.write(f"# {category_name} - Content Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Domains Analyzed:** {len(results)}\n\n")
        
        # Summary statistics
        avg_risk = sum(r['risk_score'] for r in results if r['accessible']) / len([r for r in results if r['accessible']]) if results else 0
        accessible_count = sum(1 for r in results if r['accessible'])
        
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
    print("DOMAIN CONTENT ANALYSIS TOOL (with caching)")
    print("Analyzing website content for health and behavioral hazards\n")
    
    # Ensure directories exist
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize cache and recommendations
    cache = AnalysisCache(CACHE_DIR / ANALYSIS_CACHE_FILE)
    recommendations = RecommendationEngine(CACHE_DIR / RECOMMENDATIONS_FILE)
    
    # Load all existing domains to avoid duplicate recommendations
    all_existing_domains = set()
    category_files = ['food.txt', 'cosmetics.txt', 'conglomerates.txt']
    for cat_file in category_files:
        domains = load_domains_from_list(cat_file)
        all_existing_domains.update(domains)
    
    categories = [
        ('Food & Delivery', 'food.txt'),
        ('Cosmetics & Beauty', 'cosmetics.txt'),
        ('Conglomerates', 'conglomerates.txt')
    ]
    
    for category_name, category_file in categories:
        results = analyze_category(
            category_name, 
            category_file, 
            sample_size=5,
            cache=cache,
            recommendations=recommendations,
            existing_domains=all_existing_domains
        )
        generate_markdown_report(category_name, results)
        generate_html_report(category_name, results)
        
        # Save JSON for programmatic access
        json_path = DATA_DIR / f"{category_name.lower().replace(' & ', '_').replace(' ', '_')}_data.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✓ Data saved to: {json_path}")
    
    # Save cache and recommendations
    cache.save_cache()
    recommendations.save_recommendations()
    
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


if __name__ == '__main__':
    main()
