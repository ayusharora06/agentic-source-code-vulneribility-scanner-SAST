"""
Branch Flipper Agent - LLM-powered fuzzing input generation for branch coverage
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .agent_base import AgentBase


@dataclass
class BranchTarget:
    branch_id: str
    file_path: str
    line_number: int
    condition: str
    current_value: bool
    target_value: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch_id": self.branch_id,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "condition": self.condition,
            "current_value": self.current_value,
            "target_value": self.target_value
        }


@dataclass
class FlipInput:
    input_id: str
    branch_id: str
    input_bytes: bytes
    input_description: str
    strategy: str
    constraints: List[str]
    confidence: float
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_id": self.input_id,
            "branch_id": self.branch_id,
            "input_hex": self.input_bytes.hex() if self.input_bytes else None,
            "input_description": self.input_description,
            "strategy": self.strategy,
            "constraints": self.constraints,
            "confidence": self.confidence,
            "created_at": self.created_at
        }


class BranchFlipperAgent(AgentBase):
    
    def __init__(self, agent_id: str = "branch_flipper", model: str = "gpt-4o-mini", **kwargs):
        self.flip_inputs: List[FlipInput] = []
        self._branch_context: Dict[str, Any] = {}
        self._source_code: str = ""
        super().__init__(agent_id, model, temperature=0.3, **kwargs)
    
    @property
    def system_prompt(self) -> str:
        return """You are a fuzzing expert helping to achieve better code coverage.

Your job is to:
1. Analyze uncovered code branches
2. Understand the conditions required to reach them
3. Generate specific inputs that will flip the branch

Strategies:
- For numeric comparisons: calculate boundary values
- For string comparisons: craft matching strings
- For NULL checks: provide null or valid pointers
- For size checks: calculate exact sizes needed
- For magic values: identify and include them

Generate minimal, targeted inputs that specifically trigger the target branch."""

    def _register_tools(self) -> None:
        self.register_tool(
            name="get_branch_context",
            func=self._get_branch_context,
            description="Get the branch and source code context",
            parameters={}
        )
        
        self.register_tool(
            name="analyze_condition",
            func=self._analyze_condition,
            description="Analyze what's needed to satisfy a condition",
            parameters={
                "condition": {"type": "string", "description": "The condition expression"},
                "target_value": {"type": "boolean", "description": "Whether condition should be true or false"}
            }
        )
        
        self.register_tool(
            name="submit_flip_input",
            func=self._submit_flip_input,
            description="Submit an input designed to flip the branch",
            parameters={
                "input_hex": {"type": "string", "description": "Hex-encoded input bytes"},
                "input_description": {"type": "string", "description": "Human-readable description of the input"},
                "strategy": {"type": "string", "description": "Strategy used: boundary, magic_value, null, overflow, etc."},
                "constraints": {"type": "array", "items": {"type": "string"}, "description": "Constraints this input satisfies"},
                "confidence": {"type": "number", "description": "Confidence score 0.0-1.0"}
            }
        )
        
        self.register_tool(
            name="suggest_mutation",
            func=self._suggest_mutation,
            description="Suggest a mutation to an existing input",
            parameters={
                "base_input_hex": {"type": "string", "description": "Base input to mutate"},
                "mutation_type": {"type": "string", "description": "Type: bit_flip, insert, delete, replace"},
                "offset": {"type": "integer", "description": "Byte offset to mutate"},
                "reason": {"type": "string", "description": "Why this mutation might help"}
            }
        )

    def _get_branch_context(self) -> Dict[str, Any]:
        return {
            "branch": self._branch_context,
            "source_code": self._source_code[:2000]
        }

    def _analyze_condition(self, condition: str, target_value: bool) -> str:
        need = "true" if target_value else "false"
        return f"To make '{condition}' evaluate to {need}, analyze the variables and operators involved."

    def _submit_flip_input(
        self,
        input_hex: str = "",
        input_description: str = "",
        strategy: str = "unknown",
        constraints: List[str] = None,
        confidence: float = 0.5
    ) -> str:
        constraints = constraints or []
        try:
            input_bytes = bytes.fromhex(input_hex) if input_hex else b""
        except ValueError:
            input_bytes = input_hex.encode() if input_hex else b""
        
        flip_input = FlipInput(
            input_id=f"flip_{len(self.flip_inputs) + 1}_{int(time.time())}",
            branch_id=self._branch_context.get("branch_id", "unknown"),
            input_bytes=input_bytes,
            input_description=input_description,
            strategy=strategy,
            constraints=constraints,
            confidence=confidence
        )
        self.flip_inputs.append(flip_input)
        return f"Input submitted: {strategy} strategy, confidence {confidence:.0%}"

    def _suggest_mutation(self, base_input_hex: str, mutation_type: str, offset: int, reason: str) -> str:
        return f"Mutation suggested: {mutation_type} at offset {offset} - {reason}"

    async def generate_flip_input(
        self,
        branch: Dict[str, Any],
        source_code: str,
        existing_inputs: List[bytes] = None
    ) -> List[FlipInput]:
        self.flip_inputs = []
        self._branch_context = branch
        self._source_code = source_code
        
        existing_str = ""
        if existing_inputs:
            existing_str = f"\n\nExisting corpus inputs (hex):\n"
            for i, inp in enumerate(existing_inputs[:5]):
                existing_str += f"- Input {i+1}: {inp.hex()}\n"
        
        prompt = f"""Generate an input to flip this uncovered branch:

Branch: Line {branch.get('line_number', 'unknown')}
Condition: {branch.get('condition', 'unknown')}
Currently evaluates to: {branch.get('current_value', 'unknown')}
Need it to evaluate to: {branch.get('target_value', 'unknown')}

Source code context:
```
{source_code[:1500]}
```
{existing_str}

Instructions:
1. Use get_branch_context to review the details
2. Use analyze_condition to understand what's needed
3. Use submit_flip_input to provide your crafted input
4. Optionally use suggest_mutation to modify existing inputs"""

        await self.run(prompt)
        return self.flip_inputs

    def get_results(self) -> Dict[str, Any]:
        return {
            "branch_id": self._branch_context.get("branch_id"),
            "inputs": [i.to_dict() for i in self.flip_inputs],
            "total_generated": len(self.flip_inputs)
        }
