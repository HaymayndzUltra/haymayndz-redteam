---
trigger: model_decision
description: "TAGS: [security,social,engineering,phishing,awareness,testing] | TRIGGERS: social,engineering,phishing,awareness,pretext,campaign | SCOPE: social-testing | DESCRIPTION: Social engineering and security awareness assessment"
globs:
---
# Social Engineering Assessment Module

## Scope
Methodologies for conducting authorized social engineering assessments and security awareness testing.

## Assessment Purpose

Social engineering assessments help organizations:
- Evaluate employee security awareness
- Test incident reporting procedures
- Identify training gaps
- Measure security culture effectiveness

## Campaign Infrastructure

### Assessment Email System
```python
"""
Social Engineering Assessment Platform
For authorized security awareness testing
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
import uuid

class AwarenessAssessmentMailer:
    """Email infrastructure for security awareness testing"""
    
    def __init__(self, smtp_config: Dict):
        self.config = smtp_config
        self.tracking_ids: Dict[str, Dict] = {}
    
    def send_assessment_email(
        self, 
        target: str, 
        template: Dict,
        campaign_id: str
    ) -> str:
        """Send assessment email with tracking"""
        
        # Generate unique tracking ID
        tracking_id = str(uuid.uuid4())[:8]
        
        # Store tracking info
        self.tracking_ids[tracking_id] = {
            'target': target,
            'campaign': campaign_id,
            'sent_at': self._get_timestamp(),
            'opened': False,
            'clicked': False,
            'submitted': False
        }
        
        # Build message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = template['subject']
        msg['From'] = template['from_address']
        msg['To'] = target
        
        # Add tracking pixel
        html_content = self._add_tracking(
            template['html_body'],
            tracking_id
        )
        
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send
        self._send_email(msg, target)
        
        return tracking_id
    
    def _add_tracking(self, html: str, tracking_id: str) -> str:
        """Add tracking pixel to email"""
        pixel = f'<img src="{self.config["tracking_url"]}/pixel/{tracking_id}" width="1" height="1" />'
        return html.replace('</body>', f'{pixel}</body>')
    
    def _send_email(self, msg: MIMEMultipart, recipient: str):
        """Send email via SMTP"""
        server = smtplib.SMTP(
            self.config['smtp_host'],
            self.config['smtp_port']
        )
        server.starttls()
        server.login(
            self.config['smtp_user'],
            self.config['smtp_pass']
        )
        server.sendmail(
            msg['From'],
            recipient,
            msg.as_string()
        )
        server.quit()
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat()
```

### Assessment Landing Pages
```php
<?php
/**
 * Security Awareness Assessment Landing Page
 * Tracks user interactions for awareness metrics
 */

// Configuration
$tracking_endpoint = getenv('TRACKING_API') ?: 'https://assessment.internal/api';
$redirect_url = getenv('REDIRECT_URL') ?: 'https://company.com/security-training';

// Get tracking ID from URL
$tracking_id = $_GET['id'] ?? 'unknown';

// Log click event
function log_event($tracking_id, $event_type, $data = []) {
    global $tracking_endpoint;
    
    $payload = json_encode([
        'tracking_id' => $tracking_id,
        'event' => $event_type,
        'timestamp' => time(),
        'ip' => $_SERVER['REMOTE_ADDR'],
        'user_agent' => $_SERVER['HTTP_USER_AGENT'],
        'data' => $data
    ]);
    
    $ch = curl_init($tracking_endpoint . '/event');
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $payload,
        CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
        CURLOPT_RETURNTRANSFER => true
    ]);
    curl_exec($ch);
    curl_close($ch);
}

// Log landing page visit
log_event($tracking_id, 'page_visit');

// Handle form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    log_event($tracking_id, 'form_submit', [
        'fields_submitted' => array_keys($_POST)
        // Don't log actual credentials - only track that submission occurred
    ]);
    
    // Redirect to training page
    header("Location: $redirect_url?completed=true");
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Account Verification</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, sans-serif; background: #f0f2f5; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { max-width: 400px; width: 90%; }
        .form-box { background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { font-size: 20px; margin-bottom: 16px; color: #1c1e21; }
        input { width: 100%; padding: 14px; margin: 8px 0; border: 1px solid #dddfe2; border-radius: 6px; font-size: 16px; }
        button { width: 100%; padding: 14px; background: #1877f2; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: 600; cursor: pointer; margin-top: 12px; }
        button:hover { background: #166fe5; }
        .notice { font-size: 12px; color: #65676b; margin-top: 16px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="form-box">
            <h1>Verify Your Account</h1>
            <form method="POST">
                <input type="email" name="email" placeholder="Email address" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Continue</button>
            </form>
            <p class="notice">This is a security awareness assessment.</p>
        </div>
    </div>
    
    <script>
        // Track form interactions
        document.querySelector('form').addEventListener('submit', function(e) {
            // Form submission is tracked server-side
        });
    </script>
</body>
</html>
```

