#!/bin/bash
# GSB Domain Monitor - Auto-alert when domain gets flagged
# Secure version - reads API key from file or environment

# Load API key from secure file or environment
GSB_API_KEY="${GSB_API_KEY:-$(cat ~/.gsb_api_key 2>/dev/null)}"

if [ -z "$GSB_API_KEY" ]; then
    echo "ERROR: GSB_API_KEY not set. Either:"
    echo "  1. Export GSB_API_KEY environment variable"
    echo "  2. Create ~/.gsb_api_key with your API key"
    exit 1
fi

DOMAIN="${1:-whatsappqrscan.site}"
CHECK_INTERVAL="${2:-1800}"  # 30 minutes default

echo "[GSB Monitor] Starting..."
echo "[GSB Monitor] Domain: $DOMAIN"
echo "[GSB Monitor] Check interval: ${CHECK_INTERVAL}s ($(($CHECK_INTERVAL / 60)) minutes)"
echo ""

check_gsb() {
    local domain="$1"
    local result=$(curl -s "https://safebrowsing.googleapis.com/v4/threatMatches:find?key=$GSB_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"client\": {\"clientId\": \"evilpanel-monitor\", \"clientVersion\": \"1.0\"},
            \"threatInfo\": {
                \"threatTypes\": [\"MALWARE\", \"SOCIAL_ENGINEERING\", \"UNWANTED_SOFTWARE\"],
                \"platformTypes\": [\"ANY_PLATFORM\"],
                \"threatEntryTypes\": [\"URL\"],
                \"threatEntries\": [
                    {\"url\": \"https://$domain/\"},
                    {\"url\": \"https://m.$domain/\"},
                    {\"url\": \"https://www.$domain/\"}
                ]
            }
        }" 2>/dev/null)
    
    if echo "$result" | grep -q "matches"; then
        return 1  # Flagged
    fi
    return 0  # Clean
}

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    if check_gsb "$DOMAIN"; then
        echo "[$TIMESTAMP] ✅ $DOMAIN - Clean"
    else
        echo ""
        echo "[$TIMESTAMP] 🚨🚨🚨 ALERT: $DOMAIN FLAGGED BY GSB! 🚨🚨🚨"
        echo ""
        echo "ACTION REQUIRED: Rotate domain immediately!"
        echo ""
        # Exit with error code for automation
        exit 1
    fi
    
    sleep $CHECK_INTERVAL
done

