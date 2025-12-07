#!/bin/bash
# GeoIP Database Update Script for EvilPanel
# Downloads and installs MaxMind GeoLite2 databases for geographic cloaking
#
# Prerequisites:
#   - MaxMind account with license key
#   - libnginx-mod-http-geoip2 installed
#
# Usage: ./update-geoip.sh [license_key]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
GEOIP_DIR="/usr/share/GeoIP"
MAXMIND_LICENSE_KEY="${1:-$MAXMIND_LICENSE_KEY}"
MAXMIND_ACCOUNT_ID="${MAXMIND_ACCOUNT_ID:-}"

# GeoLite2 database URLs (free tier)
GEOLITE2_COUNTRY_URL="https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-Country&license_key=${MAXMIND_LICENSE_KEY}&suffix=tar.gz"
GEOLITE2_CITY_URL="https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=${MAXMIND_LICENSE_KEY}&suffix=tar.gz"
GEOLITE2_ASN_URL="https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=${MAXMIND_LICENSE_KEY}&suffix=tar.gz"

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check for license key
    if [ -z "$MAXMIND_LICENSE_KEY" ]; then
        log_warn "MaxMind license key not provided"
        log_warn "Get a free key at: https://www.maxmind.com/en/geolite2/signup"
        echo ""
        echo "Usage: ./update-geoip.sh <license_key>"
        echo "Or set: export MAXMIND_LICENSE_KEY='your-key'"
        echo ""
        log_info "Installing GeoIP2 module only (database can be added later)..."
    fi
    
    # Check for required tools
    for cmd in curl tar; do
        if ! command -v $cmd &> /dev/null; then
            log_error "$cmd is required but not installed"
            exit 1
        fi
    done
}

# Install GeoIP2 Nginx module
install_geoip_module() {
    log_info "Installing GeoIP2 Nginx module..."
    
    # Check if already installed
    if nginx -V 2>&1 | grep -q "geoip2"; then
        log_info "GeoIP2 module already loaded in Nginx"
        return 0
    fi
    
    # Try to install
    if command -v apt &> /dev/null; then
        apt update -qq
        apt install -y libnginx-mod-http-geoip2 libmaxminddb0 libmaxminddb-dev mmdb-bin
        log_info "GeoIP2 module installed via apt"
    elif command -v yum &> /dev/null; then
        yum install -y nginx-mod-http-geoip2 libmaxminddb libmaxminddb-devel
        log_info "GeoIP2 module installed via yum"
    else
        log_error "Could not install GeoIP2 module - unsupported package manager"
        return 1
    fi
}

# Create GeoIP directory
setup_directory() {
    log_info "Setting up GeoIP directory..."
    
    mkdir -p "$GEOIP_DIR"
    chmod 755 "$GEOIP_DIR"
}

# Download and extract database
download_database() {
    local name="$1"
    local url="$2"
    local temp_file="/tmp/${name}.tar.gz"
    local temp_dir="/tmp/${name}_extract"
    
    log_info "Downloading $name database..."
    
    # Download
    if ! curl -s -o "$temp_file" "$url"; then
        log_error "Failed to download $name"
        return 1
    fi
    
    # Check if valid tar.gz
    if ! file "$temp_file" | grep -q "gzip"; then
        log_error "Downloaded file is not a valid gzip archive"
        log_warn "Check your MaxMind license key"
        rm -f "$temp_file"
        return 1
    fi
    
    # Extract
    rm -rf "$temp_dir"
    mkdir -p "$temp_dir"
    tar -xzf "$temp_file" -C "$temp_dir"
    
    # Find and copy .mmdb file
    local mmdb_file=$(find "$temp_dir" -name "*.mmdb" | head -1)
    
    if [ -n "$mmdb_file" ]; then
        cp "$mmdb_file" "$GEOIP_DIR/"
        log_info "  Installed: $(basename $mmdb_file)"
    else
        log_error "  No .mmdb file found in archive"
        return 1
    fi
    
    # Cleanup
    rm -f "$temp_file"
    rm -rf "$temp_dir"
    
    return 0
}

# Download all databases
download_all_databases() {
    if [ -z "$MAXMIND_LICENSE_KEY" ]; then
        log_warn "Skipping database download (no license key)"
        return
    fi
    
    log_info "Downloading GeoLite2 databases..."
    
    download_database "GeoLite2-Country" "$GEOLITE2_COUNTRY_URL" || true
    download_database "GeoLite2-City" "$GEOLITE2_CITY_URL" || true
    download_database "GeoLite2-ASN" "$GEOLITE2_ASN_URL" || true
}

