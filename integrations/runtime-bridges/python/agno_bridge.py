"""
Agno (agno.ai) Bridge for AGenNext Runtime Core.

Provides integration with Agno for lightweight agentic AI,
memory management, and tool execution.
"""

import json
import time
from typing import Any, Callable, Dict, Generator, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class AgnoModel(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    GOOGLE = "google"


class MemoryType(Enum):
    CONVERSATION = "conversation"
    SEMANTIC = "semantic"
    WORKING = "working"


@dataclass
class Tool:
    """Agno tool definition."""
    name: str
    description: str
    func: Optional[Callable] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Instruction:
    """Agno instruction."""
    content: str
    source: str = "user"


@dataclass
class AgentConfig:
    """Agno agent configuration."""
    model: str = "gpt-4"
    model_provider: str = "openai"
    markdown: bool = True
    multi_modal: bool = False
    tools: List[Tool] = field(default_factory=list)
    show_tool_calls: bool = False
    show_reasoning: bool = False
    memory: bool = True
    instructions: List[Instruction] = field(default_factory=list)


class AgnoBridge:
    """Bridge for Agno (agno.ai) execution."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.agents: Dict[str, AgentConfig] = {}
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.memories: Dict[str, List[str]] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._agno_enabled: bool = False
        
    def init(self, config: Dict[str, Any]) -> None:
        """Initialize the Agno bridge."""
        self.config = config
        
    def _format_agent_response(self, content: str, reasoning: Optional[str] = None) -> Dict[str, Any]:
        """Format agent response in Agno style."""
        return {
            "content": content,
            "reasoning": reasoning,
            "tool_calls": [],
            "metrics": {
                "tokens": len(content.split()),
                "latency_ms": 0,
            },
        }
        
    def invoke(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Agno action."""
        action_type = action.get("type", "invoke")
        
        if action_type == "agent_create":
            # Create an agent
            agent_id = action.get("agent_id", f"agent_{len(self.agents)}")
            agent_config = action.get("config", {})
            
            config = AgentConfig(
                model=agent_config.get("model", "gpt-4"),
                model_provider=agent_config.get("provider", "openai"),
                markdown=agent_config.get("markdown", True),
                multi_modal=agent_config.get("multi_modal", False),
                show_tool_calls=agent_config.get("show_tool_calls", False),
                show_reasoning=agent_config.get("show_reasoning", False),
                memory=agent_config.get("memory", True),
            )
            
            self.agents[agent_id] = config
            self.conversations[agent_id] = []
            self.memories[agent_id] = []
            
            return {
                "status": "created",
                "agent_id": agent_id,
                "model": config.model,
                "provider": config.model_provider,
            }
            
        elif action_type == "invoke":
            # Invoke agent
            agent_id = action.get("agent_id", "default")
            message = action.get("message", "")
            
            if agent_id not in self.agents:
                agent_id = "default"
                self.agents[agent_id] = AgentConfig()
                self.conversations[agent_id] = []
                self.memories[agent_id] = []
                
            agent_config = self.agents[agent_id]
            
            # Add to conversation
            self.conversations[agent_id].append({
                "role": "user",
                "content": message,
                "timestamp": time.time(),
            })
            
            # Mock response (in production, call actual Agno)
            response = self._format_agent_response(
                f"[Agno] {message}",
                reasoning="Processing request..." if agent_config.show_reasoning else None,
            )
            
            if agent_config.show_tool_calls:
                response["tool_calls"] = [
                    {"tool": "search", "args": {"query": message}}
                ]
            
            # Add assistant response
            self.conversations[agent_id].append({
                "role": "assistant",
                "content": response["content"],
                "timestamp": time.time(),
            })
            
            # Store in memory if enabled
            if agent_config.memory:
                self.memories[agent_id].append(
                    f"User: {message}\nAssistant: {response['content']}"
                )
            
            self._event_history.append({
                "type": "invoke",
                "agent_id": agent_id,
                "message": message,
                "response": response["content"],
            })
            
            return {
                "status": "ok",
                "response": response,
                "agent_id": agent_id,
            }
            
        elif action_type == "chat":
            # Chat (alias for invoke)
            return self.invoke({
                "type": "invoke",
                "agent_id": action.get("agent_id", "default"),
                "message": action.get("message", ""),
            })
            
        elif action_type == "stream":
            # Stream response
            agent_id = action.get("agent_id", "default")
            message = action.get("message", "")
            
            for word in f"[Agno Stream] {message}".split():
                yield {"type": "chunk", "content": word + " "}
                
        elif action_type == "tool_register":
            # Register a tool
            tool_def = action.get("tool", {})
            tool_id = tool_def.get("name")
            
            if tool_id:
                agent_id = action.get("agent_id", "default")
                
                if agent_id not in self.agents:
                    self.agents[agent_id] = AgentConfig()
                    
                tool = Tool(
                    name=tool_id,
                    description=tool_def.get("description", ""),
                    parameters=tool_def.get("parameters", {}),
                )
                
                self.agents[agent_id].tools.append(tool)
                
                return {
                    "status": "registered",
                    "tool": tool_id,
                    "agent_id": agent_id,
                }
            
        elif action_type == "tools_list":
            # List tools for agent
            agent_id = action.get("agent_id", "default")
            
            if agent_id not in self.agents:
                return {"status": "ok", "tools": []}
                
            return {
                "status": "ok",
                "tools": [
                    {"name": t.name, "description": t.description}
                    for t in self.agents[agent_id].tools
                ],
            }
            
        elif action_type == "memory_get":
            # Get agent memory
            agent_id = action.get("agent_id", "default")
            memories = self.memories.get(agent_id, [])
            
            return {
                "status": "ok",
                "agent_id": agent_id,
                "memories": memories,
            }
            
        elif action_type == "memory_search":
            # Search memory
            agent_id = action.get("agent_id", "default")
            query = action.get("query", "")
            
            memories = self.memories.get(agent_id, [])
            results = [m for m in memories if query.lower() in m.lower()]
            
            return {
                "status": "ok",
                "query": query,
                "results": results,
            }
            
        elif action_type == "memory_clear":
            # Clear memory
            agent_id = action.get("agent_id", "default")
            self.memories[agent_id] = []
            
            return {
                "status": "ok",
                "agent_id": agent_id,
            }
            
        elif action_type == "conversation_get":
            # Get conversation
            agent_id = action.get("agent_id", "default")
            messages = self.conversations.get(agent_id, [])
            
            return {
                "status": "ok",
                "agent_id": agent_id,
                "messages": messages[-20:],  # Last 20 messages
            }
            
        elif action_type == "conversation_clear":
            # Clear conversation
            agent_id = action.get("agent_id", "default")
            self.conversations[agent_id] = []
            
            return {
                "status": "ok",
                "agent_id": agent_id,
            }
            
        elif action_type == "agents_list":
            # List all agents
            return {
                "status": "ok",
                "agents": [
                    {
                        "id": agent_id,
                        "model": config.model,
                        "provider": config.model_provider,
                        "has_memory": config.memory,
                    }
                    for agent_id, config in self.agents.items()
                ],
            }
            
        return {"status": "unknown_action", "action": action}
        
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        """Stream agent response."""
        for event in self._event_history[-10:]:
            yield event
            
    def close(self) -> None:
        """Clean up resources."""
        self.agents.clear()
        self.conversations.clear()
        self.memories.clear()
        self._event_history.clear()


# FastAPI integration
def create_agno_app(bridge: AgnoBridge):
    """Create a FastAPI app for Agno bridge."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from typing import Optional, List, Dict, Any
    
    app = FastAPI(title="Agno Bridge", version="0.1.0")
    
    class CreateAgentInput(BaseModel):
        agent_id: Optional[str] = None
        config: Dict[str, Any] = {}
        
    class ChatInput(BaseModel):
        agent_id: str = "default"
        message: str = ""
        
    class ToolInput(BaseModel):
        agent_id: str = "default"
        tool: Dict[str, Any] = {}
        
    @app.post("/agents/create")
    def create_agent(req: CreateAgentInput):
        return bridge.invoke({
            "type": "agent_create",
            "agent_id": req.agent_id,
            "config": req.config,
        })
        
    @app.post("/chat")
    def chat(req: ChatInput):
        return bridge.invoke({
            "type": "chat",
            "agent_id": req.agent_id,
            "message": req.message,
        })
        
    @app.post("/invoke")
    def invoke(req: ChatInput):
        return bridge.invoke({
            "type": "invoke",
            "agent_id": req.agent_id,
            "message": req.message,
        })
        
    @app.get("/agents")
    def list_agents():
        return bridge.invoke({"type": "agents_list"})
        
    @app.get("/agents/{agent_id}/memory")
    def get_memory(agent_id: str):
        return bridge.invoke({
            "type": "memory_get",
            "agent_id": agent_id,
        })
        
    @app.post("/agents/{agent_id}/memory/clear")
    def clear_memory(agent_id: str):
        return bridge.invoke({
            "type": "memory_clear",
            "agent_id": agent_id,
        })
        
    @app.get("/agents/{agent_id}/conversation")
    def get_conversation(agent_id: str):
        return bridge.invoke({
            "type": "conversation_get",
            "agent_id": agent_id,
        })
        
    @app.get("/stream")
    def stream():
        return {"events": list(bridge.stream())}
        
    return app