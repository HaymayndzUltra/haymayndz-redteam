#!/bin/bash
# Cloudflare Setup Script for EvilPanel
# Configures origin IP hiding behind Cloudflare proxy
#
# Prerequisites:
#   1. Domain added to Cloudflare
#   2. DNS nameservers updated to Cloudflare
#   3. CF_API_TOKEN environment variable set
#
# Usage: ./setup-cloudflare.sh <domain> [zone_id]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
DOMAIN="${1:-frontnews.site}"
ZONE_ID="${2:-}"
CONFIG_PATH="/opt/evilpanel/config/domains.yaml"
NGINX_CONF="/etc/nginx/sites-available/$DOMAIN"

# Cloudflare API settings
CF_API_BASE="https://api.cloudflare.com/client/v4"

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check for API token
    if [ -z "$CF_API_TOKEN" ]; then
        log_error "CF_API_TOKEN environment variable not set"
        echo "Set it with: export CF_API_TOKEN='your-token'"
        exit 1
    fi
    
    # Check for required tools
    for cmd in curl jq nginx; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd is required but not installed"
            exit 1
        fi
    done
    
    log_info "Prerequisites OK"
}

# Get zone ID from domain if not provided
get_zone_id() {
    if [ -n "$ZONE_ID" ]; then
        log_info "Using provided zone ID: $ZONE_ID"
        return
    fi
    
    log_info "Looking up zone ID for $DOMAIN..."
    
    ZONE_ID=$(curl -s -X GET "$CF_API_BASE/zones?name=$DOMAIN" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" | jq -r '.result[0].id')
    
    if [ "$ZONE_ID" == "null" ] || [ -z "$ZONE_ID" ]; then
        log_error "Could not find zone ID for $DOMAIN"
        log_error "Make sure the domain is added to your Cloudflare account"
        exit 1
    fi
    
    log_info "Zone ID: $ZONE_ID"
}

# Get server's public IP
get_server_ip() {
    log_info "Detecting server public IP..."
    
    SERVER_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || curl -s ipecho.net/plain)
    
    if [ -z "$SERVER_IP" ]; then
        log_error "Could not detect server IP"
        exit 1
    fi
    
    log_info "Server IP: $SERVER_IP"
}

# Create or update DNS records
setup_dns_records() {
    log_info "Setting up DNS records..."
    
    # Records to create: @, www, m (all proxied)
    SUBDOMAINS=("@" "www" "m")
    
    for subdomain in "${SUBDOMAINS[@]}"; do
        if [ "$subdomain" == "@" ]; then
            NAME="$DOMAIN"
        else
            NAME="$subdomain.$DOMAIN"
        fi
        
        log_info "Configuring $NAME..."
        
        # Check if record exists
        EXISTING=$(curl -s -X GET "$CF_API_BASE/zones/$ZONE_ID/dns_records?type=A&name=$NAME" \
            -H "Authorization: Bearer $CF_API_TOKEN" \
            -H "Content-Type: application/json" | jq -r '.result[0].id')
        
        RECORD_DATA=$(cat <<EOF
{
    "type": "A",
    "name": "$NAME",
    "content": "$SERVER_IP",
    "ttl": 1,
    "proxied": true
}
EOF
)
        
        if [ "$EXISTING" != "null" ] && [ -n "$EXISTING" ]; then
            # Update existing record
            curl -s -X PUT "$CF_API_BASE/zones/$ZONE_ID/dns_records/$EXISTING" \
                -H "Authorization: Bearer $CF_API_TOKEN" \
                -H "Content-Type: application/json" \
                --data "$RECORD_DATA" > /dev/null
            log_info "  Updated: $NAME -> $SERVER_IP (proxied)"
        else
            # Create new record
            curl -s -X POST "$CF_API_BASE/zones/$ZONE_ID/dns_records" \
                -H "Authorization: Bearer $CF_API_TOKEN" \
                -H "Content-Type: application/json" \
                --data "$RECORD_DATA" > /dev/null
            log_info "  Created: $NAME -> $SERVER_IP (proxied)"
        fi
    done
}

