# Scripts Guide

## Shell Scripts (Recommended)

Convenient wrapper scripts that run Python code inside Docker with external DNS.

### Quick Start
```bash
./start.sh                    # Start Docker container
./full-workflow.sh            # Complete maintenance workflow
./stop.sh                     # Stop container
```

### Individual Scripts
```bash
./analyze.sh                  # Analyze domains for hazards
./check-variations.sh         # Check for TLD variations
./add-variations.sh           # Add verified variations
./apply-recommendations.sh    # Apply cached recommendations
./recalculate-enablers.sh     # Recalculate enabler scores
./regenerate-reports.sh       # Regenerate HTML/Markdown reports
./generate-ultra.sh           # Regenerate master blocklist
./shell.sh                    # Enter container shell
```

### Full Workflow (Interactive)
```bash
./full-workflow.sh
```
Steps through:
1. Domain analysis with caching
2. Review recommendations
3. Apply changes (optional)
4. Check TLD variations
5. Add variations (optional)
6. Regenerate ultra list
7. Git commit (optional)

---

## Python Scripts (Direct)

Run inside Docker container to bypass Pi-hole DNS.

### Directory Structure
```
/
├── lists/         → Blocklist files (food.txt, cosmetics.txt, etc.)
├── scripts/       → Maintenance Python scripts
├── research/      → Analysis reports and data (auto-generated)
└── *.sh           → Shell wrapper scripts
```

## Common Commands

### Regenerate Master List
```bash
docker exec -it pihole-blocklist-analyzer python3 scripts/generate_ultra.py
# Or use shell script:
./generate-ultra.sh
```
Output: `lists/blackout-ultra.txt`

### Check for Missing Domain Variations
```bash
docker exec -it pihole-blocklist-analyzer python3 scripts/check_domain_variations.py
# Or:
./check-variations.sh
```
Shows missing .com, .org, .net, .ca, .co.uk variations

### Auto-Add Domain Variations
```bash
docker exec -it pihole-blocklist-analyzer python3 scripts/add_domain_variations.py
# Or:
./add-variations.sh
```
Adds verified TLD variations to category lists

### Analyze Domain Content
```bash
docker exec -it pihole-blocklist-analyzer python3 scripts/analyze_domains.py
# Or:
./analyze.sh
```
Analyzes websites for:
- Health hazards (ultra-processed foods, sugar, additives)
- Behavioral manipulation tactics (urgency, FOMO, discounts)
- Marketing patterns (limited offers, countdown timers)
- **Bi-directional enabler scoring** (platforms facilitating high-risk brands)
- Risk scores (0-100) with enabler bonuses
- Related domains to consider

Generates:
- **Interactive HTML reports** with charts, filters, sorting
- **Mobile-responsive** layouts
- **Failed analysis tracking** with error categorization
- **Markdown reports** in research/docs/
- **JSON data files** in research/data/

### Recalculate Enabler Scores (Fast)
```bash
docker exec -it pihole-blocklist-analyzer python3 scripts/recalculate_enabler_scores.py
# Or:
./recalculate-enablers.sh
```
Fast recalculation of enabler scores without re-scraping:
- Uses existing related_domains data
- Bi-directional relationship detection
- Completes in seconds vs 80-minute full reanalysis

### Regenerate Reports
```bash
docker exec -it pihole-blocklist-analyzer python3 scripts/regenerate_reports.py
# Or:
./regenerate-reports.sh
```
Regenerates HTML and Markdown reports from existing JSON data:
- Updates all category reports
- Dynamic JSON loading with fallback
- Mobile-responsive design
- Useful after score recalculation

### Apply Recommendations
```bash
docker exec -it pihole-blocklist-analyzer python3 scripts/apply_recommendations.py
# Or:
./apply-recommendations.sh              # Interactive
./apply-recommendations.sh --dry-run    # Preview only
./apply-recommendations.sh --yes        # Auto-apply
```

Processes recommendations:
- Adds high-risk related domains
- Removes low-risk domains (<30 score)

## Script Arguments

### analyze_domains.py
```bash
python3 scripts/analyze_domains.py           # Analyze all categories
```

### apply_recommendations.py
```bash
python3 scripts/apply_recommendations.py --dry-run    # Preview changes
python3 scripts/apply_recommendations.py --yes        # Skip confirmation
python3 scripts/apply_recommendations.py --additions  # Only additions
python3 scripts/apply_recommendations.py --removals   # Only removals
```

## Caching

### Domain Verification Cache
File: `lists/.domain_cache.json`
- Stores DNS lookup results
- Permanent cache (verified/not_found)
- Shared by check_domain_variations.py and add_domain_variations.py

### Analysis Cache  
File: `research/analysis_cache.json`
- Stores domain content analysis
- 30-day expiry (configurable)
- Used by analyze_domains.py

### Recommendations
File: `research/recommendations.json`
- Pending additions/removals
- Status tracking (pending/applied)
- Processed by apply_recommendations.py

## Workflow Examples

### Daily Monitoring
```bash
./start.sh
./analyze.sh                      # Uses cache, fast
./apply-recommendations.sh        # Review and apply
./generate-ultra.sh               # Update master
git add . && git commit -m "Daily update" && git push
./stop.sh
```

### Weekly Deep Check
```bash
./start.sh
./full-workflow.sh               # Interactive, handles everything
./stop.sh
```

### Quick TLD Expansion
```bash
./start.sh
./check-variations.sh
./add-variations.sh
./generate-ultra.sh
./stop.sh
```

## Troubleshooting

### Pi-hole blocking analysis
✅ Use Docker container with external DNS (./start.sh)

### Cache issues
```bash
# Clear domain cache
rm lists/.domain_cache.json

# Clear analysis cache  
rm research/analysis_cache.json

# Clear recommendations
rm research/recommendations.json
```

### Permission errors
```bash
chmod +x *.sh
chmod +x scripts/*.py
```

### Container not found
```bash
./start.sh    # Starts container automatically
```
- Marketing patterns
- Risk scores and justifications
- Related domains to add

### Complete Workflow
```bash
cd scripts

# 1. Research: Analyze current domains
python3 analyze_domains.py

# 2. Check what's missing
python3 check_domain_variations.py

# 3. Add variations (if desired)
python3 add_domain_variations.py

# 4. Regenerate master list
python3 generate_ultra.py

# 5. Commit changes
cd ..
git add lists/ research/
git commit -m "Update blocklists with new domain variations and research"
git push
```

## Pi-hole URLs

All blocklists are served from the `/lists/` directory:

- Food: `https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/lists/food.txt`
- Cosmetics: `https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/lists/cosmetics.txt`
- Conglomerates: `https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/lists/conglomerates.txt`
- Master: `https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/lists/blackout-ultra.txt`

## Cache File

The domain verification cache is stored in `lists/.domain_cache.json` and is automatically managed by the scripts. It dramatically speeds up subsequent runs by avoiding redundant DNS lookups.
