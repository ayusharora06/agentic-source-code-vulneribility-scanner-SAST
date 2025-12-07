"""
Database models for vulnerability analysis tool
"""

import sqlite3
import json
import time
from typing import Any, Dict, List, Optional
import asyncio
import aiosqlite
from dataclasses import dataclass


@dataclass
class VulnerabilityRecord:
    """Database record for vulnerabilities"""
    id: Optional[int] = None
    vuln_id: str = ""
    session_id: str = ""
    vuln_type: str = ""
    severity: str = ""
    description: str = ""
    file_path: str = ""
    line_number: int = 0
    function_name: Optional[str] = None
    code_snippet: Optional[str] = None
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None
    fix_suggestion: Optional[str] = None
    tool_source: str = ""
    confidence: float = 1.0
    created_at: float = 0.0
    metadata: str = "{}"  # JSON string
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "vuln_id": self.vuln_id,
            "session_id": self.session_id,
            "vuln_type": self.vuln_type,
            "severity": self.severity,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "function_name": self.function_name,
            "code_snippet": self.code_snippet,
            "cwe_id": self.cwe_id,
            "cvss_score": self.cvss_score,
            "fix_suggestion": self.fix_suggestion,
            "tool_source": self.tool_source,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "metadata": json.loads(self.metadata) if self.metadata else {}
        }


@dataclass 
class PatchRecord:
    """Database record for patches"""
    id: Optional[int] = None
    patch_id: str = ""
    vulnerability_id: str = ""
    session_id: str = ""
    file_path: str = ""
    original_code: str = ""
    patched_code: str = ""
    patch_description: str = ""
    confidence: float = 1.0
    patch_type: str = "fix"
    lines_added: int = 0
    lines_removed: int = 0
    lines_modified: int = 0
    test_suggested: Optional[str] = None
    notes: Optional[str] = None
    created_at: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "patch_id": self.patch_id,
            "vulnerability_id": self.vulnerability_id,
            "session_id": self.session_id,
            "file_path": self.file_path,
            "original_code": self.original_code,
            "patched_code": self.patched_code,
            "patch_description": self.patch_description,
            "confidence": self.confidence,
            "patch_type": self.patch_type,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "lines_modified": self.lines_modified,
            "test_suggested": self.test_suggested,
            "notes": self.notes,
            "created_at": self.created_at
        }


@dataclass
class TriageRecord:
    """Database record for triage results"""
    id: Optional[int] = None
    vulnerability_id: str = ""
    session_id: str = ""
    priority: str = "medium"
    exploitability: str = "unknown"
    business_impact: str = ""
    technical_impact: str = ""
    attack_vector: str = ""
    remediation_effort: str = "moderate"
    timeline_recommendation: str = "1-month"
    justification: str = ""
    confidence: float = 1.0
    risk_score: float = 5.0
    created_at: float = 0.0
    metadata: str = "{}"  # JSON for prerequisites, affected_components, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        metadata_dict = json.loads(self.metadata) if self.metadata else {}
        return {
            "id": self.id,
            "vulnerability_id": self.vulnerability_id,
            "session_id": self.session_id,
            "priority": self.priority,
            "exploitability": self.exploitability,
            "business_impact": self.business_impact,
            "technical_impact": self.technical_impact,
            "attack_vector": self.attack_vector,
            "remediation_effort": self.remediation_effort,
            "timeline_recommendation": self.timeline_recommendation,
            "justification": self.justification,
            "confidence": self.confidence,
            "risk_score": self.risk_score,
            "created_at": self.created_at,
            **metadata_dict
        }


@dataclass
class SessionRecord:
    """Database record for analysis sessions"""
    id: Optional[int] = None
    session_id: str = ""
    analysis_type: str = ""
    target: str = ""
    status: str = "active"  # active, completed, failed
    started_at: float = 0.0
    completed_at: Optional[float] = None
    total_vulnerabilities: int = 0
    total_patches: int = 0
    total_cost: float = 0.0
    metadata: str = "{}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "analysis_type": self.analysis_type,
            "target": self.target,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_vulnerabilities": self.total_vulnerabilities,
            "total_patches": self.total_patches,
            "total_cost": self.total_cost,
            "metadata": json.loads(self.metadata) if self.metadata else {}
        }


