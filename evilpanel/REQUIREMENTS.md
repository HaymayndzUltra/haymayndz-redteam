# EvilPanel System Requirements

## Server Requirements

### Development Environment (Task 5.3)

| Component | Minimum Spec |
|-----------|-------------|
| CPU | 2 cores |
| RAM | 4 GB |
| Storage | 20 GB SSD |
| OS | Ubuntu 22.04 / Debian 12 |
| Python | 3.10+ |

### Production (Low Volume) - Up to 100 concurrent

| Component | Recommended Spec |
|-----------|-----------------|
| CPU | 4 cores |
| RAM | 8 GB |
| Storage | 50 GB SSD |
| Bandwidth | 100 Mbps |
| OS | Ubuntu 22.04 LTS |

### Production (High Volume) - 500+ concurrent

| Component | Recommended Spec |
|-----------|-----------------|
| CPU | 8 cores |
| RAM | 16 GB |
| Storage | 100 GB NVMe |
| Bandwidth | 1 Gbps |
| OS | Ubuntu 22.04 LTS |

---

## Cloudflare Requirement Matrix (Task 5.4)

### When Cloudflare is REQUIRED

| Scenario | Cloudflare Required | Reason |
|----------|-------------------|--------|
| Public internet deployment | **YES** | DDoS protection, IP masking |
| High-value targets | **YES** | Enhanced anonymity |
| Long-term operations | **YES** | Domain reputation protection |
| Multi-region targeting | **YES** | CDN benefits |

### When Cloudflare is OPTIONAL

| Scenario | Cloudflare Required | Reason |
|----------|-------------------|--------|
| Testing/development | NO | Not needed for local testing |
| Internal network only | NO | No public exposure |
| Short-term single-use | NO | Minimal exposure window |

### Cloudflare Configuration

When using Cloudflare, apply these settings:

```
SSL/TLS:
  - Mode: Full (strict)
  - Always Use HTTPS: ON
  - Min TLS Version: 1.2

Security:
  - Bot Fight Mode: OFF (important!)
  - Challenge Passage: 30 minutes
  - Security Level: Essentially Off

Firewall:
  - Create rule to allow target regions
  - Block suspicious bot traffic manually

Performance:
  - Proxy status: Enabled (orange cloud)
  - Caching Level: Standard
  - Browser Cache TTL: 4 hours

Network:
  - WebSocket: ON
  - HTTP/2: ON
  - 0-RTT: OFF
```

### OPSEC Cloudflare Settings

```
Domain Settings:
  - WHOIS: Privacy protection enabled
  - Registrar: Privacy-focused (Njalla, Namecheap privacy)
  - Domain age: Minimum 30 days before use

Account Settings:
  - Use dedicated email
  - Enable 2FA
  - Use VPN when accessing dashboard
```

---

## Network Requirements

### Ports

| Port | Protocol | Purpose |
|------|----------|---------|
| 443 | HTTPS | AiTM Proxy |
| 8080 | HTTP | Dashboard API |
| 80 | HTTP | Let's Encrypt verification |

### Firewall Rules

```bash
# Allow required ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp

# Enable firewall
sudo ufw enable
```

---

## SSL Certificate Requirements

### Let's Encrypt

- Valid domain name pointing to server IP
- Port 80 open for HTTP-01 challenge
- OR DNS access for DNS-01 challenge (wildcards)

### Certificate Renewal

```bash
# Manual renewal
certbot renew

# Auto-renewal (cron)
0 0,12 * * * certbot renew --quiet
```

---

## Database Requirements

### SQLite (Default)

- Suitable for low to medium volume
- No additional setup required
- File-based storage in `data/evilpanel.db`

### PostgreSQL (Optional)

For high volume deployments:

```bash
# Install
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb evilpanel
sudo -u postgres createuser evilpanel_user
```

---

## Dependencies

### System Packages

```bash
sudo apt update
sudo apt install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    certbot \
    openssl \
    curl \
    git
```

### Python Packages

See `requirements.txt` for full list.

Core dependencies:
- FastAPI >= 0.109.0
- mitmproxy >= 10.2.0
- playwright >= 1.41.0

---

## Quick Start

### Docker (Recommended)

```bash
# Clone repository
git clone <repo-url>
cd maxphisher2-clean

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r evilpanel/requirements.txt

# Install Playwright browsers
playwright install firefox

# Initialize database
python -c "from evilpanel.database.models import Database; Database()"

# Start server
uvicorn evilpanel.dashboard.api.main:app --host 0.0.0.0 --port 8080
```

---

## Monitoring

### Health Check

```bash
curl http://localhost:8080/api/health
```

### Logs

```bash
# Docker logs
docker-compose logs -f evilpanel

# System logs
tail -f /var/log/evilpanel/app.log
```

### Metrics

Dashboard statistics available at:
- `/api/dashboard/stats` - Overview
- `/api/traffic` - Traffic statistics
- `/api/logs` - Captured sessions

