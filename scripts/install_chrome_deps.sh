#!/bin/bash
# Chrome Dependencies Installation Script for WSL2
# This script installs Chrome and required libraries for Selenium WebDriver

set -e

echo "========================================================================"
echo "Chrome/Chromium Installation for MaxPhisher Impersonator"
echo "========================================================================"
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "[INFO] This script needs sudo privileges."
    echo "[INFO] You will be prompted for your password."
    echo ""
fi

# Update package list
echo "[1/4] Updating package list..."
sudo apt update -qq

# Install NSS libraries and dependencies
echo "[2/4] Installing required libraries (NSS, ATK, CUPS, etc.)..."
sudo apt install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libxshmfence1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libdbus-1-3 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libpango-1.0-0 \
    libcairo2 \
    wget

# Download and install Chrome
echo "[3/4] Downloading and installing Google Chrome..."
cd /tmp
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb || sudo apt --fix-broken install -y
rm -f google-chrome-stable_current_amd64.deb

# Verify installation
echo "[4/4] Verifying installation..."
if command -v google-chrome &> /dev/null; then
    CHROME_VERSION=$(google-chrome --version)
    echo "✓ Chrome installed: $CHROME_VERSION"
else
    echo "✗ Chrome installation failed!"
    exit 1
fi

# Check ChromeDriver dependencies
echo ""
echo "Checking ChromeDriver dependencies..."
CHROMEDRIVER_PATH=$(find ~/.wdm/drivers/chromedriver -name "chromedriver" -type f 2>/dev/null | head -1)
if [ -n "$CHROMEDRIVER_PATH" ]; then
    MISSING_LIBS=$(ldd "$CHROMEDRIVER_PATH" 2>&1 | grep "not found" || true)
    if [ -z "$MISSING_LIBS" ]; then
        echo "✓ All ChromeDriver dependencies satisfied"
    else
        echo "⚠ Some libraries still missing:"
        echo "$MISSING_LIBS"
    fi
else
    echo "⚠ ChromeDriver not yet downloaded (will be downloaded on first run)"
fi

echo ""
echo "========================================================================"
echo "✅ Installation Complete!"
echo "========================================================================"
echo ""
echo "You can now run impersonator.py:"
echo "  python3 impersonator.py --profile /path/to/profile.json \\"
echo "    --proxy 'socks5://user:pass@host:port'"
echo ""
echo "========================================================================"