# Configure SSL mode
setup_ssl_mode() {
    log_info "Configuring SSL mode to Full (Strict)..."
    
    curl -s -X PATCH "$CF_API_BASE/zones/$ZONE_ID/settings/ssl" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data '{"value":"full"}' > /dev/null
    
    log_info "SSL mode set to Full"
}

# Enable security features
setup_security() {
    log_info "Configuring Cloudflare security settings..."
    
    # Enable Always Use HTTPS
    curl -s -X PATCH "$CF_API_BASE/zones/$ZONE_ID/settings/always_use_https" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data '{"value":"on"}' > /dev/null
    log_info "  Always Use HTTPS: ON"
    
    # Set minimum TLS version
    curl -s -X PATCH "$CF_API_BASE/zones/$ZONE_ID/settings/min_tls_version" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data '{"value":"1.2"}' > /dev/null
    log_info "  Minimum TLS: 1.2"
    
    # Enable HTTP/2
    curl -s -X PATCH "$CF_API_BASE/zones/$ZONE_ID/settings/http2" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data '{"value":"on"}' > /dev/null
    log_info "  HTTP/2: ON"
    
    # Set security level
    curl -s -X PATCH "$CF_API_BASE/zones/$ZONE_ID/settings/security_level" \
        -H "Authorization: Bearer $CF_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data '{"value":"medium"}' > /dev/null
    log_info "  Security Level: Medium"
}

# Update EvilPanel config
update_evilpanel_config() {
    log_info "Updating EvilPanel configuration..."
    
    if [ -f "$CONFIG_PATH" ]; then
        # Use Python to update YAML (safer than sed)
        python3 << EOF
import yaml

with open('$CONFIG_PATH', 'r') as f:
    config = yaml.safe_load(f) or {}

config['primary_domain'] = '$DOMAIN'
config['cloudflare'] = {
    'enabled': True,
    'api_token': '***REDACTED***',  # Don't store actual token
    'zone_id': '$ZONE_ID'
}

with open('$CONFIG_PATH', 'w') as f:
    yaml.dump(config, f, default_flow_style=False)

print("Config updated successfully")
EOF
    else
        log_warn "Config file not found at $CONFIG_PATH"
    fi
}

# Verify setup
verify_setup() {
    log_info "Verifying Cloudflare setup..."
    
    # Check if domain resolves through Cloudflare
    RESOLVED_IP=$(dig +short $DOMAIN | head -1)
    
    # Cloudflare IPs typically start with these ranges
    if [[ "$RESOLVED_IP" =~ ^(104\.|172\.|103\.|188\.|197\.|198\.|162\.|131\.) ]]; then
        log_info "Domain resolves to Cloudflare IP: $RESOLVED_IP"
        log_info "Origin IP ($SERVER_IP) is hidden!"
    else
        log_warn "Domain may not be proxied through Cloudflare"
        log_warn "Resolved IP: $RESOLVED_IP"
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo " Cloudflare Setup for EvilPanel"
    echo " Domain: $DOMAIN"
    echo "=========================================="
    echo ""
    
    check_prerequisites
    get_zone_id
    get_server_ip
    setup_dns_records
    setup_ssl_mode
    setup_security
    update_evilpanel_config
    verify_setup
    
    echo ""
    log_info "=========================================="
    log_info " Cloudflare setup complete!"
    log_info "=========================================="
    echo ""
    echo "Next steps:"
    echo "  1. Wait for DNS propagation (up to 24 hours)"
    echo "  2. Test with: curl -I https://$DOMAIN"
    echo "  3. Verify origin IP is hidden with: nslookup $DOMAIN"
    echo ""
    echo "Important: Reload Nginx to apply changes:"
    echo "  nginx -t && systemctl reload nginx"
}

main
