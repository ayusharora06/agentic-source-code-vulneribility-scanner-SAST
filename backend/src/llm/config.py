"""
LLM Configuration - API keys and model settings
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LLMConfig:
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    default_model: str = "gpt-4o-mini"
    fallback_models: List[str] = field(default_factory=lambda: [
        "gpt-4o-mini",
        "claude-3-haiku-20240307",
        "gemini/gemini-1.5-flash"
    ])
    
    temperature: float = 0.1
    max_tokens: int = 4096
    
    max_concurrent_requests: int = 10
    request_timeout: int = 120
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        return cls(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            default_model=os.getenv('DEFAULT_LLM_MODEL', 'gpt-4o-mini'),
            temperature=float(os.getenv('LLM_TEMPERATURE', '0.1')),
            max_tokens=int(os.getenv('LLM_MAX_TOKENS', '4096')),
        )
    
    def get_available_models(self) -> List[str]:
        models = []
        if self.openai_api_key:
            models.extend(['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'])
        if self.anthropic_api_key:
            models.extend(['claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307'])
        if self.google_api_key:
            models.extend(['gemini/gemini-1.5-pro', 'gemini/gemini-1.5-flash'])
        return models
    
    def has_any_key(self) -> bool:
        return any([self.openai_api_key, self.anthropic_api_key, self.google_api_key])


_config: Optional[LLMConfig] = None


def get_llm_config() -> LLMConfig:
    global _config
    if _config is None:
        _config = LLMConfig.from_env()
    return _config


MODEL_COSTS = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    "gemini/gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini/gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
}
