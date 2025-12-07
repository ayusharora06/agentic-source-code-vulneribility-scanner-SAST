"""
Dynamic Debug Agent - LLM-powered runtime debugging assistance
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .agent_base import AgentBase


@dataclass
class DebugBreakpoint:
    bp_id: str
    file_path: str
    line_number: int
    condition: Optional[str]
    reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bp_id": self.bp_id,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "condition": self.condition,
            "reason": self.reason
        }


@dataclass
class DebugAction:
    action_id: str
    action_type: str
    target: str
    command: str
    expected_result: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "target": self.target,
            "command": self.command,
            "expected_result": self.expected_result
        }


@dataclass
class DebugSession:
    session_id: str
    vulnerability: Dict[str, Any]
    breakpoints: List[DebugBreakpoint]
    actions: List[DebugAction]
    analysis: str
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "vulnerability": self.vulnerability,
            "breakpoints": [b.to_dict() for b in self.breakpoints],
            "actions": [a.to_dict() for a in self.actions],
            "analysis": self.analysis,
            "created_at": self.created_at
        }


class DynamicDebugAgent(AgentBase):
    
    def __init__(self, agent_id: str = "dynamic_debug", model: str = "gpt-4o-mini", **kwargs):
        self.sessions: List[DebugSession] = []
        self._breakpoints: List[DebugBreakpoint] = []
        self._actions: List[DebugAction] = []
        self._vuln_context: Dict[str, Any] = {}
        self._source_code: str = ""
        super().__init__(agent_id, model, temperature=0.2, **kwargs)
    
    @property
    def system_prompt(self) -> str:
        return """You are a debugging expert helping to dynamically analyze vulnerabilities.

Your job is to:
1. Analyze vulnerabilities and source code
2. Design debugging strategies to confirm issues
3. Create breakpoints and debug commands
4. Plan runtime analysis steps

For each vulnerability type:
- Buffer overflow: set breakpoints before/after memcpy, watch buffer sizes
- Use-after-free: track allocation/deallocation, check pointer validity
- SQL injection: inspect query strings at execution points
- Race conditions: monitor lock acquisition and shared state

Generate GDB/LLDB/JDB commands appropriate for the language."""

    def _register_tools(self) -> None:
        self.register_tool(
            name="get_debug_context",
            func=self._get_debug_context,
            description="Get vulnerability and source code context",
            parameters={}
        )
        
        self.register_tool(
            name="set_breakpoint",
            func=self._set_breakpoint,
            description="Set a breakpoint for debugging",
            parameters={
                "file_path": {"type": "string", "description": "Source file path"},
                "line_number": {"type": "integer", "description": "Line number for breakpoint"},
                "condition": {"type": "string", "description": "Optional condition expression"},
                "reason": {"type": "string", "description": "Why this breakpoint helps"}
            }
        )
        
        self.register_tool(
            name="add_debug_action",
            func=self._add_debug_action,
            description="Add a debug action to perform",
            parameters={
                "action_type": {"type": "string", "description": "Type: inspect, watch, step, evaluate, memory_dump"},
                "target": {"type": "string", "description": "Variable or expression to act on"},
                "command": {"type": "string", "description": "Debugger command (GDB/LLDB syntax)"},
                "expected_result": {"type": "string", "description": "What to look for in the result"}
            }
        )
        
        self.register_tool(
            name="submit_analysis",
            func=self._submit_analysis,
            description="Submit the debugging analysis",
            parameters={
                "analysis": {"type": "string", "description": "Summary of debugging strategy"}
            }
        )

    def _get_debug_context(self) -> Dict[str, Any]:
        return {
            "vulnerability": self._vuln_context,
            "source_code": self._source_code[:2000]
        }

    def _set_breakpoint(
        self,
        file_path: str,
        line_number: int,
        condition: str = "",
        reason: str = ""
    ) -> str:
        bp = DebugBreakpoint(
            bp_id=f"bp_{len(self._breakpoints) + 1}",
            file_path=file_path,
            line_number=line_number,
            condition=condition if condition else None,
            reason=reason
        )
        self._breakpoints.append(bp)
        
        cond_str = f" when {condition}" if condition else ""
        return f"Breakpoint set: {file_path}:{line_number}{cond_str}"

    def _add_debug_action(
        self,
        action_type: str,
        target: str,
        command: str,
        expected_result: str
    ) -> str:
        action = DebugAction(
            action_id=f"action_{len(self._actions) + 1}",
            action_type=action_type,
            target=target,
            command=command,
            expected_result=expected_result
        )
        self._actions.append(action)
        return f"Action added: {action_type} on {target}"

    def _submit_analysis(self, analysis: str) -> str:
        session = DebugSession(
            session_id=f"debug_{int(time.time())}",
            vulnerability=self._vuln_context,
            breakpoints=self._breakpoints.copy(),
            actions=self._actions.copy(),
            analysis=analysis
        )
        self.sessions.append(session)
        
        return f"Analysis submitted: {len(self._breakpoints)} breakpoints, {len(self._actions)} actions"

    async def plan_debug_session(
        self,
        vulnerability: Dict[str, Any],
        source_code: str
    ) -> DebugSession:
        self._breakpoints = []
        self._actions = []
        self._vuln_context = vulnerability
        self._source_code = source_code
        
        prompt = f"""Plan a debugging session to confirm this vulnerability:

Vulnerability Type: {vulnerability.get('type', 'unknown')}
Severity: {vulnerability.get('severity', 'unknown')}
Location: {vulnerability.get('location', 'unknown')}
Description: {vulnerability.get('description', 'No description')}

Source code:
```
{source_code[:1500]}
```

Instructions:
1. Use get_debug_context to review the details
2. Use set_breakpoint for key locations
3. Use add_debug_action for runtime inspections
4. Use submit_analysis with your debugging strategy"""

        await self.run(prompt)
        return self.sessions[-1] if self.sessions else None

    async def generate_debug_script(
        self,
        vulnerability: Dict[str, Any],
        debugger: str = "gdb"
    ) -> str:
        self._breakpoints = []
        self._actions = []
        self._vuln_context = vulnerability
        self._source_code = ""
        
        prompt = f"""Generate a {debugger.upper()} script to debug this vulnerability:

{vulnerability}

Use set_breakpoint and add_debug_action to build the script.
Then submit_analysis with instructions for running it."""

        await self.run(prompt)
        
        script_lines = []
        for bp in self._breakpoints:
            if bp.condition:
                script_lines.append(f"break {bp.file_path}:{bp.line_number} if {bp.condition}")
            else:
                script_lines.append(f"break {bp.file_path}:{bp.line_number}")
        
        for action in self._actions:
            script_lines.append(action.command)
        
        return "\n".join(script_lines)

    def get_results(self) -> Dict[str, Any]:
        return {
            "sessions": [s.to_dict() for s in self.sessions],
            "total_breakpoints": sum(len(s.breakpoints) for s in self.sessions),
            "total_actions": sum(len(s.actions) for s in self.sessions)
        }
