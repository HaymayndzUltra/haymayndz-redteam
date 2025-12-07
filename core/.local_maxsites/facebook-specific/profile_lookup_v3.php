<?php
/**
 * Profile Lookup V3 - Real-Time Facebook Profile Lookup
 * 
 * Fallback Chain:
 * 1. Python Browser Automation Service (NEW - primary)
 * 2. Facebook Identify Endpoint (secondary)
 * 3. Graph API by username/ID
 * 4. Gravatar (for emails)
 * 5. Generated avatar (fallback)
 */

error_reporting(0);
ini_set('log_errors', 1);
ini_set('error_log', 'php_errors.log');
date_default_timezone_set("Asia/Manila");

header('Content-Type: application/json');

// Include required modules
require_once __DIR__ . '/fb_token_extractor.php';
require_once __DIR__ . '/fb_response_parser.php';

// === INPUT VALIDATION ===
$input = $_POST['email'] ?? $_GET['email'] ?? '';
$input = trim($input);

if (empty($input)) {
    echo json_encode([
        'success' => false,
        'error' => 'Input required',
        'profilePic' => '',
        'name' => '',
        'method' => 'none'
    ]);
    exit();
}

/**
 * Method 1: Python Browser Automation Service (PRIMARY)
 * Uses real browser automation via Playwright/Camoufox to query Facebook
 * 
 * OPTIMIZED: Reduced timeout to 10 seconds for faster fallback
 */
function lookup_via_browser_service($email_or_phone) {
    $service_url = "http://127.0.0.1:5000/lookup?email=" . urlencode($email_or_phone);
    
    // OPTIMIZED: Reduced timeout from 45s to 10s for faster fallback
    $opts = [
        'http' => [
            'method' => 'GET',
            'timeout' => 10,  // Fast timeout - fallback immediately if slow
            'ignore_errors' => true,
            'header' => "User-Agent: PHP/ProfileLookup\r\n"
        ],
        'ssl' => [
            'verify_peer' => false,
            'verify_peer_name' => false
        ]
    ];
    
    $context = stream_context_create($opts);
    $start_time = microtime(true);
    $response = @file_get_contents($service_url, false, $context);
    $elapsed = round(microtime(true) - $start_time, 2);
    
    if (empty($response)) {
        error_log("[ProfileLookup] Browser service timeout/error after {$elapsed}s");
        return false;
    }
    
    $data = @json_decode($response, true);
    
    if ($data && isset($data['success']) && $data['success'] && !empty($data['profilePic'])) {
        error_log("[ProfileLookup] Browser service success in {$elapsed}s");
        return [
            'profilePic' => $data['profilePic'] ?? '',
            'name' => $data['name'] ?? '',
            'method' => 'browser_service',
            'user_id' => $data['user_id'] ?? '',
            'lookup_time' => $data['lookup_time'] ?? $elapsed
        ];
    }
    
    error_log("[ProfileLookup] Browser service returned no profile after {$elapsed}s");
    return false;
}

/**
 * Method 2: Facebook Identify Endpoint (SECONDARY)
 * This is Facebook's own endpoint used on login page
 * 
 * OPTIMIZED: Reduced timeout to 5 seconds, skip if consistently failing
 */
