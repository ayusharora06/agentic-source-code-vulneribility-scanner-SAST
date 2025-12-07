"""
API Routes for vulnerability analysis tool
"""

import time
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from pydantic import BaseModel

from ..database.models import Database
from ..config.settings import get_settings, Settings


class AnalysisRequest(BaseModel):
    """Request model for starting analysis"""
    type: str = "file"  # "file", "project", "code"
    target: str  # file path, project path, or code snippet
    session_id: Optional[str] = None
    options: Dict[str, Any] = {}


class SessionResponse(BaseModel):
    """Response model for session operations"""
    session_id: str
    status: str
    message: str
    timestamp: float


def create_api_router() -> APIRouter:
    """Create and configure API router"""
    router = APIRouter()
    
    # Dependencies
    def get_database():
        # This would be injected by the main app
        # For now, we'll handle this in the main app
        pass
    
    @router.get("/dashboard")
    async def get_dashboard():
        """Get all dashboard data in single call"""
        return {
            "stats": {
                "vulnerabilities": {
                    "total_vulnerabilities": 0,
                    "by_severity": {},
                    "by_type": {},
                    "recent_24h": 0
                },
                "sessions": {
                    "total_sessions": 0,
                    "active_sessions": 0,
                    "completed_sessions": 0,
                    "failed_sessions": 0,
                    "average_duration": 0.0
                }
            },
            "recent_sessions": [],
            "vulnerabilities": [],
            "timestamp": time.time()
        }
    
    @router.get("/sessions")
    async def get_sessions(limit: int = 50):
        """Get recent analysis sessions"""
        return {
            "sessions": [],
            "total": 0,
            "limit": limit
        }
    
    @router.get("/vulnerabilities")
    async def get_vulnerabilities(limit: int = 100, severity: Optional[str] = None):
        """Get all vulnerabilities"""
        return {
            "vulnerabilities": [],
            "total": 0,
            "limit": limit
        }
    
    @router.get("/sessions/{session_id}")
    async def get_session(session_id: str):
        """Get specific session details"""
        # This will be implemented when database is available
        return {
            "session_id": session_id,
            "status": "not_found"
        }
    
    @router.get("/sessions/{session_id}/vulnerabilities")
    async def get_session_vulnerabilities(session_id: str):
        """Get vulnerabilities for a session"""
        return {
            "session_id": session_id,
            "vulnerabilities": [],
            "total": 0
        }
    
    @router.get("/sessions/{session_id}/patches")
    async def get_session_patches(session_id: str):
        """Get patches for a session"""
        return {
            "session_id": session_id,
            "patches": [],
            "total": 0
        }
    
    @router.get("/sessions/{session_id}/triage")
    async def get_session_triage(session_id: str):
        """Get triage results for a session"""
        return {
            "session_id": session_id,
            "triage_results": [],
            "total": 0
        }
    
    @router.post("/upload")
    async def upload_file(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        session_id: Optional[str] = None
    ):
        """Upload file for analysis"""
        settings = get_settings()
        
        # Check file size
        if file.size > settings.max_file_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
            )
        
        # Create session ID if not provided
        if not session_id:
            session_id = f"upload_{int(time.time())}"
        
        # Save file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Start analysis in background
        # This would trigger the analysis pipeline
        background_tasks.add_task(
            lambda: print(f"Would analyze file: {temp_file_path}")
        )
        
        return {
            "message": "File uploaded successfully",
            "session_id": session_id,
            "filename": file.filename,
            "size": file.size,
            "temporary_path": temp_file_path
        }
    
    @router.get("/stats/vulnerabilities")
    async def get_vulnerability_stats():
        """Get vulnerability statistics"""
        # This will be implemented when database is available
        return {
            "total_vulnerabilities": 0,
            "by_severity": {},
            "by_type": {},
            "recent_24h": 0
        }
    
    @router.get("/stats/sessions")
    async def get_session_stats():
        """Get session statistics"""
        return {
            "total_sessions": 0,
            "active_sessions": 0,
            "completed_sessions": 0,
            "failed_sessions": 0,
            "average_duration": 0.0
        }
    
    @router.get("/tools/status")
    async def get_tools_status():
        """Get status of available analysis tools"""
        import subprocess
        
        tools = {}
        
        # Check for Infer
        try:
            result = subprocess.run(['which', 'infer'], capture_output=True, text=True)
            tools['infer'] = {
                "available": result.returncode == 0,
                "path": result.stdout.strip() if result.returncode == 0 else None
            }
        except:
            tools['infer'] = {"available": False, "error": "Command failed"}
        
        # Check for Clang
        try:
            result = subprocess.run(['which', 'clang'], capture_output=True, text=True)
            tools['clang'] = {
                "available": result.returncode == 0,
                "path": result.stdout.strip() if result.returncode == 0 else None
            }
        except:
            tools['clang'] = {"available": False, "error": "Command failed"}
        
        # Pattern analysis is always available
        tools['pattern_analysis'] = {
            "available": True,
            "description": "Built-in pattern-based vulnerability detection"
        }
        
        return tools
    
    @router.get("/agents/tools")
    async def get_agent_tools():
        """Get available tools for all agents"""
        # This would come from the agent manager
        return {
            "vuln_analyzer": [
                "analyze_file_static",
                "analyze_with_infer", 
                "analyze_with_clang",
                "pattern_analysis",
                "ai_vulnerability_review"
            ],
            "patch_producer": [
                "generate_patch",
                "validate_patch", 
                "suggest_test",
                "create_diff"
            ],
            "triage_agent": [
                "triage_vulnerability",
                "calculate_risk_score",
                "prioritize_vulnerabilities",
                "assess_exploitability",
                "recommend_timeline"
            ]
        }
    
    @router.post("/test/agent")
    async def test_agent(request: Dict[str, Any]):
        """Test agent functionality"""
        agent_id = request.get("agent_id", "vuln_analyzer")
        message = request.get("message", "Hello")
        context = request.get("context", {})
        
        # This would interact with the actual agent
        return {
            "agent_id": agent_id,
            "message": message,
            "response": f"Agent {agent_id} processed: {message}",
            "context": context,
            "timestamp": time.time()
        }
    
    @router.post("/analysis/start")
    async def start_analysis_v1(
        request: AnalysisRequest,
        background_tasks: BackgroundTasks
    ):
        """Start vulnerability analysis via API v1"""
        session_id = request.session_id or f"session_{int(time.time())}"
        
        return {
            "message": "Analysis started",
            "session_id": session_id,
            "type": request.type,
            "target": request.target[:100] if len(request.target) > 100 else request.target,
            "status": "started",
            "timestamp": time.time()
        }
    
    @router.get("/analysis/{session_id}/results")
    async def get_analysis_results(session_id: str):
        """Get analysis results for a session"""
        return {
            "session_id": session_id,
            "status": "pending",
            "vulnerabilities": [],
            "patches": [],
            "triage": [],
            "timestamp": time.time()
        }
    
    @router.get("/config")
    async def get_config():
        """Get application configuration (public settings only)"""
        settings = get_settings()
        
        return {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "max_file_size": settings.max_file_size,
            "max_project_files": settings.max_project_files,
            "analysis_timeout": settings.analysis_timeout,
            "available_features": {
                "infer_analysis": settings.enable_infer,
                "clang_analysis": settings.enable_clang,
                "pattern_analysis": settings.enable_pattern_analysis
            }
        }
    
    @router.post("/config/update")
    async def update_config(config_updates: Dict[str, Any]):
        """Update configuration (admin only)"""
        # This would require authentication in a real implementation
        return {
            "message": "Configuration update not implemented",
            "updates": config_updates
        }
    
    return router