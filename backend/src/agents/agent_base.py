"""
Agent Base - LLM-powered agent with tool support
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..llm import completion, LLMResponse, get_llm_config

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    success: bool = False
    error: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class AgentExecution:
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    status: AgentStatus = AgentStatus.IDLE
    iterations: int = 0
    tool_calls: List[ToolCall] = field(default_factory=list)
    total_cost: float = 0.0
    total_tokens: int = 0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status.value,
            "iterations": self.iterations,
            "tool_calls": len(self.tool_calls),
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "error": self.error
        }


class AgentBase(ABC):
    
    def __init__(
        self,
        agent_id: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        max_iterations: int = 10,
        **kwargs
    ):
        self.agent_id = agent_id
        self.model = model
        self.temperature = temperature
        self.max_iterations = max_iterations
        
        self.messages: List[Dict[str, Any]] = []
        self.execution: Optional[AgentExecution] = None
        self._tools: Dict[str, Callable] = {}
        self._tool_schemas: List[Dict[str, Any]] = []
        
        self._register_tools()
    
    @property
    def system_prompt(self) -> str:
        return "You are a helpful AI assistant."
    
    @abstractmethod
    def _register_tools(self) -> None:
        pass
    
    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: Dict[str, Any]
    ) -> None:
        self._tools[name] = func
        self._tool_schemas.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": list(parameters.keys())
                }
            }
        })
    
    def get_tools(self) -> List[Dict[str, Any]]:
        return self._tool_schemas
    
    async def run(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        self.execution = AgentExecution(status=AgentStatus.RUNNING)
        self.messages = [{"role": "system", "content": self.system_prompt}]
        
        if context:
            context_str = f"\n\nContext:\n```json\n{json.dumps(context, indent=2)}\n```"
            user_message = user_message + context_str
        
        self.messages.append({"role": "user", "content": user_message})
        
        try:
            result = await self._run_loop()
            self.execution.status = AgentStatus.COMPLETED
            self.execution.completed_at = time.time()
            return result
        except Exception as e:
            logger.error(f"Agent {self.agent_id} error: {e}")
            self.execution.status = AgentStatus.FAILED
            self.execution.error = str(e)
            self.execution.completed_at = time.time()
            raise
    
    async def _run_loop(self) -> str:
        for iteration in range(self.max_iterations):
            self.execution.iterations = iteration + 1
            
            response = await self._call_llm()
            
            self.execution.total_cost += response.cost
            self.execution.total_tokens += response.usage.get('total_tokens', 0)
            
            if response.tool_calls:
                tool_results = await self._execute_tools(response.tool_calls)
                
                self.messages.append({
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": response.tool_calls
                })
                
                for tool_call, result in zip(response.tool_calls, tool_results):
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(result) if not isinstance(result, str) else result
                    })
            else:
                self.messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                return response.content
        
        return self.messages[-1].get("content", "Max iterations reached")
    
    async def _call_llm(self) -> LLMResponse:
        tools = self.get_tools() if self._tools else None
        
        return await completion(
            messages=self.messages,
            model=self.model,
            temperature=self.temperature,
            tools=tools,
            tool_choice="auto" if tools else None
        )
    
    async def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Any]:
        results = []
        
        for tc in tool_calls:
            func_name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}
            
            call = ToolCall(
                id=tc["id"],
                name=func_name,
                arguments=args
            )
            
            start_time = time.time()
            
            try:
                if func_name in self._tools:
                    func = self._tools[func_name]
                    if asyncio.iscoroutinefunction(func):
                        result = await func(**args)
                    else:
                        result = func(**args)
                    
                    call.result = result
                    call.success = True
                else:
                    result = f"Unknown tool: {func_name}"
                    call.error = result
                    call.success = False
                
            except Exception as e:
                result = f"Tool error: {str(e)}"
                call.error = result
                call.success = False
                logger.error(f"Tool {func_name} error: {e}")
            
            call.execution_time = time.time() - start_time
            self.execution.tool_calls.append(call)
            results.append(result)
        
        return results
    
    def complete_execution(self, status: str = "completed", error: Optional[str] = None):
        if self.execution:
            self.execution.status = AgentStatus(status)
            self.execution.completed_at = time.time()
            if error:
                self.execution.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "model": self.model,
            "temperature": self.temperature,
            "status": self.execution.status.value if self.execution else "idle",
            "execution": self.execution.to_dict() if self.execution else None
        }