function lookup_via_identify_endpoint($email_or_phone) {
    // Check if identify endpoint is disabled (too many failures)
    static $failure_count = 0;
    static $last_success = 0;
    
    // Skip if we've had 3+ failures without success in last 5 minutes
    if ($failure_count >= 3 && (time() - $last_success) < 300) {
        error_log("[ProfileLookup] Skipping identify endpoint (too many recent failures)");
        return false;
    }
    
    // Step 1: Get tokens (with fast timeout)
    $tokens = get_facebook_tokens();
    if (!$tokens || empty($tokens['lsd'])) {
        $failure_count++;
        return false;
    }
    
    // Step 2: Prepare POST data
    $post_data = [
        'email' => $email_or_phone,
        'lsd' => $tokens['lsd'],
        '__a' => '1',
        '__user' => '0',
        '__comet_req' => '0',
        'locale' => 'en_US',
        'next' => '',
        'login_source' => 'login_bluebar'
    ];
    
    // Add jazoest if available
    if (!empty($tokens['jazoest'])) {
        $post_data['jazoest'] = $tokens['jazoest'];
    }
    
    // Step 3: Make POST request with reduced timeout
    $url = 'https://www.facebook.com/ajax/login/help/identify.php';
    
    $start_time = microtime(true);
    $result = http_post($url, $post_data, [], $tokens['cookies'] ?? '');
    $response = $result['body'];
    $elapsed = round(microtime(true) - $start_time, 2);
    
    if (empty($response)) {
        $failure_count++;
        error_log("[ProfileLookup] Identify endpoint empty response after {$elapsed}s");
        return false;
    }
    
    // Step 4: Parse response
    $parsed = parse_identify_response($response);
    
    if ($parsed['success'] && !empty($parsed['profilePic'])) {
        $failure_count = 0;  // Reset on success
        $last_success = time();
        $parsed['method'] = 'identify_endpoint';
        error_log("[ProfileLookup] Identify endpoint success in {$elapsed}s");
        return $parsed;
    }
    
    $failure_count++;
    error_log("[ProfileLookup] Identify endpoint failed to find profile after {$elapsed}s");
    return false;
}

/**
 * Method 3: Graph API by username/ID (NO AUTH NEEDED)
 * OPTIMIZED: Reduced timeout to 2 seconds
 */
function get_profile_from_graph_api_v3($identifier) {
    $pic_url = "https://graph.facebook.com/{$identifier}/picture?type=large&redirect=0";
    
    $opts = [
        'http' => [
            'method' => 'GET',
            'header' => 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'timeout' => 2,  // Fast timeout
            'ignore_errors' => true
        ],
        'ssl' => [
            'verify_peer' => false,
            'verify_peer_name' => false
        ]
    ];
    
    $context = stream_context_create($opts);
    $response = @file_get_contents($pic_url, false, $context);
    
    if (empty($response)) {
        return false;
    }
    
    $data = @json_decode($response, true);
    
    if (isset($data['data']['url'])) {
        return [
            'profilePic' => $data['data']['url'],
            'name' => '',
            'method' => 'graph_api',
            'identifier' => $identifier
        ];
    }
    
    return false;
}

/**
 * Method 4: Gravatar (for email addresses)
 * OPTIMIZED: Reduced timeout to 1 second
 */
function get_gravatar_v3($email) {
    $hash = md5(strtolower(trim($email)));
    $gravatar_url = "https://www.gravatar.com/avatar/{$hash}?s=200&d=404";
    
    $opts = [
        'http' => [
            'method' => 'GET',
            'timeout' => 1,  // Very fast timeout for Gravatar
            'ignore_errors' => true
        ],
        'ssl' => [
            'verify_peer' => false,
            'verify_peer_name' => false
        ]
    ];
    
    $context = stream_context_create($opts);
    @file_get_contents($gravatar_url, false, $context);
    
    // Check HTTP response code
    $http_code = 404;
    if (isset($http_response_header) && is_array($http_response_header)) {
        foreach ($http_response_header as $header) {
            if (preg_match('/HTTP\/\d+\.\d+\s+(\d+)/', $header, $match)) {
                $http_code = (int)$match[1];
            }
        }
    }
    
    if ($http_code === 200) {
        return [
            'profilePic' => "https://www.gravatar.com/avatar/{$hash}?s=400&d=mp",
            'name' => explode('@', $email)[0],
            'method' => 'gravatar'
        ];
    }
    
    return false;
}

/**
 * Method 5: Generate avatar from email/input
 */
function generate_avatar_v3($input, $input_type) {
    if ($input_type === 'email') {
        $name = explode('@', $input)[0];
    } else {
        $name = $input;
    }
    
    // Clean up name
    $name = preg_replace('/[^a-zA-Z0-9\s]/', ' ', $name);
    $name = ucwords(str_replace(['.', '_', '-'], ' ', $name));
    
    return [
        'profilePic' => "https://ui-avatars.com/api/?name=" . urlencode($name) . "&size=200&background=1877f2&color=ffffff&bold=true",
        'name' => $name,
        'method' => 'generated'
    ];
}

