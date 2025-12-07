"""
LLM Client - Unified interface for calling LLMs via litellm
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import litellm
from litellm import acompletion

from .config import get_llm_config, MODEL_COSTS, LLMConfig

logger = logging.getLogger(__name__)

litellm.set_verbose = False


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Dict[str, int]
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: str = "stop"
    latency: float = 0.0
    cost: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "tool_calls": self.tool_calls,
            "finish_reason": self.finish_reason,
            "latency": self.latency,
            "cost": self.cost
        }


@dataclass
class LLMClient:
    config: LLMConfig = field(default_factory=get_llm_config)
    total_cost: float = 0.0
    total_requests: int = 0
    _semaphore: Optional[asyncio.Semaphore] = None
    
    def __post_init__(self):
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        self._setup_api_keys()
    
    def _setup_api_keys(self):
        import os
        if self.config.openai_api_key:
            os.environ['OPENAI_API_KEY'] = self.config.openai_api_key
        if self.config.anthropic_api_key:
            os.environ['ANTHROPIC_API_KEY'] = self.config.anthropic_api_key
        if self.config.google_api_key:
            os.environ['GOOGLE_API_KEY'] = self.config.google_api_key
    
    async def completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        model = model or self.config.default_model
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens
        
        async with self._semaphore:
            start_time = time.time()
            
            try:
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "timeout": self.config.request_timeout,
                }
                
                if tools:
                    kwargs["tools"] = tools
                if tool_choice:
                    kwargs["tool_choice"] = tool_choice
                
                response = await acompletion(**kwargs)
                
                latency = time.time() - start_time
                
                message = response.choices[0].message
                content = message.content or ""
                
                tool_calls = None
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    tool_calls = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
                
                cost = self._calculate_cost(model, usage)
                self.total_cost += cost
                self.total_requests += 1
                
                logger.info(f"LLM call: model={model}, tokens={usage['total_tokens']}, cost=${cost:.4f}, latency={latency:.2f}s")
                
                return LLMResponse(
                    content=content,
                    model=model,
                    usage=usage,
                    tool_calls=tool_calls,
                    finish_reason=response.choices[0].finish_reason,
                    latency=latency,
                    cost=cost
                )
                
            except Exception as e:
                logger.error(f"LLM error: {e}")
                
                for fallback_model in self.config.fallback_models:
                    if fallback_model != model:
                        try:
                            logger.info(f"Trying fallback model: {fallback_model}")
                            return await self.completion(
                                messages=messages,
                                model=fallback_model,
                                temperature=temperature,
                                max_tokens=max_tokens,
                                tools=tools,
                                tool_choice=tool_choice
                            )
                        except:
                            continue
                
                raise
    
    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        if model not in MODEL_COSTS:
            return 0.0
        
        costs = MODEL_COSTS[model]
        input_cost = (usage["prompt_tokens"] / 1000) * costs["input"]
        output_cost = (usage["completion_tokens"] / 1000) * costs["output"]
        return input_cost + output_cost
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_cost": self.total_cost,
            "total_requests": self.total_requests,
            "available_models": self.config.get_available_models()
        }


_client: Optional[LLMClient] = None


def get_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


async def completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: Optional[str] = None,
) -> LLMResponse:
    client = get_client()
    return await client.completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        tools=tools,
        tool_choice=tool_choice
    )
