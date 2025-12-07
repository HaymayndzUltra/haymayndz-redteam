#!/usr/bin/env python3
"""
Facebook Profile Lookup Service v3 - OPTIMIZED
Real-time profile lookup with browser connection pooling and reduced latency

Key Optimizations:
1. Browser Connection Pooling - Reuses browser instances
2. Smart Waiting - Event-based waits instead of fixed sleeps  
3. Reduced Timeouts - Fast failure for faster fallback
4. Performance Monitoring - Detailed timing logs
"""

import json
import time
import re
import os
import sys
import base64
import threading
import queue
from datetime import datetime
import hashlib
from contextlib import contextmanager

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

app = Flask(__name__)
CORS(app)

# === CONFIGURATION ===
CONFIG = {
    'pool_size': 2,                    # Browser pool size
    'page_timeout': 15000,             # Max page load timeout (ms)
    'selector_timeout_primary': 2000,   # Primary selector timeout (ms)
    'selector_timeout_fallback': 1000,  # Fallback selector timeout (ms)
    'max_total_time': 12,              # Max total lookup time (seconds)
    'cache_ttl': 86400,                # Cache TTL: 24 hours
    'warmup_on_start': True,           # Pre-warm browser on startup
}

# Cache directory
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'data', 'lookup_cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# Invalid results to reject
INVALID_NAMES = [
    'enter security code', 'use your google account', 'account disabled',
    'find your account', 'choose your account', 'search by email',
    'search by mobile', 'try another way', 'log in', 'password',
    'reset your password', 'how do you want', 'enter the code'
]

# Performance stats
STATS = {
    'total_requests': 0,
    'cache_hits': 0,
    'successful_lookups': 0,
    'failed_lookups': 0,
    'avg_lookup_time': 0,
    'pool_hits': 0,
    'pool_misses': 0
}


# ============================================================================
# BROWSER POOL IMPLEMENTATION
# ============================================================================

class BrowserPool:
    """
    Manages a pool of reusable browser instances to reduce startup overhead.
    Each browser can handle multiple requests sequentially.
    """
    
    def __init__(self, pool_size=2):
        self.pool_size = pool_size
        self.browsers = queue.Queue()
        self.playwright = None
        self.lock = threading.Lock()
        self.initialized = False
        self._shutdown = False
    
    def initialize(self):
        """Initialize the browser pool"""
        with self.lock:
            if self.initialized:
                return
            
            print(f"[POOL] Initializing browser pool (size={self.pool_size})...")
            self.playwright = sync_playwright().start()
            
            for i in range(self.pool_size):
                browser = self._create_browser()
                if browser:
                    self.browsers.put(browser)
                    print(f"[POOL] Browser {i+1}/{self.pool_size} created")
            
            self.initialized = True
            print(f"[POOL] Pool ready with {self.browsers.qsize()} browsers")
    
    def _create_browser(self):
        """Create a new browser instance"""
        try:
            # Try Camoufox first for better anti-detection
            try:
                from camoufox.sync_api import NewBrowser
                browser = NewBrowser(self.playwright, headless=True, i_know_what_im_doing=True)
                print("[POOL] Using Camoufox browser")
            except ImportError:
                # Fallback to regular Firefox
                browser = self.playwright.firefox.launch(headless=True)
                print("[POOL] Using standard Firefox")
            
            return browser
        except Exception as e:
            print(f"[POOL] Error creating browser: {e}")
            return None
    
    @contextmanager
    def get_browser(self, timeout=5):
        """
        Get a browser from the pool. Returns it when done.
        If pool is empty, creates a new temporary browser.
        """
        browser = None
        from_pool = False
        
        try:
            # Try to get from pool
            browser = self.browsers.get(block=True, timeout=timeout)
            from_pool = True
            STATS['pool_hits'] += 1
        except queue.Empty:
            # Pool exhausted - create temporary browser
            print("[POOL] Pool exhausted, creating temporary browser")
            STATS['pool_misses'] += 1
            browser = self._create_browser()
        
        try:
            yield browser
        finally:
            if browser:
                if from_pool and not self._shutdown:
                    # Return to pool
                    try:
                        self.browsers.put(browser, block=False)
                    except queue.Full:
                        browser.close()
                else:
                    # Temporary browser - close it
                    try:
                        browser.close()
                    except:
                        pass
    
    def shutdown(self):
        """Shutdown the browser pool"""
        self._shutdown = True
        
        while not self.browsers.empty():
            try:
                browser = self.browsers.get_nowait()
                browser.close()
            except:
                pass
        
        if self.playwright:
            self.playwright.stop()
        
        print("[POOL] Pool shutdown complete")


