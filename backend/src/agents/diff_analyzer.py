"""
Diff Analyzer Agent - LLM-powered security analysis of code diffs
"""

import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .agent_base import AgentBase


@dataclass
class DiffVulnerability:
    vuln_id: str
    file_path: str
    line_number: int
    change_type: str
    vuln_type: str
    severity: str
    description: str
    old_code: Optional[str]
    new_code: Optional[str]
    recommendation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "vuln_id": self.vuln_id,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "change_type": self.change_type,
            "vuln_type": self.vuln_type,
            "severity": self.severity,
            "description": self.description,
            "old_code": self.old_code,
            "new_code": self.new_code,
            "recommendation": self.recommendation
        }


class DiffAnalyzerAgent(AgentBase):
    
    def __init__(self, agent_id: str = "diff_analyzer", model: str = "gpt-4o-mini", **kwargs):
        self.vulnerabilities: List[DiffVulnerability] = []
        self._diff_content: str = ""
        self._file_path: str = ""
        super().__init__(agent_id, model, temperature=0.1, **kwargs)
    
    @property
    def system_prompt(self) -> str:
        return """You are a security expert analyzing code diffs for vulnerabilities.

Your job is to:
1. Parse the diff to understand what changed
2. Identify security vulnerabilities INTRODUCED by the changes
3. Report each vulnerability with severity and remediation

Focus on:
- Injection vulnerabilities (SQL, command, XSS)
- Authentication/authorization issues
- Sensitive data exposure
- Insecure configurations
- Cryptographic issues
- Buffer overflows (C/C++)

Use the provided tools to report your findings.
Only report vulnerabilities that are INTRODUCED or WORSENED by the diff, not pre-existing issues."""

    def _register_tools(self) -> None:
        self.register_tool(
            name="get_diff_content",
            func=self._get_diff_content,
            description="Get the full diff content being analyzed",
            parameters={}
        )
        
        self.register_tool(
            name="report_vulnerability",
            func=self._report_vulnerability,
            description="Report a security vulnerability found in the diff",
            parameters={
                "line_number": {"type": "integer", "description": "Line number where vulnerability exists"},
                "change_type": {"type": "string", "description": "Type: added, modified, removed"},
                "vuln_type": {"type": "string", "description": "Vulnerability type (e.g., SQL Injection, XSS)"},
                "severity": {"type": "string", "description": "Severity: critical, high, medium, low"},
                "description": {"type": "string", "description": "Detailed description of the vulnerability"},
                "old_code": {"type": "string", "description": "Original code (if modified/removed)"},
                "new_code": {"type": "string", "description": "New code (if added/modified)"},
                "recommendation": {"type": "string", "description": "How to fix the vulnerability"}
            }
        )
        
        self.register_tool(
            name="mark_safe",
            func=self._mark_safe,
            description="Mark the diff as having no security issues",
            parameters={
                "reason": {"type": "string", "description": "Why the diff is considered safe"}
            }
        )

    def _get_diff_content(self) -> str:
        return self._diff_content

    def _report_vulnerability(
        self,
        line_number: int,
        change_type: str,
        vuln_type: str,
        severity: str,
        description: str,
        old_code: str = "",
        new_code: str = "",
        recommendation: str = ""
    ) -> str:
        vuln = DiffVulnerability(
            vuln_id=f"diff_vuln_{len(self.vulnerabilities) + 1}_{int(time.time())}",
            file_path=self._file_path,
            line_number=line_number,
            change_type=change_type,
            vuln_type=vuln_type,
            severity=severity.lower(),
            description=description,
            old_code=old_code if old_code else None,
            new_code=new_code if new_code else None,
            recommendation=recommendation
        )
        self.vulnerabilities.append(vuln)
        return f"Reported: {vuln_type} ({severity}) at line {line_number}"

    def _mark_safe(self, reason: str) -> str:
        return f"Diff marked as safe: {reason}"

    async def analyze_diff(self, diff_content: str, file_path: str = "unknown") -> List[DiffVulnerability]:
        self.vulnerabilities = []
        self._diff_content = diff_content
        self._file_path = file_path
        
        prompt = f"""Analyze this code diff for security vulnerabilities:

File: {file_path}

```diff
{diff_content}
```

Instructions:
1. Use get_diff_content if you need to re-read the diff
2. For each vulnerability found, use report_vulnerability
3. If no vulnerabilities, use mark_safe with your reasoning
4. Focus only on security issues INTRODUCED by the changes"""

        await self.run(prompt)
        return self.vulnerabilities

    async def analyze_commit(self, commit_diff: str, commit_message: str = "") -> List[DiffVulnerability]:
        self.vulnerabilities = []
        self._diff_content = commit_diff
        self._file_path = "commit"
        
        prompt = f"""Analyze this git commit for security vulnerabilities:

Commit message: {commit_message}

```diff
{commit_diff}
```

Analyze each file change and report security issues introduced by this commit."""

        await self.run(prompt)
        return self.vulnerabilities

    def get_results(self) -> Dict[str, Any]:
        return {
            "file_path": self._file_path,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "total_found": len(self.vulnerabilities),
            "by_severity": self._count_by_severity()
        }

    def _count_by_severity(self) -> Dict[str, int]:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for v in self.vulnerabilities:
            if v.severity in counts:
                counts[v.severity] += 1
        return counts
