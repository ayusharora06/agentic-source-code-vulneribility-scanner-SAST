"""
Triage Agent - LLM-powered vulnerability prioritization
Inspired by RoboDuck's triage agent
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .agent_base import AgentBase
from .vuln_analyzer import Vulnerability


class Priority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TriageResult:
    triage_id: str
    vulnerability_id: str
    priority: Priority
    exploitability: str
    impact: str
    cvss_estimate: float
    reasoning: str
    recommended_action: str
    estimated_effort: str
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "triage_id": self.triage_id,
            "vulnerability_id": self.vulnerability_id,
            "priority": self.priority.value,
            "exploitability": self.exploitability,
            "impact": self.impact,
            "cvss_estimate": self.cvss_estimate,
            "reasoning": self.reasoning,
            "recommended_action": self.recommended_action,
            "estimated_effort": self.estimated_effort,
            "created_at": self.created_at
        }


class TriageAgent(AgentBase):
    
    def __init__(
        self,
        agent_id: str = "triage_agent",
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        **kwargs
    ):
        self.triage_results: List[TriageResult] = []
        self._current_vuln: Optional[Dict[str, Any]] = None
        super().__init__(agent_id, model, temperature, **kwargs)
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert security vulnerability triage specialist. Your job is to analyze vulnerabilities and prioritize them based on:

1. **Exploitability**: How easy is it to exploit?
   - Trivial: Can be exploited with minimal effort, public exploit exists
   - Easy: Requires basic skills, straightforward attack vector
   - Moderate: Requires some expertise or specific conditions
   - Difficult: Requires advanced skills or complex conditions
   - Theoretical: Very difficult to exploit in practice

2. **Impact**: What's the potential damage?
   - Critical: Full system compromise, data breach, RCE
   - High: Significant data exposure, privilege escalation
   - Medium: Limited data exposure, service disruption
   - Low: Minor information disclosure, minimal impact

3. **Priority**: Final priority assignment
   - Critical: Fix immediately, stop everything else
   - High: Fix within 24-48 hours
   - Medium: Fix within a week
   - Low: Fix when convenient

Use the submit_triage tool to submit your analysis with:
- priority: The final priority (critical, high, medium, low)
- exploitability: How exploitable (trivial, easy, moderate, difficult, theoretical)
- impact: The impact level (critical, high, medium, low)
- cvss_estimate: Estimated CVSS score (0.0 - 10.0)
- reasoning: Your detailed reasoning
- recommended_action: What should be done
- estimated_effort: Estimated fix effort (hours, days, weeks)

Be objective and consistent in your assessments."""

    def _register_tools(self) -> None:
        self.register_tool(
            name="submit_triage",
            func=self._submit_triage,
            description="Submit triage assessment for a vulnerability",
            parameters={
                "priority": {"type": "string", "description": "Priority: critical, high, medium, or low"},
                "exploitability": {"type": "string", "description": "How exploitable: trivial, easy, moderate, difficult, theoretical"},
                "impact": {"type": "string", "description": "Impact level: critical, high, medium, low"},
                "cvss_estimate": {"type": "number", "description": "Estimated CVSS score (0.0 - 10.0)"},
                "reasoning": {"type": "string", "description": "Detailed reasoning for the assessment"},
                "recommended_action": {"type": "string", "description": "Recommended action to take"},
                "estimated_effort": {"type": "string", "description": "Estimated effort to fix (e.g., '2 hours', '1 day')"}
            }
        )
    
    def _submit_triage(
        self,
        priority: str = "medium",
        exploitability: str = "moderate",
        impact: str = "medium",
        cvss_estimate: float = 5.0,
        reasoning: str = "",
        recommended_action: str = "Review manually",
        estimated_effort: str = "Unknown"
    ) -> str:
        if not self._current_vuln:
            return "Error: No vulnerability being triaged"
        
        triage_id = f"TRIAGE-{len(self.triage_results) + 1:04d}"
        
        try:
            priority_enum = Priority(priority.lower())
        except ValueError:
            priority_enum = Priority.MEDIUM
        
        cvss_estimate = max(0.0, min(10.0, cvss_estimate))
        
        result = TriageResult(
            triage_id=triage_id,
            vulnerability_id=self._current_vuln.get("vuln_id", "unknown"),
            priority=priority_enum,
            exploitability=exploitability,
            impact=impact,
            cvss_estimate=cvss_estimate,
            reasoning=reasoning,
            recommended_action=recommended_action,
            estimated_effort=estimated_effort
        )
        
        self.triage_results.append(result)
        
        return f"Triage {triage_id} submitted: Priority={priority}, CVSS={cvss_estimate}"
    
    async def triage_vulnerability(self, vulnerability: Dict[str, Any]) -> TriageResult:
        self._current_vuln = vulnerability
        
        prompt = f"""Analyze and triage the following vulnerability:

Vulnerability ID: {vulnerability.get('vuln_id', 'unknown')}
Type: {vulnerability.get('vuln_type', 'unknown')}
Severity (initial): {vulnerability.get('severity', 'unknown')}
Description: {vulnerability.get('description', 'No description')}
File: {vulnerability.get('file_path', 'unknown')}
Line: {vulnerability.get('line_number', 'unknown')}
CWE: {vulnerability.get('cwe_id', 'N/A')}

Code snippet:
```
{vulnerability.get('code_snippet', 'No code available')}
```

Remediation suggestion: {vulnerability.get('remediation', 'None provided')}

Analyze this vulnerability and use the submit_triage tool to submit your assessment."""

        await self.run(prompt)
        
        if self.triage_results:
            return self.triage_results[-1]
        
        return TriageResult(
            triage_id=f"TRIAGE-{len(self.triage_results) + 1:04d}",
            vulnerability_id=vulnerability.get("vuln_id", "unknown"),
            priority=Priority.MEDIUM,
            exploitability="unknown",
            impact="unknown",
            cvss_estimate=5.0,
            reasoning="Triage failed - using default values",
            recommended_action="Manual review required",
            estimated_effort="Unknown"
        )
    
    async def triage_vulnerabilities(self, vulnerabilities: List[Dict[str, Any]]) -> List[TriageResult]:
        results = []
        for vuln in vulnerabilities:
            result = await self.triage_vulnerability(vuln)
            results.append(result)
        return results
    
    def get_triage_results(self) -> List[TriageResult]:
        return self.triage_results.copy()
    
    def get_by_priority(self, priority: Priority) -> List[TriageResult]:
        return [r for r in self.triage_results if r.priority == priority]
    
    def clear_results(self):
        self.triage_results.clear()
