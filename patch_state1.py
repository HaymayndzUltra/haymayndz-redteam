#!/usr/bin/env python3
import re

# Read current file
with open("/opt/landing/index.php", "r") as f:
    content = f.read()

# Read CSS to add
with open("/tmp/fb_feed_css.txt", "r") as f:
    new_css = f.read()

# Read new HTML
with open("/tmp/state1_html_new.txt", "r") as f:
    new_html = f.read()

# 1. Add CSS before closing </style>
content = content.replace("    </style>", new_css + "\n    </style>")

# 2. Replace State 1 HTML (the main.state-preview section)
old_html_pattern = r'(\s*)<main class="state state-preview is-active".*?</main>'
content = re.sub(old_html_pattern, "\n" + new_html, content, flags=re.DOTALL)

# 3. Also update the state-preview CSS to be simpler
old_preview_css = """.state-preview {
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
        }"""

new_preview_css = """.state-preview {
            position: relative;
            z-index: 3;
            background: #fff;
            overflow-y: auto;
            min-height: 100vh;
        }"""

content = content.replace(old_preview_css, new_preview_css)

# Write modified file
with open("/opt/landing/index.php", "w") as f:
    f.write(content)

print("Done! State 1 design patched successfully.")