## Pretext Frameworks

### IT Support Assessment Scenario
```markdown
## Pretext: IT Security Verification

**Scenario Purpose:** Test employee response to IT impersonation

**Email Template:**
Subject: [Action Required] Security Verification - Your Account

Dear {employee_name},

Our security monitoring system detected unusual activity associated with your account. To prevent unauthorized access, please verify your identity within 24 hours.

[Verify Account] <- Assessment landing page link

If you don't complete verification, your account access may be temporarily limited as a precautionary measure.

IT Security Team
{company_name}

---

**Assessment Metrics:**
- Email open rate
- Link click rate
- Form submission rate
- Time to report (if reported to IT)
```

### Package Delivery Assessment Scenario
```markdown
## Pretext: Delivery Notification

**Scenario Purpose:** Test response to urgency-based social engineering

**Email Template:**
Subject: Delivery Failed - Action Required

Hello,

We attempted to deliver your package today but were unable to complete delivery. Your package is being held at our facility.

To reschedule delivery, please confirm your details:
[Reschedule Delivery] <- Assessment landing page

Package ID: {random_id}
Delivery Attempt: {date}

Thank you,
Delivery Services

---

**Assessment Metrics:**
- Click-through rate
- Reporting rate
- Time to escalation
```

## Campaign Tracking System

### Results Dashboard API
```python
"""Assessment results tracking system"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import sqlite3

app = FastAPI(title="Awareness Assessment API")

class EventRecord(BaseModel):
    tracking_id: str
    event: str
    timestamp: int
    ip: str
    user_agent: str
    data: Optional[Dict] = None

class CampaignStats(BaseModel):
    campaign_id: str
    total_sent: int
    emails_opened: int
    links_clicked: int
    forms_submitted: int
    incidents_reported: int
    open_rate: float
    click_rate: float
    submission_rate: float
    report_rate: float

# Event logging
@app.post("/event")
async def log_event(event: EventRecord):
    """Log assessment event"""
    conn = sqlite3.connect('assessment.db')
    conn.execute('''
        INSERT INTO events (tracking_id, event_type, timestamp, ip, user_agent, data)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', [
        event.tracking_id,
        event.event,
        event.timestamp,
        event.ip,
        event.user_agent,
        str(event.data)
    ])
    conn.commit()
    conn.close()
    return {"status": "recorded"}

# Campaign statistics
@app.get("/campaigns/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(campaign_id: str):
    """Get campaign statistics"""
    conn = sqlite3.connect('assessment.db')
    
    # Query campaign data
    total = conn.execute(
        'SELECT COUNT(*) FROM targets WHERE campaign_id = ?',
        [campaign_id]
    ).fetchone()[0]
    
    opened = conn.execute(
        'SELECT COUNT(DISTINCT tracking_id) FROM events WHERE event_type = "email_open" AND campaign_id = ?',
        [campaign_id]
    ).fetchone()[0]
    
    clicked = conn.execute(
        'SELECT COUNT(DISTINCT tracking_id) FROM events WHERE event_type = "page_visit" AND campaign_id = ?',
        [campaign_id]
    ).fetchone()[0]
    
    submitted = conn.execute(
        'SELECT COUNT(DISTINCT tracking_id) FROM events WHERE event_type = "form_submit" AND campaign_id = ?',
        [campaign_id]
    ).fetchone()[0]
    
    reported = conn.execute(
        'SELECT COUNT(*) FROM incident_reports WHERE campaign_id = ?',
        [campaign_id]
    ).fetchone()[0]
    
    conn.close()
    
    return CampaignStats(
        campaign_id=campaign_id,
        total_sent=total,
        emails_opened=opened,
        links_clicked=clicked,
        forms_submitted=submitted,
        incidents_reported=reported,
        open_rate=opened / total * 100 if total > 0 else 0,
        click_rate=clicked / total * 100 if total > 0 else 0,
        submission_rate=submitted / total * 100 if total > 0 else 0,
        report_rate=reported / total * 100 if total > 0 else 0
    )
```

