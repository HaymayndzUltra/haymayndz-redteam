#!/usr/bin/env python3
"""Patch State 2: Update video, profile pic, username, and header"""

# Read current file
with open("/opt/landing/index.php", "r") as f:
    content = f.read()

# 1. Replace video URL (old → new)
old_video = "8455f5_03845574298047bab65cfd1c0e15e5ff"
new_video = "8455f5_ba2ce46ccd4f4dd6bc8a0cd16347bdd2"
content = content.replace(old_video, new_video)

# 2. Replace profile pic URL (old → new)  
old_profile = "8455f5_c082110886634d768b1c7a9f956c3b1b~mv2.jpg"
new_profile = "8455f5_6a7ec556f87d4f8bb2961ddcfb4122e7~mv2.jpg"
content = content.replace(old_profile, new_profile)

# 3. Replace username (Balita → Kabayan News)
content = content.replace('<span class="username">Balita</span>', '<span class="username">Kabayan News</span>')

# 4. Replace immersive-header HTML (old Instagram style → Facebook style)
old_header = '''<div class="immersive-header">
                    <span>Log in</span>
                    <span class="pill">Open app</span>
                </div>'''

new_header = '''<!-- Facebook Header for State 2 -->
            <div class="immersive-header">
                <div class="immersive-fb-logo" aria-label="Facebook Logo">
                    <span class="immersive-fb-logo-text">facebook</span>
                </div>
                <div class="immersive-header-right">
                    <a href="#" class="immersive-open-app">Open app</a>
                    <button class="immersive-login-btn" id="immersiveLoginBtn">Log in</button>
                </div>
            </div>'''

content = content.replace(old_header, new_header)

# 5. Add State 2 header CSS (before closing </style>)
state2_css = '''
        /* ===== STATE 2: Facebook Header Overlay ===== */
        .immersive-header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            z-index: 100;
            min-height: 56px;
        }

        .immersive-fb-logo {
            display: flex;
            align-items: center;
        }

        .immersive-fb-logo-text {
            font-size: 28px;
            font-weight: 700;
            color: #fff;
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            letter-spacing: -1px;
        }

        .immersive-header-right {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .immersive-open-app {
            color: #fff;
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
            padding: 8px 12px;
        }

        .immersive-login-btn {
            background: #1877f2;
            color: #fff;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
        }

        .state-immersive video {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            object-fit: cover;
            z-index: 1;
        }

        .state-immersive .immersive-overlay {
            z-index: 5;
        }
'''

# Add CSS before the closing </style> tag
content = content.replace("    </style>", state2_css + "\n    </style>")

# Write modified file
with open("/opt/landing/index.php", "w") as f:
    f.write(content)

print("Done! State 2 patched:")
print("- Video URL updated")
print("- Profile pic updated")
print("- Username: Balita → Kabayan News")
print("- Immersive header: Facebook style")


