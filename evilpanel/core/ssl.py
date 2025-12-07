"""
SSL/TLS Certificate Automation
Source: plan-aligned-implementation-protocol.md Lines 301-406
OPSEC: All methods return gracefully on failure (no exceptions)
"""

import subprocess
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class CertificatePaths:
    """Certificate file paths"""
    cert: str
    key: str
    chain: str
    fullchain: str


class AutoCertManager:
    """
    Automatic SSL certificate management via Let's Encrypt
    Source: plan.md Section 6.1, Line 450 - Let's Encrypt (auto SSL)
    """
    
    LETSENCRYPT_PATH = '/etc/letsencrypt/live'
    
    def __init__(self, domain: str, email: str = ''):
        self.domain = domain
        self.email = email
        self._cert_path: Optional[CertificatePaths] = None
    
    def request_certificate(self, subdomains: list = None, wildcard: bool = False) -> bool:
        """
        Request SSL certificate from Let's Encrypt
        
        Args:
            subdomains: List of subdomains to include
            wildcard: Whether to request wildcard certificate
            
        Returns:
            bool: True if certificate obtained successfully
        """
        if not self.domain:
            return False
        
        try:
            # Build certbot command
            cmd = ['certbot', 'certonly', '--non-interactive', '--agree-tos']
            
            if self.email:
                cmd.extend(['--email', self.email])
            else:
                cmd.append('--register-unsafely-without-email')
            
            # Use DNS challenge for wildcard, HTTP for standard
            if wildcard:
                cmd.extend(['--preferred-challenges', 'dns'])
                cmd.extend(['-d', f'*.{self.domain}'])
                cmd.extend(['-d', self.domain])
            else:
                cmd.extend(['--preferred-challenges', 'http'])
                cmd.extend(['-d', self.domain])
                
                # Add subdomains
                if subdomains:
                    for sub in subdomains:
                        cmd.extend(['-d', f'{sub}.{self.domain}'])
            
            # Use standalone mode
            cmd.append('--standalone')
            
            # Run certbot
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300
            )
            
            return result.returncode == 0
            
        except Exception:
            return False  # Silent failure
    
    def get_certificate_paths(self) -> Optional[CertificatePaths]:
        """
        Get paths to certificate files
        
        Returns:
            CertificatePaths if certificate exists, None otherwise
        """
        if not self.domain:
            return None
        
        try:
            cert_dir = Path(self.LETSENCRYPT_PATH) / self.domain
            
            if not cert_dir.exists():
                return None
            
            cert_path = cert_dir / 'cert.pem'
            key_path = cert_dir / 'privkey.pem'
            chain_path = cert_dir / 'chain.pem'
            fullchain_path = cert_dir / 'fullchain.pem'
            
            # Verify files exist
            if not all(p.exists() for p in [cert_path, key_path, chain_path, fullchain_path]):
                return None
            
            self._cert_path = CertificatePaths(
                cert=str(cert_path),
                key=str(key_path),
                chain=str(chain_path),
                fullchain=str(fullchain_path)
            )
            
            return self._cert_path
            
        except Exception:
            return None
    
    def check_expiry(self) -> Optional[int]:
        """
        Check certificate expiration
        
        Returns:
            Number of days until expiration, None if unable to check
        """
        try:
            paths = self.get_certificate_paths()
            if not paths:
                return None
            
            # Use openssl to check expiry
            result = subprocess.run(
                ['openssl', 'x509', '-enddate', '-noout', '-in', paths.cert],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
            
            # Parse output: notAfter=Dec 31 23:59:59 2025 GMT
            output = result.stdout.strip()
            date_str = output.split('=')[1] if '=' in output else ''
            
            if not date_str:
                return None
            
            # Parse date
            expiry_date = datetime.strptime(date_str, '%b %d %H:%M:%S %Y %Z')
            days_remaining = (expiry_date - datetime.utcnow()).days
            
            return days_remaining
            
        except Exception:
            return None
    
    def needs_renewal(self, threshold_days: int = 30) -> bool:
        """
        Check if certificate needs renewal
        
        Args:
            threshold_days: Renew if less than this many days remaining
            
        Returns:
            True if renewal needed
        """
        days = self.check_expiry()
        
        if days is None:
            return True  # No certificate or error - needs renewal
        
        return days < threshold_days
    
    def renew_certificate(self) -> bool:
        """
        Renew certificate if needed
        
        Returns:
            bool: True if renewal successful or not needed
        """
        try:
            result = subprocess.run(
                ['certbot', 'renew', '--non-interactive'],
                capture_output=True,
                timeout=300
            )
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    def setup_auto_renewal(self) -> bool:
        """
        Setup automatic certificate renewal via cron
        
        Returns:
            bool: True if cron job created successfully
        """
        try:
            cron_entry = '0 0,12 * * * certbot renew --quiet --post-hook "systemctl reload nginx"'
            
            # Check if cron entry already exists
            result = subprocess.run(
                ['crontab', '-l'],
                capture_output=True,
                text=True
            )
            
            current_cron = result.stdout if result.returncode == 0 else ''
            
            if 'certbot renew' in current_cron:
                return True  # Already configured
            
            # Add cron entry
            new_cron = current_cron.strip() + '\n' + cron_entry + '\n'
            
            process = subprocess.Popen(
                ['crontab', '-'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            process.communicate(input=new_cron.encode())
            
            return process.returncode == 0
            
        except Exception:
            return False
    
    def generate_self_signed(self, output_dir: str = '/tmp') -> Optional[CertificatePaths]:
        """
        Generate self-signed certificate as fallback
        
        Args:
            output_dir: Directory to store certificate files
            
        Returns:
            CertificatePaths if generated successfully
        """
        if not self.domain:
            return None
        
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            key_path = output_path / f'{self.domain}.key'
            cert_path = output_path / f'{self.domain}.crt'
            
            # Generate self-signed certificate
            result = subprocess.run([
                'openssl', 'req', '-x509', '-nodes',
                '-days', '365',
                '-newkey', 'rsa:2048',
                '-keyout', str(key_path),
                '-out', str(cert_path),
                '-subj', f'/CN={self.domain}'
            ], capture_output=True, timeout=60)
            
            if result.returncode != 0:
                return None
            
            return CertificatePaths(
                cert=str(cert_path),
                key=str(key_path),
                chain=str(cert_path),  # Self-signed has no chain
                fullchain=str(cert_path)
            )
            
        except Exception:
            return None
    
    def revoke_certificate(self) -> bool:
        """
        Revoke current certificate
        
        Returns:
            bool: True if revocation successful
        """
        try:
            paths = self.get_certificate_paths()
            if not paths:
                return False
            
            result = subprocess.run(
                ['certbot', 'revoke', '--cert-path', paths.cert, '--non-interactive'],
                capture_output=True,
                timeout=120
            )
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    def delete_certificate(self) -> bool:
        """
        Delete certificate files
        
        Returns:
            bool: True if deletion successful
        """
        try:
            result = subprocess.run(
                ['certbot', 'delete', '--cert-name', self.domain, '--non-interactive'],
                capture_output=True,
                timeout=60
            )
            
            return result.returncode == 0
            
        except Exception:
            return False

