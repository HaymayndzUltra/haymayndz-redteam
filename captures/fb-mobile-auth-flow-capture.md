# Facebook Mobile Authentication Flow Capture
## Security Research Documentation

**Date:** 2025-12-07  
**Target:** m.facebook.com/login/identify  
**Purpose:** Authentication flow analysis for security assessment  
**Status:** ✅ Successfully captured

---

## Overview

This document contains the captured authentication flow from Facebook's mobile web login process. The flow follows the modern "identify first" pattern where:

1. User enters email/username
2. Facebook looks up the account and displays profile picture
3. User enters password
4. Authentication completes

---

## Request #1 — Initial Page Load (GET Document)

### General
```
Request URL: https://m.facebook.com/login/identify
Request Method: GET
Status Code: 200
Resource Type: document
```

### Captured Tokens (from page/requests)
```
lsd: AdECJFn-IJ4
jazoest: 2799
fb_dtsg: NAfvIccc6T5AuQhBb4z3E249xqvpIhdVUs_pEbMsHG0HOK5Qf4ep3PA:0:0
lid: 7581009571345652040
tracePolicy: com.bloks.www.caa.ar.search
bloksAppId: fb_web
```

### Device Info (from telemetry)
```
model: SM-G955U
platformVersion: 8.0.0
num_cores: 24
ram_gb: 8
downlink_mb: 10
effective_connection_type: 4g
```

### Associated Requests
```
[POST] /async/wbloks/log/?lid=7581009571345652040&event=RESPONSE_START
[POST] /async/wbloks/log/?lid=7581009571345652040&event=EJP_FLUSHED
[POST] /async/wbloks/log/?lid=7581009571345652040&event=DEVICE_INFO_FETCHED
[POST] /async/wbloks/log/?lid=7581009571345652040&event=DISPLAY_JS_DONE
[POST] /async/wbloks/log/?lid=7581009571345652040&event=RESPONSE_END
[POST] /async/wbloks/log/?lid=7581009571345652040&event=WBLOKS_INVOKED
[POST] /async/wbloks/log/?lid=7581009571345652040&event=ROOT_MOUNTED
```

---

## Request #2 — Account Search (caa.ar.search.async)

### General
```
Request URL: https://m.facebook.com/async/wbloks/fetch/?appid=com.bloks.www.caa.ar.search.async&type=action&__bkv=5870af81e45750eb22160e3fe74a22f1ec7a22fa20d66f6fa34875f44676e658
Request Method: POST
```

### URL Parameters
```
appid: com.bloks.www.caa.ar.search.async
type: action
__bkv: 5870af81e45750eb22160e3fe74a22f1ec7a22fa20d66f6fa34875f44676e658
```

### Request Headers (Template)
```
Content-Type: application/x-www-form-urlencoded
Origin: https://m.facebook.com
Referer: https://m.facebook.com/login/identify
User-Agent: [Mobile Chrome on Android]

Cookie: datr=XXXXXX...REDACTED; sb=XXXXXX...REDACTED; [other cookies]
```

### Payload Structure
```
fb_dtsg: NAfvIccc6T5AuQhBb4z3E249xqvpIhdVUs_pEbMsHG0HOK5Qf4ep3PA:0:0
jazoest: 24826
lsd: AdECJFn-IJ4
__dyn: 0wzpawlE72fDg9ppo5S12wAxu13wqobE6u7E39x60lW4o0wW1gCwjE0AC09Mx60se2G0pS0ny0oi0zE5W0Y81soG0xo2ewbS1LwpEcE1kU1bo8Xw8S0QU3yw
__csr: [empty]
__req: 7
__a: AYy40oE89wKZ-OK2R_8lmoOD0TPPU3yog4dveMAZ169NHvqK0tfefAQzqq3kYLpg1WIYlrJDh_rGs-CtK5bR2_UklAx0z29CLAQ
__user: 0
__wma: 1

# Payload contains:
# - contact_point: [encoded email/username - AY... format]
# - client_input_params: JSON with search parameters
# - server_params: JSON with server-side context
```

### Notes
- This request searches for the account based on entered email/username
- Returns account info including profile picture URL and display name
- `__user: 0` indicates not yet authenticated

---

## Request #3 — Auth Method Selection (caa.ar.auth_method)

### General
```
Request URL: https://m.facebook.com/async/wbloks/fetch/?appid=com.bloks.www.caa.ar.auth_method&type=app&__bkv=5870af81e45750eb22160e3fe74a22f1ec7a22fa20d66f6fa34875f44676e658
Request Method: POST
```

