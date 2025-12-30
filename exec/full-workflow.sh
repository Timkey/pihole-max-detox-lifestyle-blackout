#!/bin/bash
# Complete maintenance workflow
# Runs all steps: analyze → review → apply → regenerate

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  FULL BLOCKLIST MAINTENANCE WORKFLOW                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Analyze domains
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Analyze domains for hazards"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
./analyze.sh
echo ""

# Show recommendations
if [ -f "research/recommendations.json" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "RECOMMENDATIONS SUMMARY"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    additions=$(jq '.additions | length' research/recommendations.json 2>/dev/null || echo "0")
    removals=$(jq '.removals | length' research/recommendations.json 2>/dev/null || echo "0")
    
    echo "Additions recommended: $additions domains"
    echo "Removals recommended: $removals domains"
    echo ""
fi

# Step 2: Apply recommendations (interactive)
read -p "Apply recommendations? [y/N]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STEP 2: Apply recommendations"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ./apply-recommendations.sh
    echo ""
else
    echo "⊗ Skipping recommendations"
    echo ""
fi

# Step 3: Check for TLD variations
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Check domain variations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
./check-variations.sh
echo ""

read -p "Add verified variations? [y/N]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./add-variations.sh
    echo ""
else
    echo "⊗ Skipping variations"
    echo ""
fi

# Step 4: Regenerate master list
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 4: Regenerate master blocklist"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
./generate-ultra.sh
echo ""

# Step 5: Git status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 5: Review changes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git status --short lists/ research/ || true
echo ""

read -p "Commit and push changes? [y/N]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Commit message: " commit_msg
    git add lists/ research/
    git commit -m "${commit_msg:-Updated blocklists}"
    git push
    echo ""
    echo "✓ Changes pushed to GitHub"
else
    echo "⊗ Changes not committed"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  WORKFLOW COMPLETE                                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
