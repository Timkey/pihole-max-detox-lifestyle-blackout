# Docker Container Usage Guide

## Why Docker?

Your Pi-hole blocklist prevents your PC from accessing the domains you're trying to analyze. This Docker container bypasses your Pi-hole by using external DNS servers (Google 8.8.8.8 and Cloudflare 1.1.1.1).

## Quick Start

### Start Container
```bash
# First time setup (builds image)
docker-compose up -d --build

# Subsequent starts
docker-compose up -d
```

### Run Scripts

**Option 1: Direct execution**
```bash
# Run analysis with caching
docker exec -it pihole-blocklist-analyzer python3 scripts/analyze_domains.py

# Check domain variations
docker exec -it pihole-blocklist-analyzer python3 scripts/check_domain_variations.py

# Apply recommendations
docker exec -it pihole-blocklist-analyzer python3 scripts/apply_recommendations.py

# Regenerate master list
docker exec -it pihole-blocklist-analyzer python3 scripts/generate_ultra.py
```

**Option 2: Interactive shell**
```bash
# Enter container
docker exec -it pihole-blocklist-analyzer bash

# Inside container
cd scripts
python3 analyze_domains.py
python3 check_domain_variations.py
python3 apply_recommendations.py
python3 generate_ultra.py
exit
```

### Recommended Workflow

```bash
# 1. Start container
docker-compose up -d

# 2. Analyze domains (uses cache, generates recommendations)
docker exec -it pihole-blocklist-analyzer python3 scripts/analyze_domains.py

# 3. Review recommendations
cat research/recommendations.json

# 4. Apply recommendations (interactive)
docker exec -it pihole-blocklist-analyzer python3 scripts/apply_recommendations.py

# 5. Regenerate master blocklist
docker exec -it pihole-blocklist-analyzer python3 scripts/generate_ultra.py

# 6. Commit changes
git add lists/ research/
git commit -m "Updated blocklists based on analysis"
git push
```

### Container Management

```bash
# Check if running
docker ps | grep pihole-blocklist

# View logs
docker logs pihole-blocklist-analyzer

# Stop container
docker-compose down

# Rebuild after changes to Dockerfile
docker-compose up -d --build

# Remove everything (fresh start)
docker-compose down
docker rmi pihole-max-detox-lifestyle-blackout-blocklist-analyzer
docker-compose up -d --build
```

## Verification

### Check DNS Configuration
```bash
# Should show 8.8.8.8, 1.1.1.1, 8.8.4.4 (NOT your Pi-hole)
docker exec pihole-blocklist-analyzer cat /etc/resolv.conf
```

### Test Domain Resolution
```bash
# Should return IP addresses (not 0.0.0.0)
docker exec pihole-blocklist-analyzer python3 -c "import socket; print(socket.gethostbyname('ubereats.com'))"
```

### Verify Python Packages
```bash
docker exec pihole-blocklist-analyzer pip list | grep -E "requests|beautifulsoup4|lxml"
```

## Troubleshooting

### Docker not running
```bash
# macOS (Colima)
colima start

# Linux
sudo systemctl start docker

# Windows
# Start Docker Desktop
```

### Container won't start
```bash
# View error logs
docker-compose logs

# Force rebuild
docker-compose down
docker-compose up -d --build
```

### DNS still using Pi-hole
```bash
# Check /etc/resolv.conf inside container
docker exec pihole-blocklist-analyzer cat /etc/resolv.conf

# Should show external DNS servers (8.8.8.8, 1.1.1.1)
# If not, rebuild with: docker-compose down && docker-compose up -d --build
```

### Permission errors
```bash
# Fix file permissions on host
chmod +x scripts/*.py

# Or run inside container with explicit python3
docker exec pihole-blocklist-analyzer python3 /workspace/scripts/analyze_domains.py
```

## Files Synced to Container

The entire project directory is mounted to `/workspace` inside the container:
- `lists/` → `/workspace/lists/`
- `scripts/` → `/workspace/scripts/`
- `research/` → `/workspace/research/`

Changes made inside the container are immediately reflected on your host machine and vice versa.
