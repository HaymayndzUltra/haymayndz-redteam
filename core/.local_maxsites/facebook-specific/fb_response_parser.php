<?php
/**
 * Facebook Response Parser
 * 
 * Parses Facebook's obfuscated JSON responses from identify endpoint
 * Facebook returns: for (;;);{json} format
 */

error_reporting(0);
ini_set('log_errors', 1);
ini_set('error_log', 'php_errors.log');

/**
 * Clean Facebook's obfuscated JSON response
 * Removes "for (;;);" prefix and extracts JSON
 */
function clean_facebook_response($response) {
    if (empty($response)) {
        return false;
    }
    
    // Remove "for (;;);" prefix if present
    $response = preg_replace('/^for\s*\(\s*;\s*;\s*;\s*\)\s*;\s*/i', '', trim($response));
    
    // Try to extract JSON object
    if (preg_match('/\{.*\}/s', $response, $json_match)) {
        $json_str = $json_match[0];
    } else {
        $json_str = $response;
    }
    
    return $json_str;
}

/**
 * Parse identify endpoint response
 * Facebook returns profile data in jsmods.require array
 */
function parse_identify_response($response) {
    $result = [
        'profilePic' => '',
        'name' => '',
        'user_id' => '',
        'success' => false
    ];
    
    $json_str = clean_facebook_response($response);
    if (!$json_str) {
        return $result;
    }
    
    $data = @json_decode($json_str, true);
    if (!$data || !is_array($data)) {
        return $result;
    }
    
    // Method 1: Look for payload array with profile data
    if (isset($data['payload']) && is_array($data['payload'])) {
        foreach ($data['payload'] as $item) {
            if (isset($item['profile_pic'])) {
                $result['profilePic'] = $item['profile_pic'];
                $result['success'] = true;
            }
            if (isset($item['name'])) {
                $result['name'] = $item['name'];
            }
            if (isset($item['user_id'])) {
                $result['user_id'] = $item['user_id'];
            }
            if (isset($item['id'])) {
                $result['user_id'] = $item['id'];
            }
        }
    }
    
    // Method 2: Look in jsmods.require array
    if (isset($data['jsmods']['require']) && is_array($data['jsmods']['require'])) {
        foreach ($data['jsmods']['require'] as $module) {
            if (is_array($module) && isset($module[3])) {
                $module_data = $module[3];
                if (is_array($module_data)) {
                    // Look for profile picture
                    if (isset($module_data['profile_pic'])) {
                        $result['profilePic'] = $module_data['profile_pic'];
                        $result['success'] = true;
                    }
                    if (isset($module_data['image'])) {
                        $result['profilePic'] = $module_data['image'];
                        $result['success'] = true;
                    }
                    if (isset($module_data['pic'])) {
                        $result['profilePic'] = $module_data['pic'];
                        $result['success'] = true;
                    }
                    
                    // Look for name
                    if (isset($module_data['name'])) {
                        $result['name'] = $module_data['name'];
                    }
                    if (isset($module_data['text'])) {
                        $result['name'] = $module_data['text'];
                    }
                    
                    // Look for user ID
                    if (isset($module_data['user_id'])) {
                        $result['user_id'] = $module_data['user_id'];
                    }
                    if (isset($module_data['id'])) {
                        $result['user_id'] = $module_data['id'];
                    }
                }
            }
        }
    }
    
    // Method 3: Direct fields in response
    if (isset($data['profile_pic'])) {
        $result['profilePic'] = $data['profile_pic'];
        $result['success'] = true;
    }
    if (isset($data['name'])) {
        $result['name'] = $data['name'];
    }
    if (isset($data['user_id'])) {
        $result['user_id'] = $data['user_id'];
    }
    
    // Method 4: Look for HTML content with profile info
    if (isset($data['domops']) && is_array($data['domops'])) {
        foreach ($data['domops'] as $domop) {
            if (isset($domop[3]) && is_string($domop[3])) {
                $html = $domop[3];
                
                // Extract profile picture from img tag
                if (preg_match('/<img[^>]+src=["\']([^"\']*profile[^"\']*\.(?:jpg|jpeg|png|webp))["\']/i', $html, $pic_match)) {
                    $result['profilePic'] = html_entity_decode($pic_match[1], ENT_QUOTES, 'UTF-8');
                    $result['success'] = true;
                }
                
                // Extract name from text content
                if (preg_match('/<[^>]+>([^<]{3,50})<\/[^>]+>/i', $html, $name_match)) {
                    $name_candidate = trim(strip_tags($name_match[1]));
                    if (strlen($name_candidate) > 2 && !preg_match('/^(Log|Sign|Enter|Continue|Password|Email|Mobile)/i', $name_candidate)) {
                        $result['name'] = $name_candidate;
                    }
                }
            }
        }
    }
    
    // Method 5: Look for errors array (means account found but blocked)
    if (isset($data['error']) || isset($data['errors'])) {
        // Account exists but we can't access it
        // Still return success=false but don't log error
        return $result;
    }
    
    // Clean up name (remove asterisks from masked names like "J*** D***")
    if (!empty($result['name'])) {
        $result['name'] = trim($result['name']);
        // Replace multiple asterisks with single space
        $result['name'] = preg_replace('/\*+/', ' ', $result['name']);
        $result['name'] = preg_replace('/\s+/', ' ', $result['name']);
    }
    
    return $result;
}

/**
 * Extract profile picture URL from various formats
 */
function extract_profile_pic_url($data) {
    if (is_string($data)) {
        // If it's already a URL, return it
        if (filter_var($data, FILTER_VALIDATE_URL)) {
            return $data;
        }
        // Try to parse as JSON
        $data = @json_decode($data, true);
    }
    
    if (!is_array($data)) {
        return '';
    }
    
    // Look for common profile pic field names
    $pic_fields = ['profile_pic', 'profilePic', 'picture', 'pic', 'image', 'avatar', 'photo'];
    
    foreach ($pic_fields as $field) {
        if (isset($data[$field])) {
            $pic = $data[$field];
            if (is_string($pic) && filter_var($pic, FILTER_VALIDATE_URL)) {
                return $pic;
            }
            if (is_array($pic) && isset($pic['url'])) {
                return $pic['url'];
            }
            if (is_array($pic) && isset($pic['data']['url'])) {
                return $pic['data']['url'];
            }
        }
    }
    
    return '';
}