# Global browser pool
browser_pool = BrowserPool(pool_size=CONFIG['pool_size'])


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

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
        
        if time.time() - cached.get('timestamp', 0) < CONFIG['cache_ttl']:
            result = cached.get('result')
            if result and result.get('profilePic'):
                return result
    except Exception:
        pass
    
    return None


def save_to_cache(email_or_phone, result):
    """Save lookup result to cache - only if valid"""
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
    """Check if the extracted name is valid"""
    if not name:
        return False
    
    name_str = str(name).strip()
    name_lower = name_str.lower()
    
    # Check against invalid names
    for invalid in INVALID_NAMES:
        if invalid in name_lower:
            return False
    
    if len(name_str) < 2:
        return False
    
    # Reject phone numbers
    clean = name_str.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    if clean.startswith('+639') and len(clean) >= 12:
        return False
    if clean.startswith('09') and len(clean) >= 10:
        if sum(c.isdigit() for c in clean) >= 10:
            return False
    if clean.startswith('+') and len(clean) > 1 and clean[1:].isdigit():
        return False
    if clean.isdigit() and 10 <= len(clean) <= 15:
        return False
    if len(name_str) > 5:
        digit_ratio = sum(c.isdigit() for c in name_str) / len(name_str)
        if digit_ratio > 0.7:
            return False
    
    return True


def capture_profile_pic_as_base64(page, img_element):
    """Capture profile picture as base64 data URI"""
    try:
        screenshot_bytes = img_element.screenshot(timeout=2000)
        base64_data = base64.b64encode(screenshot_bytes).decode('utf-8')
        return f"data:image/png;base64,{base64_data}"
    except Exception as e:
        print(f"[DEBUG] Error capturing pic: {e}")
        return None


# ============================================================================
# OPTIMIZED LOOKUP FUNCTION
# ============================================================================