### URL Parameters
```
appid: com.bloks.www.caa.ar.auth_method
type: app
__bkv: 5870af81e45750eb22160e3fe74a22f1ec7a22fa20d66f6fa34875f44676e658
```

### Response Data
```
Account Found: Berdugo Agila
Profile Picture: https://www.facebook.com/profile/pic.php?cuid=AYg89zwj_LqNDTk7lbtQhvf3jhZ9tkNIOR9p60Ok75xlBpYoVB5FwiISZof08lnqaeh5-tPHp_7Ly4HugxCchgD1__QhriMRqPekkPn3XdxuNDYfYFox_FGMcm8t5af97yobxio6mXKrK4Ued-4rRKPu5OTBM2LVlSKaDm4i7zYFOehkOAPkEHBdEEzlHcS2I8LbwCo5BanR0dkpdImX5OswBg1sDG7NVmgaYN9ZlP_VrLaEebQczqH1UA2gDBg1ZW4&square_px=180
Auth Methods Available: password
```

### Notes
- This request retrieves the authentication methods available for the account
- Returns profile picture and name for display
- Typically returns "password" as primary auth method

---

## Request #4 — Password POST (CRITICAL - caa.login.async)

### General
```
Request URL: https://m.facebook.com/async/wbloks/fetch/?appid=com.bloks.www.bloks.caa.login.async.send_login_request&type=action&__bkv=5870af81e45750eb22160e3fe74a22f1ec7a22fa20d66f6fa34875f44676e658
Request Method: POST
Status Code: 200
```

### URL Parameters
```
appid: com.bloks.www.bloks.caa.login.async.send_login_request
type: action
__bkv: 5870af81e45750eb22160e3fe74a22f1ec7a22fa20d66f6fa34875f44676e658
```

### Request Headers (Template)
```
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US,en;q=0.9
Content-Type: application/x-www-form-urlencoded
Origin: https://m.facebook.com
Referer: https://m.facebook.com/login/identify
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
User-Agent: Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.7444.176 Mobile Safari/537.36

Cookie: datr=XXXXXX...REDACTED; sb=XXXXXX...REDACTED; fr=XXXXXX...REDACTED; [other session cookies]
```

### Payload Structure (Form Data)
```
fb_dtsg=NAfvIccc6T5AuQhBb4z3E249xqvpIhdVUs_pEbMsHG0HOK5Qf4ep3PA:0:0
jazoest=24826
lsd=AdECJFn-IJ4
__dyn=0wzpawlE72fDg9ppo5S12wAxu13wqobE6u7E39x60lW4o0wW1gCwjE0AC09Mx60se2G0pS0ny0oi0zE5W0Y81soG0xo2ewbS1LwpEcE1kU1bo8Xw8S0QU3yw
__csr=
__hsdp=
__hblp=
__sjsp=
__req=c
__fmt=1
__a=AYy40oE89wKZ-OK2R_8lmoOD0TPPU3yog4dveMAZ169NHvqK0tfefAQzqq3kYLpg1WIYlrJDh_rGs-CtK5bR2_UklAx0z29CLAQ
__user=0
__wma=1

# Critical fields in params (JSON encoded):
# password: #PWD_BROWSER:5:TIMESTAMP:ENCRYPTED_PASSWORD_BLOB
# contact_point: AY... (encoded identifier)
# credentials_type: password
# generate_session_cookies: 1
# device_id: [device identifier]
```

### Password Encoding Format
```
Format: #PWD_BROWSER:VERSION:TIMESTAMP:ENCRYPTED_DATA
Example: #PWD_BROWSER:5:1765091500:AY...REDACTED

Where:
- VERSION: Encryption version (typically 5)
- TIMESTAMP: Unix timestamp of encryption
- ENCRYPTED_DATA: Base64/encrypted password blob
```

---

## Request #5 — Post-Login Save Credentials

### General
```
Request URL: https://m.facebook.com/async/wbloks/fetch/?appid=com.bloks.www.caa.login.save-credentials&type=app&__bkv=5870af81e45750eb22160e3fe74a22f1ec7a22fa20d66f6fa34875f44676e658
Request Method: POST
```

### Response Headers (Set-Cookie) — CRITICAL
```
Set-Cookie: c_user=100095251969319; [attributes]
Set-Cookie: xs=XXXXXX...REDACTED; [attributes]
Set-Cookie: fr=XXXXXX...REDACTED; [attributes]
Set-Cookie: datr=XXXXXX...REDACTED; [attributes]

# Successful login indicated by presence of:
# - c_user (Facebook user ID)
# - xs (session token)
```

