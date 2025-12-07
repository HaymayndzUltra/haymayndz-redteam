#!/usr/bin/env python3
"""
Pattern Encoder Utility for EvilPanel Bot Detection
Generates obfuscated pattern data

Usage:
    python3 pattern_encoder.py

Output the encoded strings to paste into mitmproxy_addon.py
"""
import base64
import zlib

# ==================== PATTERN DEFINITIONS ====================

BOT_PATTERNS = """googlebot
bingbot
slurp
duckduckbot
yandexbot
baiduspider
sogou
exabot
ia_archiver
facebookexternalhit
facebookcatalog
twitterbot
linkedinbot
pinterest
whatsapp
telegrambot
slackbot
discordbot
redditbot
nessus
nikto
sqlmap
nmap
masscan
zmap
censys
shodan
zgrab
qualys
tenable
burpsuite
owasp
acunetix
nuclei
headless
phantomjs
selenium
puppeteer
playwright
webdriver
chromedriver
geckodriver
bot
spider
crawler
scraper
curl
wget
python-requests
python-urllib
go-http-client
java/
libwww
httpie
postman
insomnia
axios
node-fetch
request/
ahrefsbot
semrushbot
petalbot
mj12bot
dotbot
rogerbot
blexbot
dataforseo"""

VM_PATTERNS = """llvmpipe
swiftshader
virtualbox
vmware
parallels
qemu
xen
hyper-v
bochs
google swiftshader"""

# ==================== ENCODING FUNCTIONS ====================

def encode_patterns(data: str) -> str:
    """Encode: zlib compress -> base64 encode"""
    compressed = zlib.compress(data.encode('utf-8'), level=9)
    encoded = base64.b64encode(compressed).decode('utf-8')
    return encoded

def decode_patterns(encoded: str) -> list:
    """Decode: base64 decode -> zlib decompress -> split lines"""
    decoded = base64.b64decode(encoded)
    decompressed = zlib.decompress(decoded)
    return [x.strip() for x in decompressed.decode('utf-8').split('\n') if x.strip()]

# ==================== MAIN ====================

if __name__ == "__main__":
    print("=" * 70)
    print("EVILPANEL PATTERN ENCODER - OBFUSCATED BOT DETECTION")
    print("=" * 70)
    
    # Encode bot patterns
    bot_encoded = encode_patterns(BOT_PATTERNS)
    print("\n[BOT PATTERNS - _VD1]")
    print(f'_VD1 = ("{bot_encoded}")')
    
    # Encode VM patterns  
    vm_encoded = encode_patterns(VM_PATTERNS)
    print("\n[VM PATTERNS - _VD2]")
    print(f'_VD2 = ("{vm_encoded}")')
    
    # Verification
    print("\n[VERIFICATION]")
    bot_decoded = decode_patterns(bot_encoded)
    vm_decoded = decode_patterns(vm_encoded)
    
    print(f"Bot patterns count: {len(bot_decoded)}")
    print(f"VM patterns count: {len(vm_decoded)}")
    print(f"Bot patterns sample: {bot_decoded[:5]}")
    print(f"VM patterns sample: {vm_decoded[:3]}")
    
    # Test decode matches original
    original_bots = [x.strip() for x in BOT_PATTERNS.split('\n') if x.strip()]
    original_vms = [x.strip() for x in VM_PATTERNS.split('\n') if x.strip()]
    
    print(f"\nBot decode correct: {bot_decoded == original_bots}")
    print(f"VM decode correct: {vm_decoded == original_vms}")
    
    print("\n" + "=" * 70)
    print("COPY THE _VD1 AND _VD2 VALUES INTO mitmproxy_addon.py")
    print("=" * 70)
