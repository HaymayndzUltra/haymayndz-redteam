<?php
// profile_lookup.php - Facebook profile lookup using existing cookies

error_reporting(0);
ini_set('log_errors', 1);
ini_set('error_log', 'php_errors.log');
date_default_timezone_set("Asia/Manila");

header('Content-Type: application/json');

// Include cookie configuration
require_once 'cookie_config.php';

// --- INPUT VALIDATION ---
$email = $_POST['email'] ?? $_GET['email'] ?? '';
$email = trim($email);

if (empty($email)) {
    echo json_encode([
        'success' => false,
        'error' => 'Email or phone number required'
    ]);
    exit();
}

// --- LOAD COOKIES ---
$cookie_data = get_valid_cookies();

if ($cookie_data === false) {
    // Silent failure - return generic response
    echo json_encode([
        'success' => false,
        'error' => 'Cookie service unavailable',
        'profilePic' => '',
        'name' => ''
    ]);
    exit();
}

$cookie_string = $cookie_data['cookie_string'];

// --- SEARCH FACEBOOK ---
function search_facebook_profile($email, $cookie_string) {
    // Use mbasic.facebook.com for easier parsing
    $search_url = 'https://mbasic.facebook.com/search/people/?q=' . urlencode($email);
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $search_url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS => 5,
        CURLOPT_COOKIE => $cookie_string,
        CURLOPT_USERAGENT => 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36',
        CURLOPT_HTTPHEADER => [
            'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language: en-US,en;q=0.5',
            'Accept-Encoding: gzip, deflate, br',
            'Connection: keep-alive',
            'Upgrade-Insecure-Requests: 1'
        ],
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => false,
        CURLOPT_TIMEOUT => 10,
        CURLOPT_CONNECTTIMEOUT => 5
    ]);
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($http_code !== 200 || empty($response)) {
        return false;
    }
    
    return $response;
}

// --- PARSE PROFILE DATA ---
function parse_profile_data($html) {
    $result = [
        'profilePic' => '',
        'name' => ''
    ];
    
    // Try to find profile picture
    // Pattern: <img src="..." alt="Profile picture" or similar
    if (preg_match('/<img[^>]+src=["\']([^"\']*profile[^"\']*\.(?:jpg|jpeg|png|webp))["\'][^>]*>/i', $html, $pic_matches)) {
        $result['profilePic'] = html_entity_decode($pic_matches[1], ENT_QUOTES, 'UTF-8');
    } elseif (preg_match('/<img[^>]+src=["\']([^"\']*\/[0-9]+\/[0-9]+\/[0-9]+\/[^"\']*)["\'][^>]*>/i', $html, $pic_matches)) {
        // Alternative pattern for FB profile pics
        $result['profilePic'] = html_entity_decode($pic_matches[1], ENT_QUOTES, 'UTF-8');
    }
    
    // Try to find name
    // Pattern: Look for anchor tags with profile links
    if (preg_match('/<a[^>]+href=["\']\/profile\.php\?id=([0-9]+)["\'][^>]*>([^<]+)<\/a>/i', $html, $name_matches)) {
        $result['name'] = trim(html_entity_decode($name_matches[2], ENT_QUOTES, 'UTF-8'));
    } elseif (preg_match('/<a[^>]+href=["\'][^"\']*\/[^"\']*["\'][^>]*>([^<]+)<\/a>/i', $html, $name_matches)) {
        // More generic pattern
        $name_candidate = trim(html_entity_decode($name_matches[1], ENT_QUOTES, 'UTF-8'));
        // Filter out common non-name text
        if (strlen($name_candidate) > 2 && 
            !preg_match('/^(See|View|More|All|Search|People|Photos|Videos|Posts)$/i', $name_candidate)) {
            $result['name'] = $name_candidate;
        }
    }
    
    // Alternative: Try Graph API style profile pic if we have user ID
    if (empty($result['profilePic']) && preg_match('/profile\.php\?id=([0-9]+)/i', $html, $id_matches)) {
        $user_id = $id_matches[1];
        $result['profilePic'] = 'https://graph.facebook.com/' . $user_id . '/picture?type=large';
    }
    
    return $result;
}

// --- EXECUTE LOOKUP ---
try {
    $html = search_facebook_profile($email, $cookie_string);
    
    if ($html === false) {
        // Silent failure - return empty result
        echo json_encode([
            'success' => false,
            'profilePic' => '',
            'name' => ''
        ]);
        exit();
    }
    
    $profile_data = parse_profile_data($html);
    
    // If we found at least profile pic or name, consider it success
    if (!empty($profile_data['profilePic']) || !empty($profile_data['name'])) {
        echo json_encode([
            'success' => true,
            'profilePic' => $profile_data['profilePic'],
            'name' => $profile_data['name']
        ]);
    } else {
        // No profile found
        echo json_encode([
            'success' => false,
            'profilePic' => '',
            'name' => ''
        ]);
    }
    
} catch (Exception $e) {
    // Silent failure
    echo json_encode([
        'success' => false,
        'profilePic' => '',
        'name' => ''
    ]);
}