### Post-Login State
```
New __user: 100095251969319
New fb_dtsg: NAftzBD40PX3wyBQiTwUjeYziCtQVeUqZkjBjfeYDc-GSz5uhrI9VRw:28:1765091604
New jazoest: 25689
Redirect: https://m.facebook.com/login/save-device/
```

---

## Token Reference

### Pre-Authentication Tokens
| Token | Value | Purpose |
|-------|-------|---------|
| `lsd` | `AdECJFn-IJ4` | CSRF protection |
| `jazoest` | `24826` / `2799` | Request validation |
| `fb_dtsg` | `NAfvIccc6T5A...` | CSRF token |
| `lid` | `7581009571345652040` | Request tracking ID |
| `__bkv` | `5870af81e4575...` | Bloks version key |
| `__a` | `AYy40oE89wKZ...` | Request signature |

### Post-Authentication Tokens
| Token | Value | Purpose |
|-------|-------|---------|
| `c_user` | `100095251969319` | User ID |
| `xs` | `[REDACTED]` | Session token |
| `fb_dtsg` | `NAftzBD40PX3...` | New CSRF token |
| `jazoest` | `25689` | New request validation |

---

## Cookie Flow

### Initial Cookies (Pre-Login)
```
datr: Device/browser identifier (persistent)
sb: Session browser token
fr: Facebook tracking/remarketing
_js_datr: JavaScript-set datr variant
```

### Post-Login Cookies (Added)
```
c_user: Authenticated user ID
xs: Session authentication token
presence: Online presence tracking
```

---

## Request Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    FACEBOOK MOBILE AUTH FLOW                      │
└─────────────────────────────────────────────────────────────────┘

[1] GET /login/identify
    │
    ├── Response: Login page with email input
    ├── Tokens: lsd, fb_dtsg, jazoest, lid
    └── Cookies: datr, sb (set)

[2] User enters email → Click "Continue"
    │
    ▼
[3] POST /async/wbloks/fetch/?appid=com.bloks.www.caa.ar.search.async
    │
    ├── Payload: contact_point (encoded email)
    ├── Response: Account found/not found
    └── If found → proceed to auth_method

[4] POST /async/wbloks/fetch/?appid=com.bloks.www.caa.ar.auth_method
    │
    ├── Response: Profile picture, name, auth methods
    └── Display: Password input with profile pic

[5] User enters password → Click "Log in"
    │
    ▼
[6] POST /async/wbloks/fetch/?appid=com.bloks.www.bloks.caa.login.async.send_login_request
    │
    ├── Payload: #PWD_BROWSER:5:TIMESTAMP:ENCRYPTED_PASSWORD
    ├── Response: Success/Failure
    └── Set-Cookie: c_user, xs (if successful)

[7] POST /async/wbloks/fetch/?appid=com.bloks.www.caa.login.save-credentials
    │
    ├── Prompt: "Save your login info?"
    └── Final authenticated state
```

---

## Captured Screenshots

| Screenshot | Description |
|------------|-------------|
| `fb-identify-page.png` | Initial "Find your account" page |
| `fb-email-typed.png` | Email entered in input field |
| `fb-profile-pic-password.png` | Profile picture + password field displayed |

---

## Operational Notes

### For Template Replication
1. Initial page must set `datr` cookie (device tracking)
2. All requests require matching `lsd`, `fb_dtsg`, `jazoest` tokens
3. `__bkv` must match current Bloks version
4. Password must be encrypted using `#PWD_BROWSER:5:` format
5. Profile picture endpoint uses `cuid` parameter with encrypted user reference

### Key Endpoints
```
Base: https://m.facebook.com

/login/identify                                    - Entry point
/async/wbloks/fetch/?appid=com.bloks.www.caa.ar.search.async    - Account lookup
/async/wbloks/fetch/?appid=com.bloks.www.caa.ar.auth_method     - Auth method
/async/wbloks/fetch/?appid=com.bloks.www.bloks.caa.login.async.send_login_request - Password submit
/async/wbloks/fetch/?appid=com.bloks.www.caa.login.save-credentials - Save login
/login/save-device/                                - Post-login device save
```

### Success Indicators
- Response contains `c_user` cookie
- Response contains `xs` cookie
- `__user` changes from `0` to actual user ID
- Redirect to `/login/save-device/` or home feed

---

## Disclaimer

This documentation is for authorized security research and penetration testing purposes only. All testing was conducted on accounts owned by the researcher with explicit authorization.

---

*Generated: 2025-12-07*  
*Framework: Security Research Assistant v2.0*