# Create example Nginx GeoIP config
create_nginx_geoip_config() {
    log_info "Creating example Nginx GeoIP configuration..."
    
    local config_file="/etc/nginx/conf.d/geoip.conf"
    
    cat > "$config_file" << 'EOF'
# GeoIP2 Configuration for Geographic Cloaking
# Include this in your nginx.conf http block

# Load GeoIP2 databases
geoip2 /usr/share/GeoIP/GeoLite2-Country.mmdb {
    auto_reload 60m;
    $geoip2_country_code country iso_code;
    $geoip2_country_name country names en;
}

# Optional: City-level data
# geoip2 /usr/share/GeoIP/GeoLite2-City.mmdb {
#     $geoip2_city_name city names en;
#     $geoip2_region_name subdivisions 0 names en;
# }

# Optional: ASN data (useful for blocking cloud providers)
# geoip2 /usr/share/GeoIP/GeoLite2-ASN.mmdb {
#     $geoip2_asn autonomous_system_number;
#     $geoip2_asn_org autonomous_system_organization;
# }

# Map allowed countries
# Modify this list based on your target audience
map $geoip2_country_code $allowed_country {
    default 0;
    
    # Target countries (allow)
    PH 1;  # Philippines
    US 1;  # United States
    
    # Add more as needed:
    # CA 1;  # Canada
    # GB 1;  # United Kingdom
    # AU 1;  # Australia
}

# Map blocked countries (high scanner activity)
map $geoip2_country_code $blocked_country {
    default 0;
    
    # Countries with high scanner activity
    CN 1;  # China
    RU 1;  # Russia
    KP 1;  # North Korea
    IR 1;  # Iran
    
    # Note: Adjust based on your needs
}
EOF

    log_info "GeoIP config created at: $config_file"
    log_info "Add this to your nginx.conf: include /etc/nginx/conf.d/geoip.conf;"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    # Check databases exist
    local dbs_found=0
    for db in GeoLite2-Country.mmdb GeoLite2-City.mmdb GeoLite2-ASN.mmdb; do
        if [ -f "$GEOIP_DIR/$db" ]; then
            log_info "  Found: $db"
            ((dbs_found++))
        fi
    done
    
    if [ $dbs_found -eq 0 ]; then
        log_warn "No GeoIP databases found"
        log_warn "Run with license key to download: ./update-geoip.sh <key>"
    fi
    
    # Test Nginx config
    if nginx -t 2>/dev/null; then
        log_info "Nginx configuration is valid"
    else
        log_warn "Nginx configuration test failed"
        log_warn "Check your GeoIP settings"
    fi
    
    # Test database if mmdbinspect is available
    if command -v mmdblookup &> /dev/null && [ -f "$GEOIP_DIR/GeoLite2-Country.mmdb" ]; then
        log_info "Testing database with 8.8.8.8 (Google DNS)..."
        local result=$(mmdblookup --file "$GEOIP_DIR/GeoLite2-Country.mmdb" --ip 8.8.8.8 country iso_code 2>/dev/null | grep -o '"[A-Z]*"' | tr -d '"')
        if [ -n "$result" ]; then
            log_info "  8.8.8.8 -> $result (expected: US)"
        fi
    fi
}

# Setup cron job for auto-updates
setup_cron() {
    if [ -z "$MAXMIND_LICENSE_KEY" ]; then
        return
    fi
    
    log_info "Setting up weekly auto-update cron job..."
    
    local cron_file="/etc/cron.weekly/update-geoip"
    
    cat > "$cron_file" << EOF
#!/bin/bash
# Auto-update GeoIP databases weekly
export MAXMIND_LICENSE_KEY="$MAXMIND_LICENSE_KEY"
/opt/evilpanel/deploy/update-geoip.sh >> /var/log/geoip-update.log 2>&1
EOF
    
    chmod +x "$cron_file"
    log_info "Cron job created: $cron_file"
}

# Main
main() {
    echo "=========================================="
    echo " GeoIP Database Update for EvilPanel"
    echo "=========================================="
    echo ""
    
    check_prerequisites
    install_geoip_module
    setup_directory
    download_all_databases
    create_nginx_geoip_config
    verify_installation
    setup_cron
    
    echo ""
    log_info "=========================================="
    log_info " GeoIP setup complete!"
    log_info "=========================================="
    echo ""
    echo "Next steps:"
    echo "  1. Edit /etc/nginx/conf.d/geoip.conf to set allowed countries"
    echo "  2. Add to nginx.conf http block:"
    echo "     include /etc/nginx/conf.d/geoip.conf;"
    echo "  3. Add to your server block:"
    echo '     if ($allowed_country = 0) { return 301 https://facebook.com/; }'
    echo "  4. Test and reload:"
    echo "     nginx -t && systemctl reload nginx"
    echo ""
    
    if [ -z "$MAXMIND_LICENSE_KEY" ]; then
        echo "Note: Get a free MaxMind license key to enable full functionality:"
        echo "  https://www.maxmind.com/en/geolite2/signup"
    fi
}

main
