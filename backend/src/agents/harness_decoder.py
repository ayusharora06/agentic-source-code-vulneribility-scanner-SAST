"""
Harness Decoder Agent - LLM-powered fuzzing input decoder and encoder
"""

import time
import struct
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .agent_base import AgentBase


@dataclass
class DecodedField:
    name: str
    field_type: str
    offset: int
    size: int
    value: Any
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.field_type,
            "offset": self.offset,
            "size": self.size,
            "value": str(self.value),
            "description": self.description
        }


@dataclass
class InputFormat:
    format_id: str
    name: str
    fields: List[DecodedField]
    total_size: int
    description: str
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "format_id": self.format_id,
            "name": self.name,
            "fields": [f.to_dict() for f in self.fields],
            "total_size": self.total_size,
            "description": self.description,
            "created_at": self.created_at
        }


class HarnessDecoderAgent(AgentBase):
    
    def __init__(self, agent_id: str = "harness_decoder", model: str = "gpt-4o-mini", **kwargs):
        self.formats: List[InputFormat] = []
        self._input_bytes: bytes = b""
        self._harness_code: str = ""
        super().__init__(agent_id, model, temperature=0.1, **kwargs)
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert at reverse engineering input formats for fuzzing harnesses.

Your job is to:
1. Analyze raw input bytes and harness code
2. Identify the structure and meaning of input fields
3. Create a human-readable format specification

Look for:
- Length prefixes (often first 2-4 bytes)
- Magic numbers/signatures
- Null-terminated strings
- Fixed-size fields (int32, int64, floats)
- Nested structures
- Arrays with count prefixes

Use the tools to decode and document the format."""

    def _register_tools(self) -> None:
        self.register_tool(
            name="get_input_context",
            func=self._get_input_context,
            description="Get the raw input and harness code",
            parameters={}
        )
        
        self.register_tool(
            name="read_bytes",
            func=self._read_bytes,
            description="Read bytes from the input at a specific offset",
            parameters={
                "offset": {"type": "integer", "description": "Byte offset to start reading"},
                "length": {"type": "integer", "description": "Number of bytes to read"},
                "format": {"type": "string", "description": "Format: hex, uint32_le, uint16_le, int32_le, string, raw"}
            }
        )
        
        self.register_tool(
            name="define_field",
            func=self._define_field,
            description="Define a field in the input format",
            parameters={
                "name": {"type": "string", "description": "Field name"},
                "field_type": {"type": "string", "description": "Type: uint32, uint16, uint8, int32, string, bytes, array"},
                "offset": {"type": "integer", "description": "Byte offset"},
                "size": {"type": "integer", "description": "Size in bytes"},
                "description": {"type": "string", "description": "What this field represents"}
            }
        )
        
        self.register_tool(
            name="submit_format",
            func=self._submit_format,
            description="Submit the complete format specification",
            parameters={
                "name": {"type": "string", "description": "Format name"},
                "description": {"type": "string", "description": "Overall format description"}
            }
        )

    def _get_input_context(self) -> Dict[str, Any]:
        return {
            "input_hex": self._input_bytes.hex(),
            "input_length": len(self._input_bytes),
            "harness_code": self._harness_code[:1500] if self._harness_code else None
        }

    def _read_bytes(self, offset: int, length: int, format: str = "hex") -> str:
        if offset >= len(self._input_bytes):
            return f"Error: offset {offset} beyond input length {len(self._input_bytes)}"
        
        end = min(offset + length, len(self._input_bytes))
        data = self._input_bytes[offset:end]
        
        if format == "hex":
            return data.hex()
        elif format == "uint32_le" and len(data) >= 4:
            return str(struct.unpack("<I", data[:4])[0])
        elif format == "uint16_le" and len(data) >= 2:
            return str(struct.unpack("<H", data[:2])[0])
        elif format == "int32_le" and len(data) >= 4:
            return str(struct.unpack("<i", data[:4])[0])
        elif format == "string":
            try:
                null_pos = data.find(b'\x00')
                if null_pos >= 0:
                    data = data[:null_pos]
                return data.decode('utf-8', errors='replace')
            except:
                return data.hex()
        else:
            return data.hex()

    def _define_field(self, name: str = "field", field_type: str = "bytes", offset: int = 0, size: int = 0, description: str = "") -> str:
        value = self._read_bytes(offset, size, "hex")
        
        field = DecodedField(
            name=name,
            field_type=field_type,
            offset=offset,
            size=size,
            value=value,
            description=description
        )
        
        if not hasattr(self, '_pending_fields'):
            self._pending_fields = []
        self._pending_fields.append(field)
        
        return f"Field defined: {name} ({field_type}) at offset {offset}, size {size}"

    def _submit_format(self, name: str, description: str) -> str:
        fields = getattr(self, '_pending_fields', [])
        
        format_spec = InputFormat(
            format_id=f"fmt_{int(time.time())}",
            name=name,
            fields=fields,
            total_size=len(self._input_bytes),
            description=description
        )
        self.formats.append(format_spec)
        self._pending_fields = []
        
        return f"Format submitted: {name} with {len(fields)} fields"

    async def decode_input(self, input_bytes: bytes, harness_code: str = "") -> InputFormat:
        self.formats = []
        self._pending_fields = []
        self._input_bytes = input_bytes
        self._harness_code = harness_code
        
        prompt = f"""Decode this fuzzing input and identify its structure:

Input (hex): {input_bytes.hex()}
Input length: {len(input_bytes)} bytes

{"Harness code:" if harness_code else ""}
```
{harness_code[:1000] if harness_code else "No harness code provided"}
```

Instructions:
1. Use get_input_context to see the full input
2. Use read_bytes to examine specific parts
3. Use define_field for each field you identify
4. Use submit_format when done with the specification"""

        await self.run(prompt)
        return self.formats[-1] if self.formats else None

    async def infer_format(self, samples: List[bytes]) -> InputFormat:
        self.formats = []
        self._pending_fields = []
        self._input_bytes = samples[0] if samples else b""
        self._harness_code = ""
        
        samples_str = "\n".join([f"Sample {i+1}: {s.hex()}" for i, s in enumerate(samples[:5])])
        
        prompt = f"""Analyze these input samples to infer the format:

{samples_str}

Instructions:
1. Compare the samples to find common patterns
2. Identify fixed fields vs variable fields
3. Use define_field for each identified field
4. Use submit_format with your findings"""

        await self.run(prompt)
        return self.formats[-1] if self.formats else None

    def get_results(self) -> Dict[str, Any]:
        return {
            "formats": [f.to_dict() for f in self.formats],
            "total_decoded": len(self.formats)
        }
