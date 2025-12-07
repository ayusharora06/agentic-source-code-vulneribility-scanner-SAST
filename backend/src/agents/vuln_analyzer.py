"""
Vulnerability Analyzer Agent - LLM-powered vulnerability detection
Inspired by RoboDuck's vuln_analyzer
"""

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .agent_base import AgentBase, AgentStatus


@dataclass
class Vulnerability:
    vuln_id: str
    vuln_type: str
    severity: str
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    cwe_id: Optional[str] = None
    confidence: float = 0.0
    remediation: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "vuln_id": self.vuln_id,
            "vuln_type": self.vuln_type,
            "severity": self.severity,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "cwe_id": self.cwe_id,
            "confidence": self.confidence,
            "remediation": self.remediation,
            "created_at": self.created_at
        }


class VulnAnalyzerAgent(AgentBase):
    
    def __init__(
        self,
        agent_id: str = "vuln_analyzer",
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        **kwargs
    ):
        self.discovered_vulnerabilities: List[Vulnerability] = []
        self._source_code: str = ""
        self._file_path: str = ""
        super().__init__(agent_id, model, temperature, **kwargs)
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert security vulnerability analyzer. Your job is to carefully analyze source code and identify security vulnerabilities.

For each vulnerability you find, you MUST use the report_vulnerability tool to report it with:
- vuln_type: The type of vulnerability (e.g., "SQL Injection", "Buffer Overflow", "XSS", "Command Injection", etc.)
- severity: One of "critical", "high", "medium", "low"
- description: A clear description of the vulnerability
- line_number: The line number where the vulnerability exists
- code_snippet: The vulnerable code snippet
- cwe_id: The CWE ID if known (e.g., "CWE-89" for SQL Injection)
- remediation: How to fix the vulnerability

You have tools to:
1. read_source - Read specific lines from the source code
2. find_pattern - Search for specific patterns in the code
3. report_vulnerability - Report a discovered vulnerability

Analyze the code thoroughly for:
- Injection vulnerabilities (SQL, Command, LDAP, XPath, etc.)
- Buffer overflows and memory corruption
- Authentication/Authorization issues
- Cryptographic weaknesses
- Input validation issues
- Race conditions
- Information disclosure
- Insecure configurations

Be thorough but precise. Only report real vulnerabilities with high confidence."""

    def _register_tools(self) -> None:
        self.register_tool(
            name="read_source",
            func=self._read_source,
            description="Read specific lines from the source code being analyzed",
            parameters={
                "start_line": {"type": "integer", "description": "Starting line number (1-indexed)"},
                "end_line": {"type": "integer", "description": "Ending line number (1-indexed)"}
            }
        )
        
        self.register_tool(
            name="find_pattern",
            func=self._find_pattern,
            description="Search for a regex pattern in the source code",
            parameters={
                "pattern": {"type": "string", "description": "Regex pattern to search for"}
            }
        )
        
        self.register_tool(
            name="report_vulnerability",
            func=self._report_vulnerability,
            description="Report a discovered vulnerability",
            parameters={
                "vuln_type": {"type": "string", "description": "Type of vulnerability"},
                "severity": {"type": "string", "description": "Severity: critical, high, medium, or low"},
                "description": {"type": "string", "description": "Description of the vulnerability"},
                "line_number": {"type": "integer", "description": "Line number of the vulnerability"},
                "code_snippet": {"type": "string", "description": "The vulnerable code snippet"},
                "cwe_id": {"type": "string", "description": "CWE ID (e.g., CWE-89)"},
                "remediation": {"type": "string", "description": "How to fix the vulnerability"}
            }
        )
    
    def _read_source(self, start_line: int, end_line: int) -> str:
        lines = self._source_code.split('\n')
        start = max(0, start_line - 1)
        end = min(len(lines), end_line)
        
        result_lines = []
        for i in range(start, end):
            result_lines.append(f"{i + 1}: {lines[i]}")
        
        return '\n'.join(result_lines)
    
    def _find_pattern(self, pattern: str) -> str:
        import re
        lines = self._source_code.split('\n')
        matches = []
        
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            for i, line in enumerate(lines):
                if regex.search(line):
                    matches.append(f"Line {i + 1}: {line.strip()}")
        except re.error as e:
            return f"Invalid regex pattern: {e}"
        
        if matches:
            return '\n'.join(matches[:20])
        return "No matches found"
    
    def _report_vulnerability(
        self,
        vuln_type: str,
        severity: str,
        description: str,
        line_number: int,
        code_snippet: str,
        cwe_id: str = "",
        remediation: str = ""
    ) -> str:
        vuln_id = f"VULN-{len(self.discovered_vulnerabilities) + 1:04d}"
        
        severity = severity.lower()
        if severity not in ["critical", "high", "medium", "low"]:
            severity = "medium"
        
        confidence = 0.9 if severity in ["critical", "high"] else 0.7
        
        vuln = Vulnerability(
            vuln_id=vuln_id,
            vuln_type=vuln_type,
            severity=severity,
            description=description,
            file_path=self._file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            cwe_id=cwe_id if cwe_id else None,
            confidence=confidence,
            remediation=remediation if remediation else None
        )
        
        self.discovered_vulnerabilities.append(vuln)
        
        return f"Vulnerability {vuln_id} reported: {vuln_type} ({severity}) at line {line_number}"
    
    async def analyze_code(self, code: str, file_path: str = "<analyzed_code>") -> List[Vulnerability]:
        self._source_code = code
        self._file_path = file_path
        self.discovered_vulnerabilities = []
        
        lines = code.split('\n')
        code_preview = '\n'.join(f"{i+1}: {line}" for i, line in enumerate(lines[:100]))
        if len(lines) > 100:
            code_preview += f"\n... ({len(lines) - 100} more lines)"
        
        prompt = f"""Analyze the following source code for security vulnerabilities.
        
File: {file_path}
Total lines: {len(lines)}

Source code:
```
{code_preview}
```

Use the read_source tool if you need to see more lines.
Use find_pattern to search for specific vulnerability patterns.
Use report_vulnerability to report each vulnerability you find.

After analyzing, provide a summary of your findings."""

        await self.run(prompt)
        
        return self.discovered_vulnerabilities
    
    async def analyze_file(self, file_path: str) -> List[Vulnerability]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        return await self.analyze_code(code, file_path)
    
    def get_discovered_vulnerabilities(self) -> List[Vulnerability]:
        return self.discovered_vulnerabilities.copy()
    
    def clear_vulnerabilities(self):
        self.discovered_vulnerabilities.clear()