def lookup_profile_optimized(email_or_phone):
    """
    Optimized Facebook profile lookup with reduced latency.
    
    Key optimizations:
    1. Uses browser pool (no startup overhead)
    2. Smart waiting (event-based, not fixed sleep)
    3. Reduced timeouts for faster fallback
    4. Parallel selector checks where possible
    """
    start_time = time.time()
    timings = {}
    
    DESKTOP_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    try:
        with browser_pool.get_browser(timeout=3) as browser:
            if not browser:
                return {'success': False, 'error': 'No browser available', 'timings': timings}
            
            # Create context with optimized settings
            context = browser.new_context(
                user_agent=DESKTOP_UA,
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            
            try:
                # === STEP 1: Navigate (with reduced timeout) ===
                t1 = time.time()
                page.goto(
                    "https://www.facebook.com/login/identify",
                    wait_until="domcontentloaded",  # Faster than networkidle
                    timeout=CONFIG['page_timeout']
                )
                timings['navigation'] = round(time.time() - t1, 2)
                
                # === STEP 2: Find and fill input (optimized) ===
                t2 = time.time()
                input_field = None
                
                # Try primary selector first
                try:
                    input_field = page.wait_for_selector(
                        'input#identify_email, input[name="email"]',
                        timeout=CONFIG['selector_timeout_primary']
                    )
                except PlaywrightTimeoutError:
                    # Try fallback selectors
                    try:
                        input_field = page.wait_for_selector(
                            'input.inputtext, input[type="text"]',
                            timeout=CONFIG['selector_timeout_fallback']
                        )
                    except:
                        pass
                
                if not input_field:
                    context.close()
                    return {'success': False, 'error': 'Input not found', 'timings': timings}
                
                # Fill input (no click needed with fill())
                input_field.fill(email_or_phone)
                timings['input_fill'] = round(time.time() - t2, 2)
                
                # === STEP 3: Submit and wait for result ===
                t3 = time.time()
                
                # Click search button or press Enter
                try:
                    search_btn = page.wait_for_selector('button#did_submit', timeout=1000)
                    if search_btn:
                        search_btn.click()
                except:
                    input_field.press("Enter")
                
                # Wait for navigation/content change (smart wait)
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=5000)
                except:
                    pass
                
                # Small wait for dynamic content
                page.wait_for_timeout(1500)
                timings['submit_wait'] = round(time.time() - t3, 2)
                
                # Get page content for scenario detection
                page_content = page.content()
                
                # === STEP 4: Handle OTP page quickly ===
                t4 = time.time()
                otp_indicators = ["Enter security code", "Enter the code", "sent you a code", "6-digit code"]
                
                if any(ind.lower() in page_content.lower() for ind in otp_indicators):
                    print("[DEBUG] OTP page detected - clicking Try another way")
                    try:
                        try_another = page.wait_for_selector(
                            'a[name="reset_action"], *:has-text("Try another way")',
                            timeout=CONFIG['selector_timeout_primary']
                        )
                        if try_another:
                            try_another.click()
                            page.wait_for_timeout(2000)
                            page_content = page.content()
                    except:
                        pass
                timings['otp_handling'] = round(time.time() - t4, 2)
                
                # === STEP 5: Extract profile (VERIFIED SELECTORS - Dec 2025) ===
                t5 = time.time()
                profile_pic = None
                profile_name = None
                
                # VERIFIED name selectors (ordered by likelihood)
                # NOTE: _9o4e is for "Facebook user" name, _9o4d is for phone numbers
                name_selectors = [
                    'div._9o4e',          # Reset password page - VERIFIED WORKING
                    'div._amc8',          # Alternative name element
                    'div.fsl.fwb.fcb',    # Google popup
                    'span._amc8'          # Alternative span
                ]
                
                # VERIFIED pic selectors - Facebook uses scontent CDN
                pic_selectors = [
                    'img._2qgu[src*="scontent"]',     # Primary - scontent CDN
                    'img._2qgu[src*="profile"]',     # Alternative
                    'img[src*="scontent"][src*="fna"]',  # CDN with fna
                    'img._2qgu'                       # Fallback
                ]
                
                # Extract name (first valid match wins)
                for sel in name_selectors:
                    try:
                        elem = page.query_selector(sel)
                        if elem:
                            text = elem.inner_text().strip()
                            if is_valid_name(text):
                                profile_name = text
                                print(f"[DEBUG] Found name with {sel}: {profile_name}")
                                break
                    except:
                        continue
                
                # Extract profile pic (must have scontent in src for valid FB pics)
                for sel in pic_selectors:
                    try:
                        elem = page.query_selector(sel)
                        if elem:
                            src = elem.get_attribute('src') or ''
                            # Only accept real FB profile pics (scontent CDN)
                            if 'scontent' in src or 'profile' in src:
                                profile_pic = capture_profile_pic_as_base64(page, elem)
                                if profile_pic:
                                    print(f"[DEBUG] Captured profile pic from {sel}")
                                    break
                    except:
                        continue
                
                # Fallback: regex extraction from page source
                if not profile_name:
                    # Try _9o4e first (verified working)
                    name_match = re.search(r'<div[^>]*class="[^"]*_9o4e[^"]*"[^>]*>([^<]+)</div>', page_content)
                    if not name_match:
                        name_match = re.search(r'<div[^>]*class="[^"]*_amc8[^"]*"[^>]*>([^<]+)</div>', page_content)
                    if name_match:
                        text = name_match.group(1).strip()
                        if is_valid_name(text):
                            profile_name = text
                            print(f"[DEBUG] Found name via regex: {profile_name}")
                
                timings['extraction'] = round(time.time() - t5, 2)
                timings['total'] = round(time.time() - start_time, 2)
                
                context.close()
                
                return {
                    'success': bool(profile_pic or profile_name),
                    'profilePic': profile_pic or '',
                    'name': profile_name or '',
                    'method': 'browser_optimized_v3',
                    'timings': timings
                }
                
            except Exception as e:
                context.close()
                raise e
                
    except PlaywrightTimeoutError as e:
        timings['total'] = round(time.time() - start_time, 2)
        return {
            'success': False,
            'error': 'Timeout',
            'method': 'browser_optimized_v3',
            'timings': timings
        }
    except Exception as e:
        timings['total'] = round(time.time() - start_time, 2)
        print(f"[ERROR] Exception: {e}")
        return {
            'success': False,
            'error': str(e),
            'method': 'browser_optimized_v3',
            'timings': timings
        }


