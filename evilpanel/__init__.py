"""
EvilPanel AiTM Integration Module
Public API exports for external consumption
"""

from .core.proxy import EvilPanelProxy, ProxyConfig
from .core.phishlet import PhishletParser, Phishlet
from .core.session import SessionCapture, CapturedSession
from .core.ssl import AutoCertManager, CertificatePaths
from .core.router import TemplateRouter
from .core.recovery import ErrorRecovery
from .core.dataimpulse import DataImpulseIntegration

__all__ = [
    'EvilPanelProxy',
    'ProxyConfig',
    'PhishletParser',
    'Phishlet',
    'SessionCapture',
    'CapturedSession',
    'AutoCertManager',
    'CertificatePaths',
    'TemplateRouter',
    'ErrorRecovery',
    'DataImpulseIntegration',
]

__version__ = '1.0.0'

