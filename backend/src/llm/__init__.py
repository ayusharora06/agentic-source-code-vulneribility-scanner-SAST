"""
LLM integration module - Unified API for OpenAI, Anthropic, Google
"""

from .client import LLMClient, LLMResponse, completion, get_client
from .config import LLMConfig, get_llm_config

__all__ = [
    'LLMClient',
    'LLMResponse',
    'completion', 
    'get_client',
    'LLMConfig',
    'get_llm_config'
]
