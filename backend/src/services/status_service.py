"""
Centralized WebSocket status service for real-time updates
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class StatusService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._connections: Set[WebSocket] = set()
        self._session_connections: Dict[str, Set[WebSocket]] = {}
        self._initialized = True
    
    async def connect(self, websocket: WebSocket, session_id: str = None):
        await websocket.accept()
        self._connections.add(websocket)
        
        if session_id:
            if session_id not in self._session_connections:
                self._session_connections[session_id] = set()
            self._session_connections[session_id].add(websocket)
        
        logger.info(f"WebSocket connected. Total: {len(self._connections)}")
        
        await self._send(websocket, {
            "event": "connected",
            "data": {"message": "Connected to status service"}
        })
    
    def disconnect(self, websocket: WebSocket):
        self._connections.discard(websocket)
        
        for session_id, connections in list(self._session_connections.items()):
            connections.discard(websocket)
            if not connections:
                del self._session_connections[session_id]
        
        logger.info(f"WebSocket disconnected. Total: {len(self._connections)}")
    
    async def _send(self, websocket: WebSocket, message: Dict[str, Any]):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, event: str, data: Dict[str, Any] = None):
        message = {
            "event": event,
            "timestamp": time.time(),
            "data": data or {}
        }
        
        disconnected = set()
        for ws in self._connections:
            try:
                await ws.send_json(message)
            except:
                disconnected.add(ws)
        
        for ws in disconnected:
            self.disconnect(ws)
    
    async def emit(self, session_id: str, event: str, data: Dict[str, Any] = None):
        message = {
            "event": event,
            "session_id": session_id,
            "timestamp": time.time(),
            "data": data or {}
        }
        
        await self.broadcast(event, {**message["data"], "session_id": session_id})
    
    async def emit_step(self, session_id: str, step: str, status: str, message: str = None, details: Dict = None):
        await self.emit(session_id, f"step_{status}", {
            "step": step,
            "message": message or f"{step} {status}",
            "details": details or {}
        })
    
    async def emit_analysis_started(self, session_id: str, target: str):
        await self.emit(session_id, "analysis_started", {
            "target": target,
            "message": "Analysis started"
        })
    
    async def emit_analysis_completed(self, session_id: str, summary: Dict = None):
        await self.emit(session_id, "analysis_completed", {
            "message": "Analysis completed",
            "summary": summary or {}
        })
    
    async def emit_analysis_failed(self, session_id: str, error: str):
        await self.emit(session_id, "analysis_failed", {
            "message": "Analysis failed",
            "error": error
        })
    
    async def emit_vulnerability_found(self, session_id: str, vuln: Dict):
        await self.emit(session_id, "vulnerability_found", {
            "vulnerability": vuln,
            "message": f"Found {vuln.get('severity', 'unknown')} severity vulnerability"
        })


_status_service: StatusService = None


def get_status_service() -> StatusService:
    global _status_service
    if _status_service is None:
        _status_service = StatusService()
    return _status_service
