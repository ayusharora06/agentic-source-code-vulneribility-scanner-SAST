"""
Coverage Analyzer Agent - LLM-powered code coverage analysis and gap identification
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .agent_base import AgentBase


@dataclass
class CoverageGap:
    gap_id: str
    file_path: str
    start_line: int
    end_line: int
    function_name: Optional[str]
    gap_type: str
    severity: str
    reason: str
    suggestion: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "function_name": self.function_name,
            "gap_type": self.gap_type,
            "severity": self.severity,
            "reason": self.reason,
            "suggestion": self.suggestion
        }


@dataclass
class CoverageReport:
    report_id: str
    file_path: str
    total_lines: int
    covered_lines: int
    coverage_pct: float
    gaps: List[CoverageGap]
    priority_functions: List[str]
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "file_path": self.file_path,
            "total_lines": self.total_lines,
            "covered_lines": self.covered_lines,
            "coverage_pct": self.coverage_pct,
            "gaps": [g.to_dict() for g in self.gaps],
            "priority_functions": self.priority_functions,
            "created_at": self.created_at
        }


class CoverageAnalyzerAgent(AgentBase):
    
    def __init__(self, agent_id: str = "coverage_analyzer", model: str = "gpt-4o-mini", **kwargs):
        self.reports: List[CoverageReport] = []
        self._gaps: List[CoverageGap] = []
        self._priority_functions: List[str] = []
        self._coverage_data: Dict[str, Any] = {}
        self._source_code: str = ""
        super().__init__(agent_id, model, temperature=0.1, **kwargs)
    
    @property
    def system_prompt(self) -> str:
        return """You are a code coverage expert analyzing test coverage gaps.

Your job is to:
1. Analyze coverage data and source code
2. Identify critical coverage gaps
3. Prioritize which code paths need testing
4. Suggest how to improve coverage

Focus on:
- Security-critical code (auth, crypto, input validation)
- Error handling paths
- Edge cases and boundary conditions
- Complex conditional logic
- Functions with low coverage

Provide actionable insights for improving test coverage."""

    def _register_tools(self) -> None:
        self.register_tool(
            name="get_coverage_context",
            func=self._get_coverage_context,
            description="Get coverage data and source code",
            parameters={}
        )
        
        self.register_tool(
            name="report_gap",
            func=self._report_gap,
            description="Report a coverage gap",
            parameters={
                "start_line": {"type": "integer", "description": "Start line of uncovered code"},
                "end_line": {"type": "integer", "description": "End line of uncovered code"},
                "function_name": {"type": "string", "description": "Function containing the gap"},
                "gap_type": {"type": "string", "description": "Type: error_handling, edge_case, security, logic, etc."},
                "severity": {"type": "string", "description": "Severity: critical, high, medium, low"},
                "reason": {"type": "string", "description": "Why this gap matters"},
                "suggestion": {"type": "string", "description": "How to add coverage"}
            }
        )
        
        self.register_tool(
            name="prioritize_function",
            func=self._prioritize_function,
            description="Mark a function as high priority for testing",
            parameters={
                "function_name": {"type": "string", "description": "Function name"},
                "reason": {"type": "string", "description": "Why this function needs priority testing"}
            }
        )
        
        self.register_tool(
            name="submit_report",
            func=self._submit_report,
            description="Submit the coverage analysis report",
            parameters={
                "summary": {"type": "string", "description": "Summary of findings"}
            }
        )

    def _get_coverage_context(self) -> Dict[str, Any]:
        return {
            "coverage": self._coverage_data,
            "source_code": self._source_code[:3000]
        }

    def _report_gap(
        self,
        start_line: int = 0,
        end_line: int = 0,
        function_name: str = "",
        gap_type: str = "unknown",
        severity: str = "medium",
        reason: str = "",
        suggestion: str = ""
    ) -> str:
        gap = CoverageGap(
            gap_id=f"gap_{len(self._gaps) + 1}_{int(time.time())}",
            file_path=self._coverage_data.get("file_path", "unknown"),
            start_line=start_line,
            end_line=end_line,
            function_name=function_name if function_name else None,
            gap_type=gap_type,
            severity=severity.lower(),
            reason=reason,
            suggestion=suggestion
        )
        self._gaps.append(gap)
        return f"Gap reported: {gap_type} at lines {start_line}-{end_line} ({severity})"

    def _prioritize_function(self, function_name: str, reason: str) -> str:
        if function_name not in self._priority_functions:
            self._priority_functions.append(function_name)
        return f"Prioritized: {function_name} - {reason}"

    def _submit_report(self, summary: str) -> str:
        coverage_data = self._coverage_data
        
        report = CoverageReport(
            report_id=f"cov_report_{int(time.time())}",
            file_path=coverage_data.get("file_path", "unknown"),
            total_lines=coverage_data.get("total_lines", 0),
            covered_lines=coverage_data.get("covered_lines", 0),
            coverage_pct=coverage_data.get("coverage_pct", 0.0),
            gaps=self._gaps.copy(),
            priority_functions=self._priority_functions.copy()
        )
        self.reports.append(report)
        
        return f"Report submitted: {len(self._gaps)} gaps, {len(self._priority_functions)} priority functions"

    async def analyze_coverage(
        self,
        coverage_data: Dict[str, Any],
        source_code: str
    ) -> CoverageReport:
        self._gaps = []
        self._priority_functions = []
        self._coverage_data = coverage_data
        self._source_code = source_code
        
        uncovered_str = ""
        if coverage_data.get("uncovered_lines"):
            uncovered_str = f"Uncovered lines: {coverage_data['uncovered_lines'][:50]}"
        
        prompt = f"""Analyze this code coverage data:

File: {coverage_data.get('file_path', 'unknown')}
Total lines: {coverage_data.get('total_lines', 0)}
Covered lines: {coverage_data.get('covered_lines', 0)}
Coverage: {coverage_data.get('coverage_pct', 0):.1f}%
{uncovered_str}

Source code:
```
{source_code[:2000]}
```

Instructions:
1. Use get_coverage_context to review the data
2. Use report_gap for each significant coverage gap
3. Use prioritize_function for critical functions
4. Use submit_report when done analyzing"""

        await self.run(prompt)
        return self.reports[-1] if self.reports else None

    async def suggest_tests(self, source_code: str, existing_tests: str = "") -> List[str]:
        self._gaps = []
        self._priority_functions = []
        self._coverage_data = {"file_path": "unknown", "total_lines": 0, "covered_lines": 0, "coverage_pct": 0}
        self._source_code = source_code
        
        prompt = f"""Suggest tests to improve coverage for this code:

Source:
```
{source_code[:2000]}
```

{"Existing tests:" if existing_tests else ""}
```
{existing_tests[:1000] if existing_tests else "No existing tests provided"}
```

Use prioritize_function for functions that need tests.
Then submit_report with your suggestions."""

        await self.run(prompt)
        return self._priority_functions

    def get_results(self) -> Dict[str, Any]:
        return {
            "reports": [r.to_dict() for r in self.reports],
            "total_gaps": sum(len(r.gaps) for r in self.reports),
            "priority_functions": self._priority_functions
        }
