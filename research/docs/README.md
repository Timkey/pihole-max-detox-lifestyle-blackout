# Research & Analysis

This directory contains automated content analysis reports for blocklisted domains.

## Purpose

The analysis script (`scripts/analyze_domains.py`) provides:

1. **Evidence-based justification** for blocking decisions
2. **Hazard cluster identification** across categories
3. **Discovery of new domains** to add to blocklists
4. **Quantified risk assessment** for each domain

## Generated Reports

### Markdown Reports
- `food_&_delivery_analysis.md` - Food and delivery services analysis
- `cosmetics_&_beauty_analysis.md` - Beauty and cosmetics analysis
- `conglomerates_analysis.md` - Major conglomerates analysis

### JSON Data Files
- `food_&_delivery_data.json` - Structured data for programmatic access
- `cosmetics_&_beauty_data.json`
- `conglomerates_data.json`

## Analysis Methodology

### Health Hazards Detected
- **Ultra-processed foods**: Artificial ingredients, preservatives, additives
- **High sugar content**: Sweetened products, desserts, candy
- **Fast food**: Quick service, convenience meals
- **Addictive patterns**: Language promoting cravings
- **Poor nutrition**: Empty calories, junk food

### Behavioral Hazards Detected
- **Impulsive ordering**: One-click checkout, instant ordering
- **Urgency tactics**: Limited time offers, flash sales
- **Discount manipulation**: Aggressive promotional pricing
- **Over-convenience**: Frictionless delivery systems
- **Upselling**: Combos, meal deals, upgrades
- **Addiction language**: "Must-have", "trending", "favorites"

### Marketing Tactics Analyzed
- **Social proof**: Reviews, ratings, popularity claims
- **Scarcity**: Limited availability, exclusivity
- **FOMO**: Fear of missing out messaging
- **Personalization**: Targeted recommendations

## Risk Scoring

Each domain receives a risk score (0-100):
- **0-40**: Low risk
- **41-70**: Moderate risk
- **71-100**: High risk

Score components:
- Health hazards: 30 points max
- Behavioral hazards: 40 points max
- Marketing tactics: 30 points max

## Using Research Data

### Validate Blocklist Decisions
Review justifications to confirm domains should be blocked.

### Discover New Domains
Check "Related Domains" sections for additional sites to add.

### Refine Detection
Identify new hazard keywords based on analysis results.

### Communicate with Users
Use justifications to explain blocking decisions to Pi-hole users.

## Regenerating Reports

```bash
cd scripts
python3 analyze_domains.py
```

Reports are automatically saved to this directory.

## Note on Accessibility

Some domains may be inaccessible due to:
- Geographic restrictions
- Bot detection
- HTTPS/SSL issues
- Rate limiting

Failed analyses are noted in reports but don't invalidate blocking decisions based on known business models.
