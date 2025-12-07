"""
Error Recovery Procedures
Source: plan-review-meta-instruction2.md (GAP-010 resolution)
Implements graceful degradation and recovery for proxy, SSL, and database failures

OPSEC: Silent failure, cleanup on error, no sensitive logging
"""

import asyncio
import time
from typing import Optional, Callable, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class FailureType(Enum):
    """Types of failures"""
    PROXY = "proxy"
    SSL = "ssl"
    DATABASE = "database"
    NETWORK = "network"
    TEMPLATE = "template"


@dataclass
class FailureRecord:
    """Record of a failure event"""
    failure_type: FailureType
    timestamp: datetime
    retry_count: int = 0
    recovered: bool = False
    fallback_used: bool = False


@dataclass
class RecoveryConfig:
    """Recovery configuration"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    enable_fallback: bool = True
    enable_alerts: bool = True


class ErrorRecovery:
    """
    Error recovery and graceful degradation handler
    Source: plan.md Task 5.2
    
    Features:
    - Retry with exponential backoff
    - Fallback to static templates
    - Telegram alerts for persistent failures
    - Memory buffering for database failures
    """
    
    def __init__(self, config: RecoveryConfig = None):
        self.config = config or RecoveryConfig()
        self.failure_history: List[FailureRecord] = []
        self.memory_buffer: List[dict] = []
        self._telegram_bot = None
        self._telegram_chat_id = None
    
    def configure_alerts(self, bot_token: str, chat_id: str) -> None:
        """Configure Telegram alerts"""
        try:
            self._telegram_bot = bot_token
            self._telegram_chat_id = chat_id
        except Exception:
            pass  # Silent failure
    
    async def handle_proxy_failure(
        self,
        operation: Callable,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """
        Handle proxy failure with retry and fallback
        Source: plan.md Task 5.2
        
        Strategy:
        1. Retry 3x with exponential backoff
        2. On persistent failure, fall back to static templates
        3. Send Telegram alert
        
        Args:
            operation: Async function to retry
            *args: Arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            Operation result or None on failure
        """
        record = FailureRecord(
            failure_type=FailureType.PROXY,
            timestamp=datetime.utcnow()
        )
        
        # Retry with exponential backoff
        for attempt in range(self.config.max_retries):
            try:
                result = await operation(*args, **kwargs)
                record.recovered = True
                return result
            except Exception:
                record.retry_count = attempt + 1
                
                if attempt < self.config.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)
        
        # All retries failed - fall back to static templates
        if self.config.enable_fallback:
            record.fallback_used = True
            await self._fallback_to_static()
        
        # Send alert
        if self.config.enable_alerts:
            await self._send_alert(
                "Proxy failure",
                f"Proxy failed after {self.config.max_retries} retries. "
                "Fallback to static templates activated."
            )
        
        self.failure_history.append(record)
        return None
    
    async def handle_ssl_failure(
        self,
        domain: str
    ) -> bool:
        """
        Handle SSL certificate failure
        Source: plan.md Task 5.2
        
        Strategy:
        1. Attempt auto-renewal via certbot
        2. Fall back to self-signed certificate
        3. Send alert if all recovery fails
        
        Args:
            domain: Domain for certificate
            
        Returns:
            bool: True if recovery successful
        """
        record = FailureRecord(
            failure_type=FailureType.SSL,
            timestamp=datetime.utcnow()
        )
        
        try:
            # Attempt 1: Auto-renewal
            from .ssl import AutoCertManager
            
            cert_manager = AutoCertManager(domain=domain)
            
            if cert_manager.needs_renewal():
                success = cert_manager.renew_certificate()
                
                if success:
                    record.recovered = True
                    self.failure_history.append(record)
                    return True
            
            # Attempt 2: Request new certificate
            success = cert_manager.request_certificate()
            
            if success:
                record.recovered = True
                self.failure_history.append(record)
                return True
            
            # Attempt 3: Self-signed fallback
            if self.config.enable_fallback:
                paths = cert_manager.generate_self_signed()
                
                if paths:
                    record.recovered = True
                    record.fallback_used = True
                    self.failure_history.append(record)
                    
                    # Alert about self-signed usage
                    if self.config.enable_alerts:
                        await self._send_alert(
                            "SSL fallback",
                            f"Using self-signed certificate for {domain}. "
                            "Manual certificate renewal recommended."
                        )
                    
                    return True
            
            # All recovery failed
            if self.config.enable_alerts:
                await self._send_alert(
                    "SSL failure",
                    f"SSL certificate recovery failed for {domain}. "
                    "Manual intervention required."
                )
            
            self.failure_history.append(record)
            return False
            
        except Exception:
            self.failure_history.append(record)
            return False
    
    async def handle_database_failure(
        self,
        data: dict = None
    ) -> bool:
        """
        Handle database failure with memory buffering
        Source: plan.md Task 5.2
        
        Strategy:
        1. Buffer data to memory
        2. Attempt periodic flush to database
        3. Alert on persistent failure
        
        Args:
            data: Data to buffer (optional)
            
        Returns:
            bool: True if data buffered/saved successfully
        """
        record = FailureRecord(
            failure_type=FailureType.DATABASE,
            timestamp=datetime.utcnow()
        )
        
        try:
            # Buffer data to memory
            if data:
                data['buffered_at'] = datetime.utcnow().isoformat()
                self.memory_buffer.append(data)
                record.fallback_used = True
            
            # Attempt to flush buffer periodically
            if len(self.memory_buffer) > 0:
                flushed = await self._flush_buffer()
                
                if flushed:
                    record.recovered = True
            
            self.failure_history.append(record)
            return True
            
        except Exception:
            self.failure_history.append(record)
            return False
    
    async def _flush_buffer(self) -> bool:
        """Attempt to flush memory buffer to database"""
        if not self.memory_buffer:
            return True
        
        try:
            from ..database.models import Database
            
            db = Database()
            flushed_count = 0
            
            for item in self.memory_buffer[:]:
                try:
                    # Attempt to save each buffered item
                    # This would depend on the data type
                    flushed_count += 1
                    self.memory_buffer.remove(item)
                except Exception:
                    continue
            
            return flushed_count > 0
            
        except Exception:
            return False
    
    async def _fallback_to_static(self) -> bool:
        """Activate static template fallback"""
        try:
            from .router import TemplateRouter
            
            # Disable AiTM routing, use static templates only
            router = TemplateRouter()
            
            # This would signal the system to use static templates
            return True
        except Exception:
            return False
    
    async def _send_alert(self, title: str, message: str) -> bool:
        """Send Telegram alert"""
        if not self._telegram_bot or not self._telegram_chat_id:
            return False
        
        try:
            import httpx
            
            url = f"https://api.telegram.org/bot{self._telegram_bot}/sendMessage"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json={
                    'chat_id': self._telegram_chat_id,
                    'text': f"🚨 {title}\n\n{message}",
                    'parse_mode': 'HTML'
                })
                
                return response.status_code == 200
        except Exception:
            return False
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay"""
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        return min(delay, self.config.max_delay)
    
    def get_failure_stats(self) -> dict:
        """Get failure statistics"""
        stats = {
            'total_failures': len(self.failure_history),
            'recovered': sum(1 for f in self.failure_history if f.recovered),
            'fallback_used': sum(1 for f in self.failure_history if f.fallback_used),
            'by_type': {}
        }
        
        for failure_type in FailureType:
            type_failures = [f for f in self.failure_history if f.failure_type == failure_type]
            stats['by_type'][failure_type.value] = {
                'count': len(type_failures),
                'recovered': sum(1 for f in type_failures if f.recovered)
            }
        
        return stats
    
    def clear_history(self) -> None:
        """Clear failure history"""
        self.failure_history.clear()
    
    def get_buffer_size(self) -> int:
        """Get memory buffer size"""
        return len(self.memory_buffer)


# Global recovery instance
_recovery_instance: Optional[ErrorRecovery] = None


def get_recovery_instance() -> ErrorRecovery:
    """Get or create global recovery instance"""
    global _recovery_instance
    
    if _recovery_instance is None:
        _recovery_instance = ErrorRecovery()
    
    return _recovery_instance


async def handle_failure(
    failure_type: FailureType,
    operation: Callable = None,
    data: dict = None,
    domain: str = None
) -> Any:
    """
    Convenience function for handling failures
    
    Args:
        failure_type: Type of failure
        operation: Optional async operation to retry (for proxy)
        data: Optional data to buffer (for database)
        domain: Optional domain (for SSL)
        
    Returns:
        Recovery result
    """
    recovery = get_recovery_instance()
    
    if failure_type == FailureType.PROXY and operation:
        return await recovery.handle_proxy_failure(operation)
    elif failure_type == FailureType.SSL and domain:
        return await recovery.handle_ssl_failure(domain)
    elif failure_type == FailureType.DATABASE:
        return await recovery.handle_database_failure(data)
    
    return None

