# Quick Reference - Scripts Usage

## Directory Structure
```
/
├── lists/         → Blocklist files (food.txt, cosmetics.txt, etc.)
├── scripts/       → Maintenance Python scripts
└── README.md      → Full documentation
```

## Common Commands

### Regenerate Master List
```bash
cd scripts
python3 generate_ultra.py
```
Output: `lists/blackout-ultra.txt`

### Check for Missing Domain Variations
```bash
cd scripts
python3 check_domain_variations.py
```
Shows missing .com, .org, .net, .ca, .co.uk variations

### Auto-Add Domain Variations
```bash
cd scripts
python3 add_domain_variations.py
```
Adds verified TLD variations to lists/food.txt, lists/cosmetics.txt, lists/conglomerates.txt

### Complete Workflow
```bash
cd scripts

# 1. Check what's missing
python3 check_domain_variations.py

# 2. Add variations (if desired)
python3 add_domain_variations.py

# 3. Regenerate master list
python3 generate_ultra.py

# 4. Commit changes
cd ..
git add lists/
git commit -m "Update blocklists with new domain variations"
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
