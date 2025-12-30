# Research Workflow Guide

## Overview
The content analysis tool helps justify blocklist decisions and discover new domains through automated website analysis.

## Quick Start

```bash
cd scripts
python3 analyze_domains.py
```

## What It Does

### 1. Content Extraction
- Fetches homepage content from each domain
- Extracts visible text, links, and product information
- Handles redirects and common web structures

### 2. Hazard Detection
Scans for problematic content patterns:

**Health Hazards**
- Ultra-processed food ingredients
- High sugar/sodium content
- Addictive food language
- Nutritionally poor offerings

**Behavioral Triggers**
- Impulsive ordering mechanisms
- Artificial urgency (limited time, flash sales)
- Aggressive discounts and promotions
- Friction-free convenience
- Upselling tactics

**Marketing Manipulation**
- Social proof abuse
- Scarcity tactics
- FOMO messaging
- Hyper-personalization

### 3. Risk Quantification
- Calculates 0-100 risk score per domain
- Weights behavioral hazards highest (40% of score)
- Provides clear justification text

### 4. Discovery
- Extracts related domain links
- Identifies partner sites and subsidiaries
- Suggests new domains to add to blocklists

## Reading the Reports

### Summary Section
```markdown
- Accessible domains: 4/5
- Average Risk Score: 76.5/100
```
Shows how many sites were successfully analyzed and overall risk level.

### Hazard Clusters
```markdown
### Health Hazards
- ultra_processed: 45 occurrences
- sugar: 32 occurrences
```
Aggregated hazard counts across all analyzed domains in the category.

### Individual Analysis
```markdown
### doordash.com
**Risk Score:** 85/100

**Justification for Blocking:**
- Promotes health hazards: ultra_processed, fast_food
- Uses behavioral manipulation: impulsive_ordering, urgency
- HIGH RISK: Multiple concerning patterns detected
```

Each domain gets its own section with:
- Risk score
- Blocking justification
- Sample products found
- Related domains discovered

## Using Results

### 1. Validate Current Blocks
Review justifications to ensure domains belong on blocklists.

### 2. Add New Domains
Check "Related Domains" sections:
```markdown
**Related Domains Found:**
- `doordash.partner.com`
- `delivery-api.example.com`
```
Research these and add if appropriate.

### 3. Refine Categories
If a domain shows unexpected hazards, consider:
- Moving to different category
- Adding sub-category blocks
- Updating hazard keywords

### 4. Document Decisions
Use justifications in:
- GitHub issue discussions
- Pull request descriptions
- User documentation
- Pi-hole community posts

## Customization

### Adjust Sample Size
Edit `analyze_domains.py`:
```python
analyze_category(category_name, category_file, sample_size=10)
```
Default is 5 domains per category to balance thoroughness with speed.

### Add Hazard Keywords
Edit keyword dictionaries in `analyze_domains.py`:
```python
HEALTH_HAZARDS = {
    'your_category': ['keyword1', 'keyword2', ...],
}
```

### Change Risk Weighting
Adjust scoring in `calculate_risk_score()` method.

## Interpreting Risk Scores

| Score | Level | Recommendation |
|-------|-------|----------------|
| 0-40 | Low | Review justification, may not need blocking |
| 41-70 | Moderate | Good candidate for blocking |
| 71-100 | High | Strong case for blocking |

## Limitations

- **Coverage**: Analyzes homepage only, not entire site
- **Dynamic Content**: May miss JavaScript-rendered content
- **Geographic**: Results vary by location/language
- **Rate Limiting**: Respect site policies, use delays

## Best Practices

1. **Run Periodically**: Re-analyze every few months to catch changes
2. **Sample Broadly**: Analyze diverse domains from each category
3. **Cross-Reference**: Compare findings across similar brands
4. **Document Discoveries**: Track related domains in issues/PRs
5. **Share Findings**: Contribute insights back to community

## Troubleshooting

**"Failed to access" errors**
- Normal for some sites with bot protection
- Geographic restrictions
- Not an issue - block based on business model

**Low risk scores for known bad actors**
- Homepage may not show worst content
- Business model still harmful
- Consider manual research

**Missing hazards**
- Add keywords to detection dictionaries
- Check report JSON files for raw data
- May need site-specific analysis

## Example Workflow

```bash
# 1. Run analysis
cd scripts
python3 analyze_domains.py

# 2. Review reports
cd ../research
less food_&_delivery_analysis.md

# 3. Add discovered domains
cd ../lists
echo "newfood-delivery.com" >> food.txt
echo "www.newfood-delivery.com" >> food.txt

# 4. Regenerate master list
cd ../scripts
python3 generate_ultra.py

# 5. Document findings
cd ..
git add research/ lists/
git commit -m "Add newfood-delivery.com based on DoorDash analysis"
```

## Contributing

Found new hazard patterns? Improved detection keywords? Share:
1. Open an issue describing the pattern
2. Submit PR with keyword additions
3. Include example domains showing the pattern
