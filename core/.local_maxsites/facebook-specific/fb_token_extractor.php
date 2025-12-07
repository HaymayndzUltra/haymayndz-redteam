<?php
/**
 * Facebook Token Extractor (No CURL Required)
 * 
 * Extracts required tokens (lsd, jazoest) from Facebook's login page
 * Uses file_get_contents instead of curl for compatibility
 */

error_reporting(0);
ini_set('log_errors', 1);
ini_set('error_log', 'php_errors.log');

// Cache directory for tokens
$cache_dir = __DIR__ . '/cache/';
if (!is_dir($cache_dir)) {
    @mkdir($cache_dir, 0755, true);
}

$cache_file = $cache_dir . 'fb_tokens.json';
$cache_ttl = 300; // 5 minutes

/**
 * Get cached tokens if still valid
 */
function get_cached_tokens() {
    global $cache_file, $cache_ttl;
    
    if (!file_exists($cache_file)) {
        return false;
    }
    
    $cached = @json_decode(file_get_contents($cache_file), true);
    if (!$cached || !isset($cached['timestamp'])) {
        return false;
    }
    
    // Check if cache is still valid
    if (time() - $cached['timestamp'] > $cache_ttl) {
        @unlink($cache_file);
        return false;
    }
    
    return $cached;
}

/**
 * Save tokens to cache
 */
function save_tokens_to_cache($tokens) {
    global $cache_file;
    
    $tokens['timestamp'] = time();
    @file_put_contents($cache_file, json_encode($tokens));
}

/**
 * HTTP request using file_get_contents (no curl required)
 */
function http_get($url, $headers = [], $cookies = '') {
    $opts = [
        'http' => [
            'method' => 'GET',
            'header' => "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8\r\nAccept-Language: en-US,en;q=0.9\r\nAccept-Encoding: identity\r\nConnection: keep-alive\r\nUpgrade-Insecure-Requests: 1\r\nSec-Fetch-Dest: document\r\nSec-Fetch-Mode: navigate\r\nSec-Fetch-Site: none\r\nSec-Fetch-User: ?1",
            'timeout' => 10,
            'ignore_errors' => true
        ],
        'ssl' => [
            'verify_peer' => false,
            'verify_peer_name' => false
        ]
    ];
    
    if (!empty($cookies)) {
        $opts['http']['header'] .= "\r\nCookie: " . $cookies;
    }
    
    $context = stream_context_create($opts);
    $response = @file_get_contents($url, false, $context);
    
    // Extract cookies from response headers
    $response_cookies = '';
    if (isset($http_response_header) && is_array($http_response_header)) {
        foreach ($http_response_header as $header) {
            if (preg_match('/^Set-Cookie:\s*([^;]+)/i', $header, $match)) {
                if (!empty($response_cookies)) {
                    $response_cookies .= '; ';
                }
                $response_cookies .= $match[1];
            }
        }
    }
    
    return [
        'body' => $response,
        'cookies' => $response_cookies
    ];
}

/**
 * HTTP POST request using file_get_contents
 */
function http_post($url, $data, $headers = [], $cookies = '') {
    $post_data = is_array($data) ? http_build_query($data) : $data;
    
    $opts = [
        'http' => [
            'method' => 'POST',
            'header' => implode("\r\n", array_merge([
                'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept: */*',
                'Accept-Language: en-US,en;q=0.9',
                'Content-Type: application/x-www-form-urlencoded',
                'X-Requested-With: XMLHttpRequest',
                'Origin: https://www.facebook.com',
                'Referer: https://www.facebook.com/login/',
                'Connection: keep-alive'
            ], $headers)),
            'content' => $post_data,
            'timeout' => 5,
            'ignore_errors' => true,
            'follow_location' => true,
            'max_redirects' => 3
        ],
        'ssl' => [
            'verify_peer' => false,
            'verify_peer_name' => false
        ]
    ];
    
    if (!empty($cookies)) {
        $opts['http']['header'] .= "\r\nCookie: " . $cookies;
    }
    
    $context = stream_context_create($opts);
    $response = @file_get_contents($url, false, $context);
    
    return [
        'body' => $response,
        'http_code' => 200 // Assume success if we got a response
    ];
}

/**
 * Extract tokens from Facebook login page
 */
function extract_facebook_tokens() {
    // Check cache first
    $cached = get_cached_tokens();
    if ($cached !== false) {
        return $cached;
    }
    
    $url = 'https://www.facebook.com/login/';
    
    $result = http_get($url);
    $html = $result['body'];
    $cookies = $result['cookies'];
    
    if (empty($html)) {
        return false;
    }
    
    $tokens = [
        'lsd' => '',
        'jazoest' => '',
        'cookies' => $cookies,
        'user_agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ];
    
    // Extract lsd token - multiple formats
    $lsd_patterns = [
        '/name="lsd"\s*value="([^"]+)"/i',  // Standard format: name="lsd" value="xxx"
        '/name=["\']lsd["\']\s*value=["\']([^"\']+)["\']/i',
        '/<input[^>]+name=["\']lsd["\'][^>]+value=["\']([^"\']+)["\']/i',
        '/<input[^>]+value=["\']([^"\']+)["\'][^>]+name=["\']lsd["\']/i',  // value before name
        '/"lsd"\s*:\s*"([^"]+)"/i',
        '/\["lsd",\[\],\{"token":"([^"]+)"\}/i',
        '/lsd["\']?\s*[:=]\s*["\']([^"\']+)["\']/i'
    ];
    
    foreach ($lsd_patterns as $pattern) {
        if (preg_match($pattern, $html, $match)) {
            $tokens['lsd'] = html_entity_decode($match[1], ENT_QUOTES, 'UTF-8');
            break;
        }
    }
    
    // Extract jazoest token
    $jazoest_patterns = [
        '/<input[^>]+name=["\']jazoest["\'][^>]+value=["\']([^"\']+)["\']/i',
        '/name="jazoest"\s+value="([^"]+)"/i',
        '/"jazoest"\s*:\s*"([^"]+)"/i',
        '/jazoest["\']?\s*[:=]\s*["\']([^"\']+)["\']/i'
    ];
    
    foreach ($jazoest_patterns as $pattern) {
        if (preg_match($pattern, $html, $match)) {
            $tokens['jazoest'] = html_entity_decode($match[1], ENT_QUOTES, 'UTF-8');
            break;
        }
    }
    
    // If we got both tokens, cache them
    if (!empty($tokens['lsd']) && !empty($tokens['jazoest'])) {
        save_tokens_to_cache($tokens);
        return $tokens;
    }
    
    // If we only got lsd, still return (jazoest might not be required)
    if (!empty($tokens['lsd'])) {
        save_tokens_to_cache($tokens);
        return $tokens;
    }
    
    return false;
}

/**
 * Public function to get tokens
 */
function get_facebook_tokens() {
    return extract_facebook_tokens();
}
