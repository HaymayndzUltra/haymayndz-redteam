<?php
/**
 * Image Proxy for Facebook Profile Pictures
 * Fetches the image server-side and serves it to the browser
 */

// Disable error output
error_reporting(0);
ini_set('display_errors', 0);

// Get the URL to proxy
$url = isset($_GET['url']) ? $_GET['url'] : '';

if (empty($url)) {
    http_response_code(400);
    die('No URL provided');
}

// Decode the URL
$url = urldecode($url);

// Only allow Facebook URLs for security
if (strpos($url, 'facebook.com') === false && strpos($url, 'fbcdn.net') === false) {
    http_response_code(403);
    die('Invalid URL');
}

// Check cache first
$cache_dir = __DIR__ . '/data/image_cache';
if (!is_dir($cache_dir)) {
    mkdir($cache_dir, 0755, true);
}

$cache_key = md5($url);
$cache_file = $cache_dir . '/' . $cache_key . '.jpg';

// Cache for 1 hour
if (file_exists($cache_file) && (time() - filemtime($cache_file) < 3600)) {
    header('Content-Type: image/jpeg');
    header('Cache-Control: public, max-age=3600');
    readfile($cache_file);
    exit;
}

// Fetch the image with cURL
$ch = curl_init();
curl_setopt_array($ch, [
    CURLOPT_URL => $url,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_MAXREDIRS => 5,
    CURLOPT_TIMEOUT => 10,
    CURLOPT_USERAGENT => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    CURLOPT_HTTPHEADER => [
        'Accept: image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language: en-US,en;q=0.9',
    ],
    CURLOPT_SSL_VERIFYPEER => false,
]);

$image_data = curl_exec($ch);
$content_type = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

// Check if we got a valid image
if ($http_code !== 200 || empty($image_data)) {
    // Return a default placeholder image
    http_response_code(404);
    die('Image not found');
}

// Verify it's an image
if (strpos($content_type, 'image') === false) {
    http_response_code(400);
    die('Not an image');
}

// Save to cache
file_put_contents($cache_file, $image_data);

// Serve the image
header('Content-Type: ' . $content_type);
header('Cache-Control: public, max-age=3600');
header('Content-Length: ' . strlen($image_data));
echo $image_data;