class Database:
    """Async SQLite database manager"""
    
    def __init__(self, db_path: str = "vulnerability_analysis.db"):
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None
        
    async def initialize(self):
        """Initialize database and create tables"""
        self.connection = await aiosqlite.connect(self.db_path)
        await self._create_tables()
        
    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
    
    async def _create_tables(self):
        """Create all database tables"""
        
        # Vulnerabilities table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vuln_id TEXT UNIQUE NOT NULL,
                session_id TEXT NOT NULL,
                vuln_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                function_name TEXT,
                code_snippet TEXT,
                cwe_id TEXT,
                cvss_score REAL,
                fix_suggestion TEXT,
                tool_source TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at REAL NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        
        # Patches table  
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS patches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patch_id TEXT UNIQUE NOT NULL,
                vulnerability_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                original_code TEXT NOT NULL,
                patched_code TEXT NOT NULL,
                patch_description TEXT NOT NULL,
                confidence REAL NOT NULL,
                patch_type TEXT NOT NULL,
                lines_added INTEGER NOT NULL,
                lines_removed INTEGER NOT NULL,
                lines_modified INTEGER NOT NULL,
                test_suggested TEXT,
                notes TEXT,
                created_at REAL NOT NULL,
                FOREIGN KEY (vulnerability_id) REFERENCES vulnerabilities (vuln_id)
            )
        """)
        
        # Triage results table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS triage_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vulnerability_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                priority TEXT NOT NULL,
                exploitability TEXT NOT NULL,
                business_impact TEXT NOT NULL,
                technical_impact TEXT NOT NULL,
                attack_vector TEXT NOT NULL,
                remediation_effort TEXT NOT NULL,
                timeline_recommendation TEXT NOT NULL,
                justification TEXT NOT NULL,
                confidence REAL NOT NULL,
                risk_score REAL NOT NULL,
                created_at REAL NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (vulnerability_id) REFERENCES vulnerabilities (vuln_id)
            )
        """)
        
        # Sessions table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                analysis_type TEXT NOT NULL,
                target TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at REAL NOT NULL,
                completed_at REAL,
                total_vulnerabilities INTEGER DEFAULT 0,
                total_patches INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                metadata TEXT DEFAULT '{}'
            )
        """)
        
        # Agent events table for audit trail
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS agent_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp REAL NOT NULL,
                data TEXT NOT NULL
            )
        """)
        
        await self.connection.commit()
    
    # Vulnerability operations
    async def insert_vulnerability(self, vuln: VulnerabilityRecord) -> int:
        """Insert vulnerability record"""
        cursor = await self.connection.execute("""
            INSERT INTO vulnerabilities (
                vuln_id, session_id, vuln_type, severity, description,
                file_path, line_number, function_name, code_snippet, cwe_id,
                cvss_score, fix_suggestion, tool_source, confidence, created_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            vuln.vuln_id, vuln.session_id, vuln.vuln_type, vuln.severity,
            vuln.description, vuln.file_path, vuln.line_number, vuln.function_name,
            vuln.code_snippet, vuln.cwe_id, vuln.cvss_score, vuln.fix_suggestion,
            vuln.tool_source, vuln.confidence, vuln.created_at, vuln.metadata
        ))
        await self.connection.commit()
        return cursor.lastrowid
    
    async def get_vulnerabilities_by_session(self, session_id: str) -> List[VulnerabilityRecord]:
        """Get all vulnerabilities for a session"""
        cursor = await self.connection.execute(
            "SELECT * FROM vulnerabilities WHERE session_id = ? ORDER BY created_at DESC",
            (session_id,)
        )
        rows = await cursor.fetchall()
        
        vulnerabilities = []
        for row in rows:
            vuln = VulnerabilityRecord(
                id=row[0], vuln_id=row[1], session_id=row[2], vuln_type=row[3],
                severity=row[4], description=row[5], file_path=row[6], line_number=row[7],
                function_name=row[8], code_snippet=row[9], cwe_id=row[10], cvss_score=row[11],
                fix_suggestion=row[12], tool_source=row[13], confidence=row[14], created_at=row[15],
                metadata=row[16] if row[16] else "{}"
            )
            vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    # Patch operations  
    async def insert_patch(self, patch: PatchRecord) -> int:
        """Insert patch record"""
        cursor = await self.connection.execute("""
            INSERT INTO patches (
                patch_id, vulnerability_id, session_id, file_path, original_code,
                patched_code, patch_description, confidence, patch_type, lines_added,
                lines_removed, lines_modified, test_suggested, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patch.patch_id, patch.vulnerability_id, patch.session_id, patch.file_path,
            patch.original_code, patch.patched_code, patch.patch_description, patch.confidence,
            patch.patch_type, patch.lines_added, patch.lines_removed, patch.lines_modified,
            patch.test_suggested, patch.notes, patch.created_at
        ))
        await self.connection.commit()
        return cursor.lastrowid
    
    async def get_patches_by_session(self, session_id: str) -> List[PatchRecord]:
        """Get all patches for a session"""
        cursor = await self.connection.execute(
            "SELECT * FROM patches WHERE session_id = ? ORDER BY created_at DESC",
            (session_id,)
        )
        rows = await cursor.fetchall()
        
        patches = []
        for row in rows:
            patch = PatchRecord(
                id=row[0], patch_id=row[1], vulnerability_id=row[2], session_id=row[3],
                file_path=row[4], original_code=row[5], patched_code=row[6], patch_description=row[7],
                confidence=row[8], patch_type=row[9], lines_added=row[10], lines_removed=row[11],
                lines_modified=row[12], test_suggested=row[13], notes=row[14], created_at=row[15]
            )
            patches.append(patch)
        
        return patches
    
    # Triage operations
    async def insert_triage_result(self, triage: TriageRecord) -> int:
        """Insert triage result"""
        cursor = await self.connection.execute("""
            INSERT INTO triage_results (
                vulnerability_id, session_id, priority, exploitability, business_impact,
                technical_impact, attack_vector, remediation_effort, timeline_recommendation,
                justification, confidence, risk_score, created_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            triage.vulnerability_id, triage.session_id, triage.priority, triage.exploitability,
            triage.business_impact, triage.technical_impact, triage.attack_vector,
            triage.remediation_effort, triage.timeline_recommendation, triage.justification,
            triage.confidence, triage.risk_score, triage.created_at, triage.metadata
        ))
        await self.connection.commit()
        return cursor.lastrowid
    
    # Session operations
    async def insert_session(self, session: SessionRecord) -> int:
        """Insert session record"""
        cursor = await self.connection.execute("""
            INSERT INTO sessions (
                session_id, analysis_type, target, status, started_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session.session_id, session.analysis_type, session.target,
            session.status, session.started_at, session.metadata
        ))
        await self.connection.commit()
        return cursor.lastrowid
    
    async def update_session_status(self, session_id: str, status: str, completed_at: float = None):
        """Update session status"""
        await self.connection.execute("""
            UPDATE sessions 
            SET status = ?, completed_at = ?
            WHERE session_id = ?
        """, (status, completed_at, session_id))
        await self.connection.commit()
    
    async def get_session(self, session_id: str) -> Optional[SessionRecord]:
        """Get session by ID"""
        cursor = await self.connection.execute(
            "SELECT * FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        row = await cursor.fetchone()
        
        if row:
            return SessionRecord(
                id=row[0], session_id=row[1], analysis_type=row[2], target=row[3],
                status=row[4], started_at=row[5], completed_at=row[6],
                total_vulnerabilities=row[7], total_patches=row[8], total_cost=row[9],
                metadata=row[10] if row[10] else "{}"
            )
        return None
    
    async def get_recent_sessions(self, limit: int = 50) -> List[SessionRecord]:
        """Get recent sessions"""
        cursor = await self.connection.execute(
            "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        
        sessions = []
        for row in rows:
            session = SessionRecord(
                id=row[0], session_id=row[1], analysis_type=row[2], target=row[3],
                status=row[4], started_at=row[5], completed_at=row[6],
                total_vulnerabilities=row[7], total_patches=row[8], total_cost=row[9],
                metadata=row[10] if row[10] else "{}"
            )
            sessions.append(session)
        
        return sessions
    
    # Agent events for audit trail
    async def log_agent_event(self, session_id: str, agent_id: str, event_type: str, data: Dict[str, Any]):
        """Log agent event for audit trail"""
        await self.connection.execute("""
            INSERT INTO agent_events (session_id, agent_id, event_type, timestamp, data)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, agent_id, event_type, time.time(), json.dumps(data)))
        await self.connection.commit()
    
    # Statistics and analytics
    async def get_vulnerability_stats(self) -> Dict[str, Any]:
        """Get vulnerability statistics"""
        # Total vulnerabilities
        cursor = await self.connection.execute("SELECT COUNT(*) FROM vulnerabilities")
        total = (await cursor.fetchone())[0]
        
        # By severity
        cursor = await self.connection.execute("""
            SELECT severity, COUNT(*) FROM vulnerabilities GROUP BY severity
        """)
        by_severity = {row[0]: row[1] for row in await cursor.fetchall()}
        
        # By type
        cursor = await self.connection.execute("""
            SELECT vuln_type, COUNT(*) FROM vulnerabilities GROUP BY vuln_type ORDER BY COUNT(*) DESC LIMIT 10
        """)
        by_type = {row[0]: row[1] for row in await cursor.fetchall()}
        
        # Recent activity
        recent_time = time.time() - (24 * 60 * 60)  # Last 24 hours
        cursor = await self.connection.execute(
            "SELECT COUNT(*) FROM vulnerabilities WHERE created_at > ?", 
            (recent_time,)
        )
        recent_count = (await cursor.fetchone())[0]
        
        return {
            "total_vulnerabilities": total,
            "by_severity": by_severity,
            "by_type": by_type,
            "recent_24h": recent_count
        }