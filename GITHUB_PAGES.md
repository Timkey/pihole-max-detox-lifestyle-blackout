# GitHub Pages Setup

## Enable GitHub Pages

1. Go to your repository settings on GitHub
2. Navigate to **Pages** section (left sidebar)
3. Under **Source**, select:
   - Branch: `main` (or your default branch)
   - Folder: `/ (root)`
4. Click **Save**

GitHub will build and deploy your site to:
```
https://timkey.github.io/pihole-max-detox-lifestyle-blackout/
```

## What's Published

- **Landing page:** `index.html` - Dashboard with links to all reports
- **Analysis reports:** `research/*.html` - Interactive charts and visualizations
- **Text reports:** `research/*.md` - Markdown format for GitHub viewing

## Local Testing

Preview HTML reports locally:
```bash
# macOS
open research/food\ \&\ delivery_analysis.html

# Linux
xdg-open research/food\ \&\ delivery_analysis.html

# Or use Python server
cd /Volumes/mnt/LAB/pihole-max-detox-lifestyle-blackout
python3 -m http.server 8000
# Then visit: http://localhost:8000
```

## URL Structure

Once GitHub Pages is enabled:

```
Main dashboard:
https://timkey.github.io/pihole-max-detox-lifestyle-blackout/

Food & Delivery report:
https://timkey.github.io/pihole-max-detox-lifestyle-blackout/research/reports/food%20&%20delivery_analysis.html

Cosmetics & Beauty report:
https://timkey.github.io/pihole-max-detox-lifestyle-blackout/research/reports/cosmetics%20&%20beauty_analysis.html

Conglomerates report:
https://timkey.github.io/pihole-max-detox-lifestyle-blackout/research/reports/conglomerates_analysis.html
```

## Automatic Updates

Every time you run `exec/analyze.sh` and push changes:
1. New HTML reports are generated
2. Commit and push to GitHub
3. GitHub Pages automatically rebuilds (takes 1-2 minutes)
4. Live reports update automatically

## Files for GitHub Pages

```
/
├── index.html              # Landing page with dashboard
├── _config.yml             # GitHub Pages configuration
├── research/
│   ├── reports/           # Interactive HTML reports (auto-published)
│   ├── docs/              # Markdown documentation (GitHub renders)
│   ├── data/              # JSON data files (for APIs)
│   └── cache/             # Not published (cached data)
└── README.md              # Updated with live links
```

## Custom Domain (Optional)

To use a custom domain:
1. Add `CNAME` file to root with your domain
2. Configure DNS:
   ```
   CNAME    @    timkey.github.io
   ```
3. Update in GitHub Pages settings

## Privacy

- All reports are **public** once on GitHub Pages
- Contains analysis data but no personal information
- Only shows aggregated hazard statistics
- Domain lists are already public in the repo

## Regenerate After Analysis

```bash
# Run analysis
exec/analyze.sh

# Commit and push (triggers GitHub Pages rebuild)
git add index.html research/reports/ research/docs/ research/data/ README.md
git commit -m "Updated analysis reports"
git push

# Wait 1-2 minutes for GitHub Pages to rebuild
# Check: https://github.com/Timkey/pihole-max-detox-lifestyle-blackout/actions
```