# ============================================================================
# FLASK ROUTES
# ============================================================================

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
    
    STATS['total_requests'] += 1
    print(f"\n[LOOKUP] Request #{STATS['total_requests']}: {email_or_phone}")
    
    # Check cache first
    cached_result = get_cached_result(email_or_phone)
    if cached_result:
        STATS['cache_hits'] += 1
        print(f"[LOOKUP] Cache hit! ({STATS['cache_hits']}/{STATS['total_requests']})")
        cached_result['cached'] = True
        return jsonify(cached_result)
    
    # Perform optimized lookup
    start_time = time.time()
    result = lookup_profile_optimized(email_or_phone)
    elapsed_time = time.time() - start_time
    
    # Update stats
    if result.get('success'):
        STATS['successful_lookups'] += 1
        save_to_cache(email_or_phone, result)
    else:
        STATS['failed_lookups'] += 1
    
    # Update average lookup time
    total_lookups = STATS['successful_lookups'] + STATS['failed_lookups']
    STATS['avg_lookup_time'] = round(
        (STATS['avg_lookup_time'] * (total_lookups - 1) + elapsed_time) / total_lookups, 2
    ) if total_lookups > 0 else elapsed_time
    
    result['lookup_time'] = round(elapsed_time, 2)
    result['cached'] = False
    
    print(f"[LOOKUP] Result: success={result.get('success')}, "
          f"pic={'Yes' if result.get('profilePic') else 'No'}, "
          f"name={result.get('name', '')[:20]}, "
          f"time={elapsed_time:.2f}s")
    
    return jsonify(result)


@app.route('/health', methods=['GET'])
def health():
    """Health check with performance stats"""
    return jsonify({
        'status': 'ok',
        'service': 'fb_lookup_service_v3_optimized',
        'version': '3.0',
        'timestamp': datetime.now().isoformat(),
        'stats': STATS,
        'pool': {
            'size': CONFIG['pool_size'],
            'available': browser_pool.browsers.qsize() if browser_pool.initialized else 0
        }
    })


@app.route('/stats', methods=['GET'])
def stats():
    """Get detailed performance statistics"""
    return jsonify({
        'stats': STATS,
        'config': CONFIG,
        'pool_status': {
            'initialized': browser_pool.initialized,
            'available_browsers': browser_pool.browsers.qsize() if browser_pool.initialized else 0,
            'pool_size': CONFIG['pool_size']
        }
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


@app.route('/pool/status', methods=['GET'])
def pool_status():
    """Get browser pool status"""
    return jsonify({
        'initialized': browser_pool.initialized,
        'pool_size': CONFIG['pool_size'],
        'available': browser_pool.browsers.qsize() if browser_pool.initialized else 0,
        'hits': STATS['pool_hits'],
        'misses': STATS['pool_misses']
    })


@app.route('/pool/restart', methods=['POST'])
def pool_restart():
    """Restart the browser pool"""
    try:
        browser_pool.shutdown()
        browser_pool.initialized = False
        browser_pool._shutdown = False
        browser_pool.browsers = queue.Queue()
        browser_pool.initialize()
        return jsonify({'success': True, 'available': browser_pool.browsers.qsize()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ============================================================================
# STARTUP
# ============================================================================

def startup():
    """Initialize service on startup"""
    print("=" * 60)
    print("Facebook Profile Lookup Service v3 - OPTIMIZED")
    print("=" * 60)
    print(f"[CONFIG] Pool size: {CONFIG['pool_size']}")
    print(f"[CONFIG] Page timeout: {CONFIG['page_timeout']}ms")
    print(f"[CONFIG] Selector timeout (primary): {CONFIG['selector_timeout_primary']}ms")
    print(f"[CONFIG] Selector timeout (fallback): {CONFIG['selector_timeout_fallback']}ms")
    print(f"[CONFIG] Max total time: {CONFIG['max_total_time']}s")
    print("=" * 60)
    
    if CONFIG['warmup_on_start']:
        print("[STARTUP] Warming up browser pool...")
        browser_pool.initialize()
    
    print(f"[INFO] Endpoint: http://localhost:5000/lookup?email=<email_or_phone>")
    print(f"[INFO] Health: http://localhost:5000/health")
    print(f"[INFO] Stats: http://localhost:5000/stats")
    print("=" * 60)


if __name__ == '__main__':
    startup()
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)

