"""
Patch Producer Agent - LLM-powered security patch generation
Inspired by RoboDuck's produce_patch
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .agent_base import AgentBase


@dataclass
class SecurityPatch:
    patch_id: str
    vulnerability_id: str
    file_path: str
    original_code: str
    patched_code: str
    patch_description: str
    confidence: float
    patch_type: str
    test_cases: List[str]
    notes: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "vulnerability_id": self.vulnerability_id,
            "file_path": self.file_path,
            "original_code": self.original_code,
            "patched_code": self.patched_code,
            "patch_description": self.patch_description,
            "confidence": self.confidence,
            "patch_type": self.patch_type,
            "test_cases": self.test_cases,
            "notes": self.notes,
            "created_at": self.created_at
        }
    
    def to_diff(self) -> str:
        original_lines = self.original_code.split('\n')
        patched_lines = self.patched_code.split('\n')
        
        diff_lines = [
            f"--- a/{self.file_path}",
            f"+++ b/{self.file_path}",
            "@@ -1,{} +1,{} @@".format(len(original_lines), len(patched_lines))
        ]
        
        for line in original_lines:
            diff_lines.append(f"-{line}")
        for line in patched_lines:
            diff_lines.append(f"+{line}")
        
        return '\n'.join(diff_lines)


class PatchProducerAgent(AgentBase):
    
    def __init__(
        self,
        agent_id: str = "patch_producer",
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        **kwargs
    ):
        self.generated_patches: List[SecurityPatch] = []
        self._current_vuln: Optional[Dict[str, Any]] = None
        super().__init__(agent_id, model, temperature, **kwargs)
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert security patch developer. Your job is to generate secure, correct patches for vulnerabilities.

When generating patches, you must:
1. Understand the vulnerability thoroughly
2. Generate a minimal, focused fix
3. Preserve the original functionality
4. Follow secure coding best practices
5. Consider edge cases and error handling

Use the submit_patch tool to submit your patch with:
- original_code: The original vulnerable code
- patched_code: Your fixed code
- patch_description: Clear description of what the patch does
- confidence: Your confidence in the patch (0.0 - 1.0)
- patch_type: Type of patch (fix, mitigation, workaround)
- test_cases: List of test cases to verify the patch
- notes: Any additional notes or caveats

Guidelines:
- For injection vulnerabilities: Use parameterized queries, input validation, output encoding
- For buffer overflows: Use safe string functions, bounds checking
- For authentication issues: Implement proper validation, session management
- For cryptographic issues: Use strong algorithms, proper key management
- Always prefer fixing the root cause over workarounds

Be precise and ensure the patch compiles and doesn't break functionality."""

    def _register_tools(self) -> None:
        self.register_tool(
            name="submit_patch",
            func=self._submit_patch,
            description="Submit a security patch for a vulnerability",
            parameters={
                "original_code": {"type": "string", "description": "The original vulnerable code"},
                "patched_code": {"type": "string", "description": "The fixed code"},
                "patch_description": {"type": "string", "description": "Description of what the patch does"},
                "confidence": {"type": "number", "description": "Confidence in the patch (0.0 - 1.0)"},
                "patch_type": {"type": "string", "description": "Type: fix, mitigation, or workaround"},
                "test_cases": {"type": "array", "description": "List of test cases to verify the patch", "items": {"type": "string"}},
                "notes": {"type": "string", "description": "Additional notes or caveats"}
            }
        )
    
    def _submit_patch(
        self,
        original_code: str,
        patched_code: str,
        patch_description: str,
        confidence: float,
        patch_type: str,
        test_cases: List[str] = None,
        notes: str = ""
    ) -> str:
        if not self._current_vuln:
            return "Error: No vulnerability being patched"
        
        patch_id = f"PATCH-{len(self.generated_patches) + 1:04d}"
        
        confidence = max(0.0, min(1.0, confidence))
        
        if patch_type not in ["fix", "mitigation", "workaround"]:
            patch_type = "fix"
        
        patch = SecurityPatch(
            patch_id=patch_id,
            vulnerability_id=self._current_vuln.get("vuln_id", "unknown"),
            file_path=self._current_vuln.get("file_path", "unknown"),
            original_code=original_code,
            patched_code=patched_code,
            patch_description=patch_description,
            confidence=confidence,
            patch_type=patch_type,
            test_cases=test_cases or [],
            notes=notes if notes else None
        )
        
        self.generated_patches.append(patch)
        
        return f"Patch {patch_id} submitted: {patch_type} with {confidence:.0%} confidence"
    
    async def generate_patch(self, vulnerability: Dict[str, Any]) -> SecurityPatch:
        self._current_vuln = vulnerability
        
        prompt = f"""Generate a security patch for the following vulnerability:

Vulnerability ID: {vulnerability.get('vuln_id', 'unknown')}
Type: {vulnerability.get('vuln_type', 'unknown')}
Severity: {vulnerability.get('severity', 'unknown')}
Description: {vulnerability.get('description', 'No description')}
File: {vulnerability.get('file_path', 'unknown')}
Line: {vulnerability.get('line_number', 'unknown')}
CWE: {vulnerability.get('cwe_id', 'N/A')}

Vulnerable code:
```
{vulnerability.get('code_snippet', 'No code available')}
```

Suggested remediation: {vulnerability.get('remediation', 'None provided')}

Generate a secure patch and use the submit_patch tool to submit it.
Include test cases to verify the patch works correctly."""

        await self.run(prompt)
        
        if self.generated_patches:
            return self.generated_patches[-1]
        
        return SecurityPatch(
            patch_id=f"PATCH-{len(self.generated_patches) + 1:04d}",
            vulnerability_id=vulnerability.get("vuln_id", "unknown"),
            file_path=vulnerability.get("file_path", "unknown"),
            original_code=vulnerability.get("code_snippet", ""),
            patched_code="// Patch generation failed - manual review required",
            patch_description="Automatic patch generation failed",
            confidence=0.0,
            patch_type="workaround",
            test_cases=[],
            notes="Manual intervention required"
        )
    
    async def generate_patches(self, vulnerabilities: List[Dict[str, Any]]) -> List[SecurityPatch]:
        patches = []
        for vuln in vulnerabilities:
            patch = await self.generate_patch(vuln)
            patches.append(patch)
        return patches
    
    def get_generated_patches(self) -> List[SecurityPatch]:
        return self.generated_patches.copy()
    
    def get_patch_by_vuln_id(self, vuln_id: str) -> Optional[SecurityPatch]:
        for patch in self.generated_patches:
            if patch.vulnerability_id == vuln_id:
                return patch
        return None
    
    def clear_patches(self):
        self.generated_patches.clear()
