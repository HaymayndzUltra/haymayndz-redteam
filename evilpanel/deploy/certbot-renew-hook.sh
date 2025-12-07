#!/bin/bash
# ============================================================
# Certificate Renewal Hook for EvilPanel
# Regenerates combined.pem after Let's Encrypt renewal
# ============================================================
#
# Installation:
#   chmod +x certbot-renew-hook.sh
#   Add to /etc/letsencrypt/renewal-hooks/deploy/evilpanel.sh
#
# ============================================================

DOMAIN="frontnews.site"
CERT_DIR="/opt/evilpanel/certs"

# Recreate combined certificate for mitmproxy
cat /etc/letsencrypt/live/${DOMAIN}/fullchain.pem \
    /etc/letsencrypt/live/${DOMAIN}/privkey.pem \
    > ${CERT_DIR}/combined.pem

chmod 600 ${CERT_DIR}/combined.pem

# Restart mitmproxy to use new certificate
systemctl restart evilpanel

# Log the renewal
echo "$(date): Certificate renewed and EvilPanel restarted" >> /var/log/certbot-evilpanel.log
