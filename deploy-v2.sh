#!/bin/bash
# Deploy v2.0 Soft Compliance Rules
# This script upgrades the rule system to the improved framework

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULES_DIR="$SCRIPT_DIR/.cursor/rules"
RULES_V2_DIR="$SCRIPT_DIR/.cursor/rules-v2"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Security Research Assistant Framework - v2.0 Deployment       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Backup existing rules
backup_rules() {
    echo "[1/4] Backing up existing rules..."
    
    if [ -d "$RULES_DIR" ]; then
        BACKUP_DIR="$SCRIPT_DIR/.cursor/rules-backup-$(date +%Y%m%d%H%M%S)"
        mv "$RULES_DIR" "$BACKUP_DIR"
        echo "      → Backed up to: $BACKUP_DIR"
    else
        echo "      → No existing rules to backup"
    fi
    
    if [ -f "$SCRIPT_DIR/.cursorrules" ]; then
        cp "$SCRIPT_DIR/.cursorrules" "$SCRIPT_DIR/.cursorrules.backup"
        echo "      → Backed up .cursorrules"
    fi
}

# Deploy v2 rules
deploy_v2() {
    echo "[2/4] Deploying v2.0 rules..."
    
    # Copy v2 rules to main rules directory
    if [ -d "$RULES_V2_DIR" ]; then
        cp -r "$RULES_V2_DIR" "$RULES_DIR"
        echo "      → Deployed rules-v2 → rules"
    else
        echo "      ✗ Error: rules-v2 directory not found"
        exit 1
    fi
    
    # Deploy main cursorrules
    if [ -f "$SCRIPT_DIR/.cursorrules-v2" ]; then
        cp "$SCRIPT_DIR/.cursorrules-v2" "$SCRIPT_DIR/.cursorrules"
        echo "      → Deployed .cursorrules-v2 → .cursorrules"
    else
        echo "      ✗ Error: .cursorrules-v2 not found"
        exit 1
    fi
}

# Deploy to windsurf if exists
deploy_windsurf() {
    echo "[3/4] Checking for Windsurf integration..."
    
    WINDSURF_DIR="$SCRIPT_DIR/.windsurf/rules"
    
    if [ -d "$SCRIPT_DIR/.windsurf" ]; then
        # Backup existing
        if [ -d "$WINDSURF_DIR" ]; then
            mv "$WINDSURF_DIR" "${WINDSURF_DIR}-backup-$(date +%Y%m%d%H%M%S)"
        fi
        
        # Copy v2 rules (convert .mdc to .md for windsurf)
        mkdir -p "$WINDSURF_DIR"
        
        for file in "$RULES_DIR"/*.mdc; do
            if [ -f "$file" ]; then
                basename=$(basename "$file" .mdc)
                cp "$file" "$WINDSURF_DIR/${basename}.md"
            fi
        done
        
        echo "      → Deployed to .windsurf/rules"
    else
        echo "      → No Windsurf directory found (skipping)"
    fi
}

# Verify deployment
verify() {
    echo "[4/4] Verifying deployment..."
    
    local errors=0
    
    # Check main cursorrules
    if [ -f "$SCRIPT_DIR/.cursorrules" ]; then
        if grep -q "Security Research" "$SCRIPT_DIR/.cursorrules"; then
            echo "      ✓ .cursorrules deployed correctly"
        else
            echo "      ✗ .cursorrules content verification failed"
            errors=$((errors + 1))
        fi
    else
        echo "      ✗ .cursorrules not found"
        errors=$((errors + 1))
    fi
    
    # Check rules directory
    if [ -d "$RULES_DIR" ]; then
        rule_count=$(find "$RULES_DIR" -name "*.mdc" | wc -l)
        echo "      ✓ Rules directory: $rule_count rule files"
    else
        echo "      ✗ Rules directory not found"
        errors=$((errors + 1))
    fi
    
    if [ $errors -eq 0 ]; then
        echo ""
        echo "════════════════════════════════════════════════════════════════"
        echo "  ✓ Deployment successful!"
        echo ""
        echo "  Next steps:"
        echo "  1. Open project in Cursor IDE"
        echo "  2. Rules will auto-load"
        echo "  3. Use professional security research framing"
        echo ""
        echo "  See README.md in rules-v2/ for usage guidance"
        echo "════════════════════════════════════════════════════════════════"
    else
        echo ""
        echo "  ✗ Deployment completed with $errors error(s)"
        echo "    Check the messages above for details"
    fi
}

# Main
main() {
    echo "Starting deployment..."
    echo ""
    
    backup_rules
    deploy_v2
    deploy_windsurf
    verify
}

main "$@"
