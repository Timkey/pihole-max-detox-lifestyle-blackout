# MAX-DETOX-LIFESTYLE-BLACKOUT v1.0

## 📊 Interactive Analysis Reports

**View live reports:** [https://timkey.github.io/pihole-max-detox-lifestyle-blackout/](https://timkey.github.io/pihole-max-detox-lifestyle-blackout/)

Interactive HTML reports with charts and visualizations:
- 🍔 [Food & Delivery Analysis](https://timkey.github.io/pihole-max-detox-lifestyle-blackout/research/reports/food%20&%20delivery_analysis.html)
- 💄 [Cosmetics & Beauty Analysis](https://timkey.github.io/pihole-max-detox-lifestyle-blackout/research/reports/cosmetics%20&%20beauty_analysis.html)
- 🏢 [Conglomerates Analysis](https://timkey.github.io/pihole-max-detox-lifestyle-blackout/research/reports/conglomerates_analysis.html)

## Introduction

**MAX-DETOX-LIFESTYLE-BLACKOUT** is a curated collection of domain blocklists designed for [Pi-hole](https://pi-hole.net/), a network-level ad and content blocker. These lists go beyond traditional ad blocking—they target websites and services that promote unhealthy consumption patterns, impulsive spending, and manufactured wants.

### What Are These Lists?

These blocklists contain domain names of:
- **Fast food chains** and **food delivery platforms** that make unhealthy eating effortless
- **Beauty and cosmetics retailers** that drive overconsumption through manufactured insecurity
- **Major conglomerates** (Nestlé, Unilever, P&G, Coca-Cola, PepsiCo) that dominate markets and choices

Each list is formatted for Pi-hole compatibility, containing one domain per line with organized sections for easy review and maintenance.

### Why Use These Lists?

In a world where corporations exploit our psychology for profit, this project stands as a digital shield against unhealthy lifestyle enablers and financial blackholes. These blocklists help you reclaim control over your attention, health, and finances by blocking domains that promote:

- **Ultra-processed foods** that damage your health
- **Predatory delivery services** that drain your wallet  
- **Beauty industry manipulation** that preys on insecurity
- **Mega-conglomerates** that control markets and choices

This is not just about blocking websites—it's about reclaiming autonomy over your digital life and breaking free from engineered consumption patterns.

### What is Pi-hole?

[Pi-hole](https://pi-hole.net/) is a DNS-level content blocker that works at the network level, protecting all devices on your network (phones, tablets, smart TVs, etc.) without requiring individual software installation. When a device tries to access a blocked domain, Pi-hole intercepts the DNS request and prevents the connection.

## Project Structure

```
/ (root)
├── README.md                      # Complete documentation and guide
├── lists/                         # Blocklist files
│   ├── food.txt                   # Fast food & delivery blocklist
│   ├── cosmetics.txt              # Beauty & cosmetics blocklist
│   ├── conglomerates.txt          # Major conglomerates blocklist
│   ├── blackout-ultra.txt         # Master combined list
│   └── .domain_cache.json         # Domain verification cache (auto-generated)
├── scripts/                       # Maintenance scripts
│   ├── generate_ultra.py          # Regenerate blackout-ultra.txt
│   ├── check_domain_variations.py # Check for missing domain TLDs
│   ├── add_domain_variations.py   # Auto-add verified domain variations
│   └── analyze_domains.py         # Content analysis & research tool
├── research/                      # Analysis reports (auto-generated)
│   ├── food_&_delivery_analysis.md
│   ├── cosmetics_&_beauty_analysis.md
│   └── conglomerates_analysis.md
└── .gitignore                     # Git configuration
```

### Docker Setup (Recommended)

Since your Pi-hole blocks domains in the blocklist, run analysis scripts in a Docker container with external DNS:

```bash
# Build and start the container
exec/start.sh

# Run analysis scripts inside container (bypasses Pi-hole DNS)
exec/analyze.sh

# Or run the complete workflow
exec/full-workflow.sh

# Stop container when done
exec/stop.sh
```

**Quick commands:**
```bash
exec/analyze.sh                      # Analyze domains for hazards
exec/check-variations.sh             # Check for TLD variations  
exec/add-variations.sh               # Add verified variations
exec/apply-recommendations.sh        # Apply cached recommendations
exec/generate-ultra.sh               # Regenerate master blocklist
exec/shell.sh                        # Enter container shell
```

The container uses Google DNS (8.8.8.8) and Cloudflare DNS (1.1.1.1) instead of your Pi-hole.

**Note for macOS users:** The start script automatically configures Colima to mount `/Volumes/mnt` for access to your project files.

### Maintenance Scripts

**`generate_ultra.py`** - Regenerates the master blocklist
- Reads all category files from lists/
- Extracts domains while preserving block organization
- Removes duplicates within each block
- Sorts domains alphabetically (case-insensitive)
- Generates lists/blackout-ultra.txt

Usage:
```bash
cd scripts
python3 generate_ultra.py
```

**`check_domain_variations.py`** - Discovers missing domain TLDs
- Checks for .com, .org, .net, .co.uk, .ca, etc. variations
- Uses DNS lookups to verify domains actually exist
- Caches results to avoid redundant checks
- Shows which domains are missing from your lists

Usage:
```bash
cd scripts
python3 check_domain_variations.py
```

**`add_domain_variations.py`** - Automatically adds verified TLD variations
- Finds and adds missing domain variations to category files
- Uses cached DNS verification results
- Maintains alphabetical sorting within blocks
- Shows real-time progress with cache hit statistics

Usage:
```bash
cd scripts
python3 add_domain_variations.py
```

**`analyze_domains.py`** - Content analysis and research tool
- Fetches and analyzes website content from blocklisted domains
- Identifies health hazards (ultra-processed foods, sugar, additives)
- Detects behavioral manipulation tactics (urgency, FOMO, discounts)
- Extracts promoted products and related domains
- Generates risk scores (0-100) and blocking justifications
- Creates detailed markdown reports in research/ directory

Usage:
```bash
cd scripts
python3 analyze_domains.py
```

Output: Generates analysis reports for each category with:
- **Hazard clusters** - Aggregated health and behavioral risks
- **Risk scores** - Quantified danger levels per domain
- **Justifications** - Evidence-based blocking rationale
- **Related domains** - New domains to consider adding

---

## Blocklist Details
python3 generate_ultra.py
```

## Blocklist Details

### 🍔 food.txt
**Fast food chains, delivery platforms, and ultra-processed food companies**

Blocks domains for food delivery services and major fast food chains that enable impulsive, unhealthy eating habits and excessive spending.

**Blocks (28 domains):**
- **Delivery Platforms**: DoorDash, UberEats, GrubHub, Postmates (including APIs)
- **Fast Food Chains**: McDonald's, Burger King, KFC, Taco Bell, Pizza Hut, Domino's, Subway, Wendy's

**Pi-hole URL:**
```
https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/lists/food.txt
```

**Use Case**: Block late-night delivery temptations, save money on overpriced delivery fees, encourage home cooking

---

### 💄 cosmetics.txt
**Beauty retailers and brands promoting overconsumption and unrealistic standards**

Blocks beauty and cosmetics retailers that drive spending through manufactured insecurity and constant trend cycles.

**Blocks (22 domains):**
- **Major Retailers**: Sephora, Ulta, BeautyBay, Cult Beauty
- **Luxury Brands**: L'Oréal, Estée Lauder, MAC Cosmetics, Clinique
- **Mass Market**: Maybelline, CoverGirl, Revlon

**Pi-hole URL:**
```
https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/lists/cosmetics.txt
```

**Use Case**: Reduce beauty marketing exposure, break impulse cosmetics purchases, focus on essentials

---

### 🏢 conglomerates.txt
**The "Nuclear" list - Major corporations dominating consumer markets**

Blocks major multinational conglomerates and their vast networks of subsidiary brands across food, beverages, personal care, and household products.

**Blocks (45 domains):**
- **Nestlé**: Including Nespresso, Gerber, Purina
- **Unilever**: Axe, Dove, Hellmann's
- **Procter & Gamble**: Gillette, Tide, Pantene
- **Coca-Cola Company**: Coca-Cola, Sprite, Fanta
- **PepsiCo**: Pepsi, Frito-Lay, Gatorade

**Pi-hole URL:**
```
https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/lists/conglomerates.txt
```

**Use Case**: Reduce exposure to mega-corporations, support local/independent alternatives, break brand loyalty cycles

---

### ☢️ blackout-ultra.txt
**The master list combining ALL categories - Maximum protection**

A unified blocklist containing all domains from food, cosmetics, and conglomerates lists, organized by category blocks. Automatically generated from source files and kept alphabetically sorted within each block.

**Blocks (95 domains across 11 category blocks)**

**Pi-hole URL:**
```
https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/lists/blackout-ultra.txt
```

**Use Case**: One-click comprehensive blocking, easiest to maintain, automatic updates include all categories

**Regeneration**: This file is automatically generated using `generate_ultra.py` which:
- Combines all category files
- Removes duplicates
- Sorts domains alphabetically within each block
- Preserves category organization for clarity

## How to Use with Pi-hole

### Prerequisites

- A working [Pi-hole installation](https://docs.pi-hole.net/main/basic-install/) (v5.0 or later recommended)
- Access to your Pi-hole admin dashboard
- Network devices configured to use Pi-hole as their DNS server

### Step-by-Step Installation

#### 1. **Access Your Pi-hole Admin Panel**
   - Open your browser and navigate to: `http://pi.hole/admin` (or your Pi-hole's IP address)
   - Log in with your admin password

#### 2. **Navigate to Adlists**
   - Click on **Group Management** in the left sidebar
   - Select **Adlists** from the submenu

#### 3. **Add Your Chosen Blocklist(s)**
   - In the "Address" field, paste one of the URLs below
   - Optionally add a comment (e.g., "Food Delivery Block")
   - Click **Add** to save
   - Repeat for each list you want to use

   **Available blocklist URLs:**
   ```
   https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/lists/food.txt
   https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/lists/cosmetics.txt
   https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/lists/conglomerates.txt
   https://raw.githubusercontent.com/Timkey/pihole-max-detox-lifestyle-blackout/main/lists/blackout-ultra.txt
   ```

#### 4. **Update Gravity**
   - After adding your lists, go to **Tools** → **Update Gravity**
   - Click **Update** and wait for the process to complete
   - This downloads and applies all blocklists (including your new ones)

#### 5. **Verify Installation**
   - Go to **Dashboard** to see updated statistics
   - Check **Group Management** → **Adlists** to confirm lists show "Last updated" timestamps
   - Try accessing a blocked domain (e.g., `www.doordash.com`) to verify blocking works

### Choosing Your Protection Level

Select blocklists based on your goals:

- **🥗 Light Mode**: Use `food.txt` only
  - Blocks food delivery and fast food sites
  - Perfect for breaking impulsive food ordering habits
  - Minimal impact on daily browsing

- **💅 Medium Mode**: Use `food.txt` + `cosmetics.txt`
  - Adds beauty/cosmetics blocking to food restrictions
  - Great for reducing beauty industry marketing exposure
  - Helps curb cosmetics impulse purchases

- **🔨 Heavy Mode**: Use `food.txt` + `cosmetics.txt` + `conglomerates.txt`
  - Individual category control for maximum flexibility
  - Block major conglomerate brands and subsidiaries
  - More granular than nuclear option

- **☢️ Nuclear Mode**: Use `blackout-ultra.txt` only
  - One master list containing all categories (11 blocks, 95+ domains)
  - Maximum protection with single list management
  - Simplest to maintain and update

### Updating Lists

Pi-hole automatically updates blocklists weekly. To manually update:
1. Go to **Tools** → **Update Gravity**
2. Click **Update**

Lists are regenerated from source files using `generate_ultra.py`, ensuring all domains stay current.

### Removing Lists

To remove a blocklist:
1. Go to **Group Management** → **Adlists**
2. Click the red trash icon next to the list
3. Run **Update Gravity** to apply changes

### Temporarily Disabling

To temporarily disable blocking without removing lists:
1. Go to **Group Management** → **Adlists**
2. Click the green checkmark to toggle the list off (turns red)
3. Run **Update Gravity**

### Whitelisting Specific Domains

If a blocked domain causes issues:
1. Go to **Whitelist** in the sidebar
2. Add the domain (e.g., `www.example.com`)
3. Click **Add to Whitelist**
4. No gravity update needed—takes effect immediately

## Frequently Asked Questions

### Will this break anything on my network?

These lists are narrowly targeted at specific consumer services. They should not affect:
- Email, social media, or essential services
- Banking, healthcare, or government websites
- News, entertainment, or productivity tools

If something breaks, you can always whitelist specific domains or temporarily disable the lists.

### Can I use these without Pi-hole?

These lists are formatted for Pi-hole but can potentially work with other DNS-based blockers (AdGuard Home, dnscrypt-proxy, etc.). However, instructions and testing focus on Pi-hole.

### Do I need all the lists?

No! Start with just one (e.g., `food.txt`) and add more as needed. The modular approach lets you customize your blocking level.

### How often are lists updated?

Pi-hole automatically checks for updates weekly. When new domains are added to the GitHub repository, they'll be downloaded during the next update cycle.

### What if I need to order food delivery occasionally?

You can:
1. Temporarily disable the list in Pi-hole (Group Management → Adlists)
2. Whitelist specific domains you need
3. Use a different device/network not protected by Pi-hole
4. Disable Pi-hole entirely for a few minutes (Dashboard → Disable button)

### Will this slow down my internet?

No. DNS blocking happens at the DNS lookup stage and actually speeds up browsing by preventing connections to blocked domains entirely.

---

## Philosophy

We believe in:
- **Digital minimalism** - Less is more
- **Conscious consumption** - Buy what you need, not what you're sold
- **Health over convenience** - Your body deserves better than delivery junk
- **Independence** - Breaking free from corporate manipulation

---

## Contributing

Found a domain that should be blocked? Open an issue or submit a pull request. Let's build this together.

## Disclaimer

These blocklists are provided as-is for personal use. Users are solely responsible for their own network filtering decisions. This project does not endorse or condemn any specific company—it simply provides tools for those seeking to reduce exposure to certain types of marketing and services.

## License

Public domain. Use freely, modify freely, share freely. 
