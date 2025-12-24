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
    in_diff: bool = True
    
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
            "recommendation": self.recommendation,
            "in_diff": self.in_diff
        }


class DiffAnalyzerAgent(AgentBase):
    
    def __init__(self, agent_id: str = "diff_analyzer", model: str = "gpt-4o-mini", **kwargs):
        self.vulnerabilities: List[DiffVulnerability] = []
        self._diff_content: str = ""
        self._file_path: str = ""
        self._file_contents: Dict[str, str] = {}
        self._changed_lines: Dict[str, List[int]] = {}
        super().__init__(agent_id, model, temperature=0.1, **kwargs)
    
    @property
    def system_prompt(self) -> str:
        return """You are a security expert analyzing code for vulnerabilities.

Your job is to:
1. Analyze both the diff AND the full file contents
2. Identify ALL security vulnerabilities in the affected files
3. Mark whether each vulnerability is in the changed lines or existing code

For each vulnerability, set in_diff:
- true = vulnerability is in newly changed/added lines
- false = vulnerability exists in the file but was NOT part of this commit

Focus on:
- Injection vulnerabilities (SQL, command, XSS)
- Authentication/authorization issues
- Sensitive data exposure
- Insecure configurations
- Cryptographic issues
- Buffer overflows (C/C++)

Use the provided tools to report your findings."""

    def _register_tools(self) -> None:
        self.register_tool(
            name="get_diff_content",
            func=self._get_diff_content,
            description="Get the diff content showing what changed",
            parameters={}
        )
        
        self.register_tool(
            name="get_file_content",
            func=self._get_file_content,
            description="Get the full content of a specific file",
            parameters={
                "file_path": {"type": "string", "description": "Path of the file to read"}
            }
        )
        
        self.register_tool(
            name="get_changed_lines",
            func=self._get_changed_lines,
            description="Get the line numbers that were changed in the commit",
            parameters={
                "file_path": {"type": "string", "description": "Path of the file"}
            }
        )
        
        self.register_tool(
            name="report_vulnerability",
            func=self._report_vulnerability,
            description="Report a security vulnerability",
            parameters={
                "file_path": {"type": "string", "description": "File where vulnerability exists"},
                "line_number": {"type": "integer", "description": "Line number of vulnerability"},
                "vuln_type": {"type": "string", "description": "Vulnerability type (e.g., SQL Injection, XSS)"},
                "severity": {"type": "string", "description": "Severity: critical, high, medium, low"},
                "description": {"type": "string", "description": "Detailed description"},
                "in_diff": {"type": "boolean", "description": "True if in changed lines, False if pre-existing"},
                "code_snippet": {"type": "string", "description": "The vulnerable code"},
                "recommendation": {"type": "string", "description": "How to fix"}
            }
        )
        
        self.register_tool(
            name="mark_safe",
            func=self._mark_safe,
            description="Mark analysis as complete with no issues found",
            parameters={
                "reason": {"type": "string", "description": "Why no vulnerabilities were found"}
            }
        )

    def _get_diff_content(self) -> str:
        return self._diff_content

    def _get_file_content(self, file_path: str = "") -> str:
        for key in self._file_contents:
            if key == file_path or key.endswith(file_path) or file_path.endswith(key):
                return self._file_contents[key]
        return f"File not found: {file_path}. Available files: {list(self._file_contents.keys())}"

    def _get_changed_lines(self, file_path: str = "") -> str:
        for key in self._changed_lines:
            if key == file_path or key.endswith(file_path) or file_path.endswith(key):
                lines = self._changed_lines[key]
                return f"Changed lines in {key}: {lines}"
        return f"No changed lines found for {file_path}"

    def _report_vulnerability(
        self,
        file_path: str = "",
        line_number: int = 0,
        vuln_type: str = "",
        severity: str = "medium",
        description: str = "",
        in_diff: bool = True,
        code_snippet: str = "",
        recommendation: str = ""
    ) -> str:
        actual_file = file_path or self._file_path
        
        vuln = DiffVulnerability(
            vuln_id=f"diff_vuln_{len(self.vulnerabilities) + 1}_{int(time.time())}",
            file_path=actual_file,
            line_number=line_number,
            change_type="added" if in_diff else "existing",
            vuln_type=vuln_type,
            severity=severity.lower(),
            description=description,
            old_code=None,
            new_code=code_snippet if code_snippet else None,
            recommendation=recommendation,
            in_diff=in_diff
        )
        self.vulnerabilities.append(vuln)
        
        status = "IN COMMIT" if in_diff else "PRE-EXISTING"
        return f"Reported [{status}]: {vuln_type} ({severity}) at {actual_file}:{line_number}"

    def _mark_safe(self, reason: str = "") -> str:
        return f"Analysis complete: {reason}"

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
2. For each vulnerability found, use report_vulnerability with in_diff=true
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

    async def analyze_commit_with_context(
        self, 
        diff_content: str, 
        commit_message: str,
        file_contents: Dict[str, str],
        changed_lines: Dict[str, List[int]]
    ) -> List[DiffVulnerability]:
        self.vulnerabilities = []
        self._diff_content = diff_content
        self._file_path = "commit"
        self._file_contents = file_contents
        self._changed_lines = changed_lines
        
        files_list = "\n".join([f"- {f}" for f in file_contents.keys()])
        
        prompt = f"""Analyze this git commit for security vulnerabilities.

Commit message: {commit_message}

Files changed:
{files_list}

DIFF (what changed):
```diff
{diff_content[:4000]}
```

Instructions:
1. Use get_diff_content to see what changed in the commit
2. Use get_file_content to read the FULL content of each affected file
3. Use get_changed_lines to see which line numbers were modified
4. Report ALL vulnerabilities found in the affected files using report_vulnerability
5. Set in_diff=true if the vulnerability is in a changed line, in_diff=false if it's pre-existing
6. If no vulnerabilities found, use mark_safe

This helps identify both new vulnerabilities introduced by the commit AND existing vulnerabilities in the affected files."""

        await self.run(prompt)
        return self.vulnerabilities

    def get_results(self) -> Dict[str, Any]:
        in_diff_count = sum(1 for v in self.vulnerabilities if v.in_diff)
        existing_count = len(self.vulnerabilities) - in_diff_count
        
        return {
            "file_path": self._file_path,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "total_found": len(self.vulnerabilities),
            "in_diff_count": in_diff_count,
            "existing_count": existing_count,
            "by_severity": self._count_by_severity()
        }

    def _count_by_severity(self) -> Dict[str, int]:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for v in self.vulnerabilities:
            if v.severity in counts:
                counts[v.severity] += 1
        return counts
