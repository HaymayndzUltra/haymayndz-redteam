<?php
/**
 * Profile Lookup V2 - Multi-Method Facebook Profile Detection
 * 
 * This version uses MULTIPLE lookup methods and does NOT rely solely on stored cookies.
 * 
 * Methods (in priority order):
 * 1. Direct Facebook username/URL → Graph API picture (NO AUTH NEEDED!)
 * 2. Graph API by ID (if ID provided)
 * 3. Fallback to stored cookies only as last resort
 * 4. Graceful fallback with email-derived avatar
 */

error_reporting(E_ALL);
ini_set('display_errors', 1);
ini_set('log_errors', 1);
ini_set('error_log', 'php_errors.log');
date_default_timezone_set("Asia/Manila");

header('Content-Type: application/json');

// === INPUT ===
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

// === DETECT INPUT TYPE ===
function detect_input_type($input) {
    // Facebook Profile URL patterns
    $fb_patterns = [
        // facebook.com/username
        '/(?:https?:\/\/)?(?:www\.)?(?:m\.)?facebook\.com\/([a-zA-Z0-9\.]+)\/?(?:\?.*)?$/i',
        // facebook.com/profile.php?id=123456
        '/(?:https?:\/\/)?(?:www\.)?(?:m\.)?facebook\.com\/profile\.php\?id=(\d+)/i',
        // facebook.com/people/Name/123456
        '/(?:https?:\/\/)?(?:www\.)?(?:m\.)?facebook\.com\/people\/[^\/]+\/(\d+)/i',
        // fb.com/username
        '/(?:https?:\/\/)?fb\.com\/([a-zA-Z0-9\.]+)\/?(?:\?.*)?$/i',
    ];
    
    foreach ($fb_patterns as $pattern) {
        if (preg_match($pattern, $input, $matches)) {
            $identifier = $matches[1];
            // Check if it's a numeric ID or username
            if (is_numeric($identifier)) {
                return ['type' => 'fb_id', 'value' => $identifier];
            } else {
                return ['type' => 'fb_username', 'value' => $identifier];
            }
        }
    }
    
    // Pure numeric (could be FB ID or phone)
    if (is_numeric($input) && strlen($input) > 8) {
        return ['type' => 'fb_id', 'value' => $input];
    }
    
    // Email
    if (filter_var($input, FILTER_VALIDATE_EMAIL)) {
        return ['type' => 'email', 'value' => $input];
    }
    
    // Phone number (stripped)
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

// === HELPER: HTTP Request (curl or file_get_contents) ===
function http_request($url, $options = []) {
    $context_options = [
        'http' => [
            'method' => 'GET',
            'header' => "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\n",
            'timeout' => $options['timeout'] ?? 10,
            'ignore_errors' => true
        ],
        'ssl' => [
            'verify_peer' => false,
            'verify_peer_name' => false
        ]
    ];
    
    if (!empty($options['cookie'])) {
        $context_options['http']['header'] .= "Cookie: {$options['cookie']}\r\n";
    }
    
    $context = stream_context_create($context_options);
    $response = @file_get_contents($url, false, $context);
    
    // Get HTTP response code from headers
    $http_code = 0;
    if (isset($http_response_header) && is_array($http_response_header)) {
        foreach ($http_response_header as $header) {
            if (preg_match('/HTTP\/\d+\.\d+\s+(\d+)/', $header, $matches)) {
                $http_code = (int)$matches[1];
            }
        }
    }
    
    return [
        'body' => $response,
        'http_code' => $http_code
    ];
}

// === METHOD 1: GRAPH API PICTURE (NO AUTH NEEDED!) ===
/**
 * The Graph API picture endpoint is PUBLIC!
 * graph.facebook.com/{username}/picture works without authentication
 */
function get_profile_from_graph_api($identifier) {
    // Test if the identifier is valid by checking if the picture URL returns a redirect
    $pic_url = "https://graph.facebook.com/{$identifier}/picture?type=large&redirect=0";
    
    $result = http_request($pic_url, ['timeout' => 5]);
    
    if ($result['http_code'] !== 200 || empty($result['body'])) {
        return false;
    }
    
    $data = json_decode($result['body'], true);
    
    if (isset($data['data']['url'])) {
        // Valid profile found!
        return [
            'profilePic' => $data['data']['url'],
            'name' => '', // Graph API doesn't return name from picture endpoint
            'method' => 'graph_api',
            'identifier' => $identifier
        ];
    }
    
    return false;
}

// === METHOD 2: SCRAPE PUBLIC PROFILE PAGE ===
/**
 * If profile is public, we can scrape name from the profile page
 * This works WITHOUT authentication for public profiles
 */
function scrape_public_profile($identifier) {
    // Try mbasic first (simpler HTML)
    $url = "https://mbasic.facebook.com/{$identifier}";
    
    $result = http_request($url, ['timeout' => 10]);
    $response = $result['body'];
    
    // Check if we hit a login wall
    if (strpos($response, 'login') !== false && strpos($response, '<title>Log') !== false) {
        return false;
    }
    
    if ($result['http_code'] !== 200 || empty($response)) {
        return false;
    }
    
    $profile_result = [];
    
    // Extract name from title
    if (preg_match('/<title>([^<|]+)/i', $response, $title_match)) {
        $name = trim($title_match[1]);
        if (!preg_match('/^(Facebook|Log|Sign|Error)/i', $name)) {
            $profile_result['name'] = html_entity_decode($name, ENT_QUOTES, 'UTF-8');
        }
    }
    
    // Extract profile ID for picture
    if (preg_match('/entity_id["\']?\s*[:=]\s*["\']?(\d+)/i', $response, $id_match)) {
        $profile_result['user_id'] = $id_match[1];
        $profile_result['profilePic'] = "https://graph.facebook.com/{$id_match[1]}/picture?type=large";
    } elseif (preg_match('/profile_id["\']?\s*[:=]\s*["\']?(\d+)/i', $response, $id_match)) {
        $profile_result['user_id'] = $id_match[1];
        $profile_result['profilePic'] = "https://graph.facebook.com/{$id_match[1]}/picture?type=large";
    }
    
    // Alternative: extract from og:image
    if (empty($profile_result['profilePic']) && preg_match('/<meta\s+property=["\']og:image["\']\s+content=["\'](https?:\/\/[^"\']+)["\']/i', $response, $og_match)) {
        $profile_result['profilePic'] = html_entity_decode($og_match[1], ENT_QUOTES, 'UTF-8');
    }
    
    if (!empty($profile_result['profilePic']) || !empty($profile_result['name'])) {
        $profile_result['method'] = 'public_scrape';
        return $profile_result;
    }
    
    return false;
}

// === METHOD 3: GRAVATAR FALLBACK ===
/**
 * Use email hash to get Gravatar profile picture
 * Works for users who have Gravatar accounts
 */
function get_gravatar($email) {
    $hash = md5(strtolower(trim($email)));
    $gravatar_url = "https://www.gravatar.com/avatar/{$hash}?s=200&d=404";
    
    // Check if gravatar exists
    $result = http_request($gravatar_url, ['timeout' => 3]);
    
    if ($result['http_code'] === 200) {
        return [
            'profilePic' => "https://www.gravatar.com/avatar/{$hash}?s=400&d=mp",
            'name' => explode('@', $email)[0],
            'method' => 'gravatar'
        ];
    }
    
    return false;
}

// === METHOD 4: STORED COOKIES FALLBACK (LAST RESORT) ===
function try_stored_cookies_lookup($email) {
    // Only try if cookie_config exists
    if (!file_exists(__DIR__ . '/cookie_config.php')) {
        return false;
    }
    
    require_once __DIR__ . '/cookie_config.php';
    
    if (!function_exists('get_valid_cookies')) {
        return false;
    }
    
    $cookie_data = get_valid_cookies();
    if ($cookie_data === false) {
        return false;
    }
    
    $cookie_string = $cookie_data['cookie_string'];
    
    // Search using cookies
    $search_url = 'https://mbasic.facebook.com/search/people/?q=' . urlencode($email);
    
    $result = http_request($search_url, [
        'cookie' => $cookie_string,
        'timeout' => 10
    ]);
    
    $response = $result['body'];
    
    if ($result['http_code'] !== 200 || empty($response)) {
        return false;
    }
    
    $profile_result = [];
    
    // Parse first result
    if (preg_match('/profile\.php\?id=(\d+)/i', $response, $id_match)) {
        $profile_result['user_id'] = $id_match[1];
        $profile_result['profilePic'] = "https://graph.facebook.com/{$id_match[1]}/picture?type=large";
    }
    
    if (preg_match('/<a[^>]+href=["\']\/profile\.php\?id=\d+["\'][^>]*>([^<]+)<\/a>/i', $response, $name_match)) {
        $profile_result['name'] = trim(html_entity_decode($name_match[1], ENT_QUOTES, 'UTF-8'));
    }
    
    if (!empty($profile_result['profilePic'])) {
        $profile_result['method'] = 'stored_cookies';
        return $profile_result;
    }
    
    return false;
}

// === GENERATE EMAIL-BASED AVATAR ===
function generate_email_avatar($email) {
    // Use a service that generates avatars from text/email
    $name = explode('@', $email)[0];
    $initials = strtoupper(substr($name, 0, 2));
    
    // UI Avatars service - generates avatar from initials
    $avatar_url = "https://ui-avatars.com/api/?name=" . urlencode($name) . "&size=200&background=1877f2&color=ffffff&bold=true";
    
    return [
        'profilePic' => $avatar_url,
        'name' => ucwords(str_replace(['.', '_', '-'], ' ', $name)),
        'method' => 'generated'
    ];
}

// === MAIN LOGIC ===
$input_info = detect_input_type($input);
$result = false;

// Strategy based on input type
switch ($input_info['type']) {
    case 'fb_username':
    case 'fb_id':
        // Best case: we have direct Facebook identifier
        // Try Graph API first (NO AUTH NEEDED!)
        $result = get_profile_from_graph_api($input_info['value']);
        
        if (!$result) {
            // Try scraping public profile
            $result = scrape_public_profile($input_info['value']);
        }
        break;
        
    case 'email':
        // Email input - try multiple methods
        
        // 1. Try Gravatar first (no FB needed)
        $result = get_gravatar($input_info['value']);
        
        // 2. If no Gravatar, try stored cookies as fallback
        if (!$result) {
            $result = try_stored_cookies_lookup($input_info['value']);
        }
        break;
        
    case 'phone':
        // Phone number - only stored cookies can help
        $result = try_stored_cookies_lookup($input_info['value']);
        break;
        
    default:
        // Unknown input type - try as username
        $result = get_profile_from_graph_api($input_info['value']);
        if (!$result) {
            $result = scrape_public_profile($input_info['value']);
        }
        break;
}

// === FALLBACK: Generate from email/input ===
if (!$result) {
    if ($input_info['type'] === 'email') {
        $result = generate_email_avatar($input_info['value']);
    } else {
        // Generic fallback
        $result = [
            'profilePic' => "https://ui-avatars.com/api/?name=" . urlencode($input_info['value']) . "&size=200&background=1877f2&color=ffffff",
            'name' => ucfirst($input_info['value']),
            'method' => 'fallback'
        ];
    }
}

// === OUTPUT ===
echo json_encode([
    'success' => !empty($result['profilePic']),
    'profilePic' => $result['profilePic'] ?? '',
    'name' => $result['name'] ?? '',
    'method' => $result['method'] ?? 'none',
    'inputType' => $input_info['type']
]);

