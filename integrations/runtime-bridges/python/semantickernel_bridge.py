"""
Microsoft Semantic Kernel Bridge for AGenNext Runtime Core.

Provides integration with Microsoft Semantic Kernel for AI orchestration,
planners, memory, and skills execution.
"""

import json
import time
from typing import Any, Dict, Generator, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class KernelType(Enum):
    CHAT = "chat"
    COMPLETION = "completion"
    PLANNER = "planner"
    RAG = "rag"
    STREAMING = "streaming"


class SkillType(Enum):
    PROMPT = "prompt"
    PYTHON = "python"
    NATIVE = "native"
    SEMANTIC = "semantic"


@dataclass
class Skill:
    """Semantic Kernel skill definition."""
    name: str
    skill_type: SkillType = SkillType.SEMANTIC
    description: str = ""
    functions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KernelConfig:
    """Configuration for a Semantic Kernel."""
    kernel_type: KernelType = KernelType.CHAT
    model_id: str = "gpt-4"
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    service_id: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    skills: List[Skill] = field(default_factory=list)
    memory_config: Optional[Dict[str, Any]] = None


class SemanticKernelBridge:
    """Bridge for Microsoft Semantic Kernel execution."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.kernels: Dict[str, KernelConfig] = {}
        self.skills: Dict[str, Skill] = {}
        self.chat_history: Dict[str, List[Dict[str, str]] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._kernel: Optional[Any] = None
        
    def init(self, config: Dict[str, Any]) -> None:
        """Initialize the Semantic Kernel bridge."""
        self.config = config
        
        # Try to import semantic-kernel
        try:
            from semantic_kernel import Kernel
            from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
            
            self._kernel = Kernel()
            
            # Add chat service
            model = config.get("model_id", "gpt-4")
            api_key = config.get("api_key")
            
            if api_key:
                chat_service = OpenAIChatCompletion(
                    ai_model_id=model,
                    api_key=api_key,
                )
                self._kernel.add_service(chat_service)
                
        except ImportError:
            self._kernel = None
            
    def _create_prompt_skill(self, name: str, prompt_template: str, description: str = "") -> Skill:
        """Create a prompt-based skill."""
        return Skill(
            name=name,
            skill_type=SkillType.PROMPT,
            description=description,
            functions={
                "execute": {
                    "prompt": prompt_template,
                    "description": description,
                }
            }
        )
        
    def _create_native_skill(self, name: str, func: Any, description: str = "") -> Skill:
        """Create a native (Python function) skill."""
        return Skill(
            name=name,
            skill_type=SkillType.NATIVE,
            description=description,
            functions={
                "execute": func,
                "description": description,
            }
        )
        
    def invoke(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Semantic Kernel action."""
        action_type = action.get("type", "invoke")
        
        if action_type == "kernel_create":
            # Create a new kernel instance
            kernel_id = action.get("kernel_id", f"kernel_{len(self.kernels)}")
            kernel_config = action.get("config", {})
            
            kernel_type = KernelType(kernel_config.get("type", "chat"))
            self.kernels[kernel_id] = KernelConfig(
                kernel_type=kernel_type,
                model_id=kernel_config.get("model_id", "gpt-4"),
                temperature=kernel_config.get("temperature", 0.7),
                max_tokens=kernel_config.get("max_tokens", 2048),
            )
            
            self.chat_history[kernel_id] = []
            
            return {
                "status": "created",
                "kernel_id": kernel_id,
                "kernel_type": kernel_type.value,
            }
            
        elif action_type == "invoke":
            # Invoke kernel
            kernel_id = action.get("kernel_id", "default")
            prompt = action.get("prompt", "")
            
            if kernel_id not in self.kernels:
                kernel_id = "default"
                self.kernels[kernel_id] = KernelConfig()
                self.chat_history[kernel_id] = []
                
            if not self._kernel:
                # Mock response
                return {
                    "status": "ok",
                    "response": f"[Semantic Kernel Mock] {prompt}",
                    "kernel_id": kernel_id,
                }
                
            try:
                # Execute via kernel
                from semantic_kernel import Kernel
                from semantic_kernel.functions import KernelArguments
                
                arguments = KernelArguments(prompt=prompt)
                result = await self._kernel.invoke_prompt(prompt=prompt, arguments=arguments)
                
                # Add to history
                self.chat_history[kernel_id].append({
                    "role": "user",
                    "content": prompt,
                })
                self.chat_history[kernel_id].append({
                    "role": "assistant",
                    "content": str(result),
                })
                
                self._event_history.append({
                    "type": "invoke",
                    "kernel_id": kernel_id,
                    "prompt": prompt,
                    "response": str(result),
                })
                
                return {
                    "status": "ok",
                    "response": str(result),
                    "kernel_id": kernel_id,
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "kernel_id": kernel_id,
                }
                
        elif action_type == "skill_register":
            # Register a skill
            skill_name = action.get("skill_name")
            skill_definition = action.get("skill", {})
            
            skill = Skill(
                name=skill_name,
                skill_type=SkillType(skill_definition.get("type", "semantic")),
                description=skill_definition.get("description", ""),
                functions=skill_definition.get("functions", {}),
            )
            
            self.skills[skill_name] = skill
            
            return {
                "status": "registered",
                "skill_name": skill_name,
            }
            
        elif action_type == "skill_execute":
            # Execute a skill function
            skill_name = action.get("skill_name")
            function_name = action.get("function_name", "execute")
            arguments = action.get("arguments", {})
            
            if skill_name not in self.skills:
                return {"status": "error", "error": "Skill not found"}
                
            skill = self.skills[skill_name]
            
            try:
                func = skill.functions.get(function_name)
                if callable(func):
                    result = func(arguments)
                elif isinstance(func, dict) and "prompt" in func:
                    result = func["prompt"].format(**arguments)
                else:
                    result = str(func)
                    
                return {
                    "status": "ok",
                    "response": result,
                    "skill_name": skill_name,
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "skill_name": skill_name,
                }
                
        elif action_type == "planner_create":
            # Create a planner
            goal = action.get("goal", "")
            plan_config = action.get("config", {})
            
            if not self._kernel:
                return {
                    "status": "ok",
                    "plan": [
                        {"step": 1, "action": "mock_action", "reasoning": "Mock planning step"}
                    ],
                    "goal": goal,
                }
                
            try:
                from semantic_kernel.planning import SequentialPlanner
                
                planner = SequentialPlanner(self._kernel)
                plan = await planner.create_plan(goal)
                
                return {
                    "status": "ok",
                    "plan": [
                        {"step": i + 1, "action": str(step), "reasoning": "Planned"}
                        for i, step in enumerate(plan.steps)
                    ],
                    "goal": goal,
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                }
                
        elif action_type == "planner_execute":
            # Execute a plan
            plan = action.get("plan", [])
            
            results = []
            for step in plan:
                # Execute each step
                results.append({
                    "step": step.get("step"),
                    "status": "completed",
                    "result": step.get("action"),
                })
                
            return {
                "status": "completed",
                "results": results,
            }
            
        elif action_type == "memory_store":
            # Store in memory
            collection = action.get("collection", "default")
            text = action.get("text", "")
            memory_id = f"mem_{len(self._event_history)}"
            
            self._event_history.append({
                "type": "memory_store",
                "collection": collection,
                "memory_id": memory_id,
                "text": text,
            })
            
            return {
                "status": "stored",
                "memory_id": memory_id,
                "collection": collection,
            }
            
        elif action_type == "memory_recall":
            # Recall from memory
            query = action.get("query", "")
            collection = action.get("collection", "default")
            
            # Simple recall (in production, use vector search)
            memories = [
                e for e in self._event_history
                if e.get("type") == "memory_store"
                and e.get("collection") == collection
            ]
            
            return {
                "status": "ok",
                "query": query,
                "memories": [m.get("text") for m in memories],
            }
            
        elif action_type == "chat_history_get":
            # Get chat history
            kernel_id = action.get("kernel_id", "default")
            messages = self.chat_history.get(kernel_id, [])
            
            return {
                "status": "ok",
                "kernel_id": kernel_id,
                "messages": messages,
            }
            
        elif action_type == "chat_history_clear":
            # Clear chat history
            kernel_id = action.get("kernel_id", "default")
            self.chat_history[kernel_id] = []
            
            return {
                "status": "ok",
                "kernel_id": kernel_id,
            }
            
        return {"status": "unknown_action", "action": action}
        
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        """Stream kernel events."""
        # TODO: Implement streaming for semantic kernel
        for event in self._event_history[-10:]:
            yield event
            
    def close(self) -> None:
        """Clean up resources."""
        self.kernels.clear()
        self.skills.clear()
        self.chat_history.clear()
        self._event_history.clear()


# FastAPI integration
def create_semantic_kernel_app(bridge: SemanticKernelBridge):
    """Create a FastAPI app for Semantic Kernel bridge."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    
    app = FastAPI(title="Semantic Kernel Bridge", version="0.1.0")
    
    class InvokeInput(BaseModel):
        type: str = "invoke"
        kernel_id: str = "default"
        prompt: str = ""
        arguments: Dict[str, Any] = {}
        
    @app.post("/invoke")
    def invoke(req: InvokeInput):
        return bridge.invoke(req.model_dump(exclude={"type"}))
        
    @app.get("/kernels")
    def list_kernels():
        return {"kernels": list(bridge.kernels.keys())}
        
    @app.get("/skills")
    def list_skills():
        return {"skills": list(bridge.skills.keys())}
        
    @app.get("/stream")
    def stream():
        return {"events": list(bridge.stream())}
        
    @app.get("/chat/{kernel_id}")
    def get_chat(kernel_id: str):
        return bridge.invoke({
            "type": "chat_history_get",
            "kernel_id": kernel_id,
        })
        
    return app