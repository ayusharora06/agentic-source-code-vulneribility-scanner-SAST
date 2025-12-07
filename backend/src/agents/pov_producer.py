"""
POV Producer Agent - LLM-powered exploit proof-of-concept generator
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .agent_base import AgentBase


@dataclass
class ExploitPOV:
    pov_id: str
    vulnerability_id: str
    exploit_type: str
    payload: str
    payload_hex: Optional[str]
    description: str
    preconditions: List[str]
    expected_outcome: str
    success_indicators: List[str]
    risk_level: str
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pov_id": self.pov_id,
            "vulnerability_id": self.vulnerability_id,
            "exploit_type": self.exploit_type,
            "payload": self.payload,
            "payload_hex": self.payload_hex,
            "description": self.description,
            "preconditions": self.preconditions,
            "expected_outcome": self.expected_outcome,
            "success_indicators": self.success_indicators,
            "risk_level": self.risk_level,
            "created_at": self.created_at
        }


class POVProducerAgent(AgentBase):
    
    def __init__(self, agent_id: str = "pov_producer", model: str = "gpt-4o-mini", **kwargs):
        self.povs: List[ExploitPOV] = []
        self._vuln_context: Dict[str, Any] = {}
        super().__init__(agent_id, model, temperature=0.2, **kwargs)
    
    @property
    def system_prompt(self) -> str:
        return """You are a security researcher creating proof-of-concept exploits for DEFENSIVE purposes.

Your job is to:
1. Analyze the vulnerability details
2. Design a minimal proof-of-concept that demonstrates the issue
3. Create a safe, reproducible exploit for testing

Guidelines:
- POCs should be minimal and targeted
- Include clear preconditions and expected outcomes
- Focus on demonstrating the vulnerability exists, not causing damage
- For memory corruption: craft inputs that trigger the bug safely
- For injection: create payloads that prove execution without harm
- Always include indicators that show successful exploitation

Use the tools to submit your POC designs."""

    def _register_tools(self) -> None:
        self.register_tool(
            name="get_vulnerability",
            func=self._get_vulnerability,
            description="Get the vulnerability details being analyzed",
            parameters={}
        )
        
        self.register_tool(
            name="submit_pov",
            func=self._submit_pov,
            description="Submit a proof-of-concept exploit",
            parameters={
                "exploit_type": {"type": "string", "description": "Type: buffer_overflow, injection, logic_flaw, etc."},
                "payload": {"type": "string", "description": "The exploit payload (text or escaped bytes)"},
                "payload_hex": {"type": "string", "description": "Hex-encoded payload for binary exploits"},
                "description": {"type": "string", "description": "What this POC does"},
                "preconditions": {"type": "array", "items": {"type": "string"}, "description": "Required conditions for exploit to work"},
                "expected_outcome": {"type": "string", "description": "What happens when exploit succeeds"},
                "success_indicators": {"type": "array", "items": {"type": "string"}, "description": "How to verify exploitation worked"},
                "risk_level": {"type": "string", "description": "Risk: low (safe), medium, high (dangerous)"}
            }
        )
        
        self.register_tool(
            name="design_input",
            func=self._design_input,
            description="Design a specific input to trigger the vulnerability",
            parameters={
                "input_type": {"type": "string", "description": "Type of input: string, binary, structured"},
                "target_field": {"type": "string", "description": "Which input field to target"},
                "strategy": {"type": "string", "description": "Exploitation strategy"}
            }
        )

    def _get_vulnerability(self) -> Dict[str, Any]:
        return self._vuln_context

    def _submit_pov(
        self,
        exploit_type: str = "unknown",
        payload: str = "",
        description: str = "",
        preconditions: List[str] = None,
        expected_outcome: str = "",
        success_indicators: List[str] = None,
        risk_level: str = "medium",
        payload_hex: str = ""
    ) -> str:
        preconditions = preconditions or []
        success_indicators = success_indicators or []
        pov = ExploitPOV(
            pov_id=f"pov_{len(self.povs) + 1}_{int(time.time())}",
            vulnerability_id=self._vuln_context.get("vuln_id", "unknown"),
            exploit_type=exploit_type,
            payload=payload,
            payload_hex=payload_hex if payload_hex else None,
            description=description,
            preconditions=preconditions,
            expected_outcome=expected_outcome,
            success_indicators=success_indicators,
            risk_level=risk_level.lower()
        )
        self.povs.append(pov)
        return f"POV submitted: {exploit_type} (risk: {risk_level})"

    def _design_input(self, input_type: str, target_field: str, strategy: str) -> str:
        return f"Designed {input_type} input targeting '{target_field}' using {strategy} strategy"

    async def generate_pov(self, vulnerability: Dict[str, Any]) -> List[ExploitPOV]:
        self.povs = []
        self._vuln_context = vulnerability
        
        prompt = f"""Generate a proof-of-concept exploit for this vulnerability:

Vulnerability Type: {vulnerability.get('type', 'unknown')}
Severity: {vulnerability.get('severity', 'unknown')}
Description: {vulnerability.get('description', 'No description')}
Location: {vulnerability.get('location', 'unknown')}
CWE: {vulnerability.get('cwe', 'N/A')}

Vulnerable Code:
```
{vulnerability.get('code_snippet', 'No code provided')}
```

Instructions:
1. Use get_vulnerability to review the details
2. Use design_input to plan your approach
3. Use submit_pov to submit your proof-of-concept
4. Keep the POC minimal and safe for testing"""

        await self.run(prompt)
        return self.povs

    def get_results(self) -> Dict[str, Any]:
        return {
            "vulnerability_id": self._vuln_context.get("vuln_id"),
            "povs": [p.to_dict() for p in self.povs],
            "total_generated": len(self.povs)
        }