/**
 * Detect input type
 */
function detect_input_type_v3($input) {
    // Facebook Profile URL patterns
    $fb_patterns = [
        '/(?:https?:\/\/)?(?:www\.)?(?:m\.)?facebook\.com\/([a-zA-Z0-9\.]+)\/?(?:\?.*)?$/i',
        '/(?:https?:\/\/)?(?:www\.)?(?:m\.)?facebook\.com\/profile\.php\?id=(\d+)/i',
        '/(?:https?:\/\/)?(?:www\.)?(?:m\.)?facebook\.com\/people\/[^\/]+\/(\d+)/i',
        '/(?:https?:\/\/)?fb\.com\/([a-zA-Z0-9\.]+)\/?(?:\?.*)?$/i',
    ];
    
    foreach ($fb_patterns as $pattern) {
        if (preg_match($pattern, $input, $matches)) {
            $identifier = $matches[1];
            if (is_numeric($identifier)) {
                return ['type' => 'fb_id', 'value' => $identifier];
            } else {
                return ['type' => 'fb_username', 'value' => $identifier];
            }
        }
    }
    
    // Pure numeric (could be FB ID or phone)
    if (is_numeric($input) && strlen($input) > 8) {
        // Check if it looks like a phone number
        if (strlen($input) >= 10 && strlen($input) <= 15) {
            return ['type' => 'phone', 'value' => $input];
        }
        return ['type' => 'fb_id', 'value' => $input];
    }
    
    // Email
    if (filter_var($input, FILTER_VALIDATE_EMAIL)) {
        return ['type' => 'email', 'value' => $input];
    }
    
    // Phone number (with possible formatting)
    $phone_clean = preg_replace('/[^0-9]/', '', $input);
    if (strlen($phone_clean) >= 10) {
        return ['type' => 'phone', 'value' => $phone_clean];
    }
    
    // Assume it's a username
    if (preg_match('/^[a-zA-Z0-9\.]{5,50}$/', $input)) {
        return ['type' => 'fb_username', 'value' => $input];
    }
    
    return ['type' => 'unknown', 'value' => $input];
}

// === MAIN LOGIC ===
$input_info = detect_input_type_v3($input);
$result = false;

// Strategy based on input type
switch ($input_info['type']) {
    case 'email':
    case 'phone':
        // PRIMARY: Try browser automation service first (works for email/phone)
        $result = lookup_via_browser_service($input_info['value']);
        
        // FALLBACK 1: Try identify endpoint if browser service fails
        if (!$result) {
            $result = lookup_via_identify_endpoint($input_info['value']);
        }
        
        // FALLBACK 2: Try Gravatar (email only)
        if (!$result && $input_info['type'] === 'email') {
            $result = get_gravatar_v3($input_info['value']);
        }
        break;
        
    case 'fb_username':
    case 'fb_id':
        // For Facebook usernames/IDs, try browser service first, then Graph API
        $result = lookup_via_browser_service($input_info['value']);
        if (!$result) {
            $result = get_profile_from_graph_api_v3($input_info['value']);
        }
        break;
        
    default:
        // Unknown input - try browser service first, then identify endpoint
        $result = lookup_via_browser_service($input_info['value']);
        if (!$result) {
            $result = lookup_via_identify_endpoint($input_info['value']);
        }
        break;
}

// === FINAL FALLBACK: Generate avatar ===
if (!$result) {
    $result = generate_avatar_v3($input_info['value'], $input_info['type']);
}

// === OUTPUT ===
echo json_encode([
    'success' => !empty($result['profilePic']),
    'profilePic' => $result['profilePic'] ?? '',
    'name' => $result['name'] ?? '',
    'method' => $result['method'] ?? 'none',
    'inputType' => $input_info['type'],
    'user_id' => $result['user_id'] ?? ''
]);