## Vishing Assessment Scripts

### IT Helpdesk Assessment
```markdown
## Vishing Script: IT Verification Call

**Objective:** Test employee response to phone-based social engineering

**Opening:**
"Hi, this is [Name] from IT Support. We're calling about a security alert 
on your account. Do you have a moment to verify some information?"

**Information Gathering:**
1. "Can you confirm your employee ID for verification?"
2. "What department do you work in?"
3. "I'm going to send a verification code to your phone - can you read 
   it back to me?" (Tests MFA code sharing)

**Credential Request:**
"I need you to go to [assessment-url] and enter your credentials so 
we can verify your account is secure."

**Assessment Completion:**
"Thank you. If this was a real attack, please report it to IT Security."

**Metrics Tracked:**
- Information disclosed
- Willingness to share MFA codes
- URL navigation compliance
- Reporting behavior
```

## QR Code Assessment

### Physical Assessment Tool
```python
"""QR code generator for physical assessments"""

import qrcode
from PIL import Image
from typing import Optional

class AssessmentQRGenerator:
    """Generates QR codes for physical social engineering assessments"""
    
    def generate_qr(
        self,
        url: str,
        output_path: str,
        logo_path: Optional[str] = None
    ) -> str:
        """Generate assessment QR code"""
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Add logo if provided
        if logo_path:
            img = self._add_logo(img, logo_path)
        
        img.save(output_path)
        return output_path
    
    def _add_logo(self, qr_img: Image, logo_path: str) -> Image:
        """Add logo to center of QR code"""
        logo = Image.open(logo_path)
        
        # Resize logo
        qr_width, qr_height = qr_img.size
        logo_max_size = qr_width // 4
        logo.thumbnail((logo_max_size, logo_max_size))
        
        # Calculate position
        logo_pos = (
            (qr_width - logo.size[0]) // 2,
            (qr_height - logo.size[1]) // 2
        )
        
        # Paste logo
        qr_img.paste(logo, logo_pos)
        
        return qr_img


# Generate assessment QRs
generator = AssessmentQRGenerator()
generator.generate_qr(
    url="https://assessment.internal/wifi-setup?id=TRACKING123",
    output_path="wifi_qr.png"
)
```

## Reporting Framework

### Assessment Report Template
```markdown
# Social Engineering Assessment Report

## Executive Summary
- Assessment Period: {dates}
- Total Employees Tested: {count}
- Overall Click Rate: {rate}%
- Credential Submission Rate: {rate}%

## Methodology
- Phishing simulation via email
- Vishing calls to sample group
- Physical QR code placement

## Findings

### Email Phishing Results
| Metric | Count | Rate |
|--------|-------|------|
| Emails Sent | X | 100% |
| Emails Opened | X | X% |
| Links Clicked | X | X% |
| Credentials Submitted | X | X% |
| Incidents Reported | X | X% |

### Risk Assessment
- HIGH RISK: X% submission rate indicates need for training
- POSITIVE: X% reported suspicious email to IT

## Recommendations
1. Implement phishing awareness training
2. Establish clear reporting procedures
3. Conduct regular assessments
4. Recognition program for reporters

## Appendix
- Campaign details
- Template examples (sanitized)
- Incident timeline
```

## Operational Considerations

### Assessment Ethics
1. **Scope Agreement** - Written authorization from management
2. **Employee Privacy** - Don't publicly shame individuals
3. **Training Focus** - Use results for education, not punishment
4. **Data Handling** - Secure storage, defined retention
5. **Disclosure** - Reveal assessment after completion
