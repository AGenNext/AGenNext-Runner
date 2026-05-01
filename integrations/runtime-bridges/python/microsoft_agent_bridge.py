"""
Microsoft Agent Framework Bridge for AGenNext Runtime Core.

Provides integration with Microsoft Agent Framework for building autonomous
agents with memory, tools, state management, and multi-agent orchestration.
"""

import json
import time
from typing import Any, Callable, Dict, Generator, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class AgentCapability(Enum):
    REASONING = "reasoning"
    PLANNING = "planning"
    MEMORY = "memory"
    TOOLS = "tools"
    OBSERVATION = "observation"


class MemoryType(Enum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    WORKING = "working"


@dataclass
class AgentSkill:
    """Skill definition for Microsoft Agent."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    handler: Optional[Callable] = None


@dataclass
class AgentMemory:
    """Memory configuration for agent."""
    memory_type: MemoryType = MemoryType.WORKING
    max_items: int = 100
    ttl_seconds: int = 3600


@dataclass
class AgentState:
    """Agent state."""
    status: str = "idle"
    current_task: Optional[str] = None
    step_count: int = 0
    last_update: float = field(default_factory=time.time)


class MicrosoftAgentBridge:
    """Bridge for Microsoft Agent Framework."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.memories: Dict[str, List[Dict[str, Any]]] = {}
        self.skills: Dict[str, AgentSkill] = {}
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self._event_history: List[Dict[str, Any]] = []
        
    def init(self, config: Dict[str, Any]) -> None:
        """Initialize the Microsoft Agent bridge."""
        self.config = config
        
    def _create_agent_state(self) -> AgentState:
        """Create new agent state."""
        return AgentState(
            status="initialized",
            step_count=0,
            last_update=time.time(),
        )
        
    def invoke(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Microsoft Agent action."""
        action_type = action.get("type", "invoke")
        
        if action_type == "agent_create":
            # Create an agent
            agent_id = action.get("agent_id", f"agent_{len(self.agents)}")
            agent_config = action.get("config", {})
            
            capabilities = agent_config.get("capabilities", ["reasoning", "tools"])
            
            self.agents[agent_id] = {
                "id": agent_id,
                "name": agent_config.get("name", agent_id),
                "description": agent_config.get("description", ""),
                "capabilities": capabilities,
                "state": self._create_agent_state(),
                "tools": agent_config.get("tools", []),
                "memory_config": agent_config.get("memory", {}),
            }
            
            self.memories[agent_id] = []
            self.conversations[agent_id] = []
            
            return {
                "status": "created",
                "agent_id": agent_id,
                "capabilities": capabilities,
            }
            
        elif action_type == "agent_invoke":
            # Invoke agent to process task
            agent_id = action.get("agent_id")
            task = action.get("task", "")
            
            if agent_id not in self.agents:
                return {"status": "error", "error": "Agent not found"}
                
            agent = self.agents[agent_id]
            agent_state = agent["state"]
            agent_state.status = "processing"
            agent_state.current_task = task
            agent_state.step_count += 1
            agent_state.last_update = time.time()
            
            # Process task based on capabilities
            result = self._process_task(agent, task)
            
            agent_state.status = "idle"
            agent_state.current_task = None
            
            # Store in memory
            self.memories[agent_id].append({
                "task": task,
                "result": result,
                "timestamp": time.time(),
            })
            
            self._event_history.append({
                "type": "agent_invoke",
                "agent_id": agent_id,
                "task": task,
                "result": result,
            })
            
            return {
                "status": "ok",
                "agent_id": agent_id,
                "result": result,
                "steps": agent_state.step_count,
            }
            
        elif action_type == "agent_stream":
            # Stream agent processing
            agent_id = action.get("agent_id")
            task = action.get("task", "")
            
            if agent_id not in self.agents:
                return {"status": "error", "error": "Agent not found"}
                
            agent = self.agents[agent_id]
            
            # Stream reasoning steps
            yield {"type": "reasoning", "content": f"Analyzing task: {task}"}
            yield {"type": "reasoning", "content": "Planning approach..."}
            yield {"type": "reasoning", "content": "Executing..."}
            yield {"type": "result", "content": f"[Agent {agent_id}] Completed: {task}"}
            
        elif action_type == "tool_register":
            # Register a tool
            tool_def = action.get("tool", {})
            tool_name = tool_def.get("name")
            
            if tool_name:
                self.skills[tool_name] = AgentSkill(
                    name=tool_name,
                    description=tool_def.get("description", ""),
                    parameters=tool_def.get("parameters", {}),
                )
                
                return {
                    "status": "registered",
                    "tool": tool_name,
                }
            
        elif action_type == "tool_execute":
            # Execute a tool
            tool_name = action.get("tool_name")
            arguments = action.get("arguments", {})
            
            if tool_name not in self.skills:
                return {"status": "error", "error": f"Tool '{tool_name}' not found"}
                
            tool = self.skills[tool_name]
            
            # Execute tool
            try:
                if tool.handler:
                    result = tool.handler(arguments)
                else:
                    result = {"status": "executed", "tool": tool_name, "args": arguments}
                    
                return result
            except Exception as e:
                return {"status": "error", "error": str(e)}
            
        elif action_type == "memory_store":
            # Store in agent memory
            agent_id = action.get("agent_id")
            content = action.get("content", "")
            memory_type = action.get("memory_type", "working")
            
            if agent_id not in self.memories:
                self.memories[agent_id] = []
                
            self.memories[agent_id].append({
                "type": memory_type,
                "content": content,
                "timestamp": time.time(),
            })
            
            # Trim to max items
            max_items = self.agents.get(agent_id, {}).get("memory_config", {}).get("max_items", 100)
            if len(self.memories[agent_id]) > max_items:
                self.memories[agent_id] = self.memories[agent_id][-max_items:]
            
            return {
                "status": "stored",
                "agent_id": agent_id,
                "memory_type": memory_type,
            }
            
        elif action_type == "memory_recall":
            # Recall from agent memory
            agent_id = action.get("agent_id")
            query = action.get("query", "")
            memory_type = action.get("memory_type")
            
            if agent_id not in self.memories:
                return {"status": "ok", "memories": []}
                
            memories = self.memories[agent_id]
            
            if memory_type:
                memories = [m for m in memories if m.get("type") == memory_type]
                
            if query:
                memories = [m for m in memories if query.lower() in str(m.get("content", "")).lower()]
                
            return {
                "status": "ok",
                "agent_id": agent_id,
                "memories": memories,
            }
            
        elif action_type == "memory_clear":
            # Clear agent memory
            agent_id = action.get("agent_id")
            
            if agent_id in self.memories:
                self.memories[agent_id] = []
                
            return {
                "status": "ok",
                "agent_id": agent_id,
            }
            
        elif action_type == "state_get":
            # Get agent state
            agent_id = action.get("agent_id")
            
            if agent_id not in self.agents:
                return {"status": "error", "error": "Agent not found"}
                
            agent = self.agents[agent_id]
            state = agent["state"]
            
            return {
                "status": "ok",
                "agent_id": agent_id,
                "state": {
                    "status": state.status,
                    "current_task": state.current_task,
                    "step_count": state.step_count,
                    "last_update": state.last_update,
                },
            }
            
        elif action_type == "agents_list":
            # List all agents
            return {
                "status": "ok",
                "agents": [
                    {
                        "id": agent_id,
                        "name": agent.get("name"),
                        "description": agent.get("description"),
                        "capabilities": agent.get("capabilities"),
                        "status": agent["state"].status,
                    }
                    for agent_id, agent in self.agents.items()
                ],
            }
            
        elif action_type == "tools_list":
            # List registered tools
            return {
                "status": "ok",
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                    }
                    for tool in self.skills.values()
                ],
            }
            
        return {"status": "unknown_action", "action": action}
        
    def _process_task(self, agent: Dict[str, Any], task: str) -> str:
        """Process a task based on agent capabilities."""
        capabilities = agent.get("capabilities", [])
        
        # Build response based on capabilities
        parts = []
        
        if "reasoning" in capabilities:
            parts.append("Reasoning: Analyzed the task requirements")
            
        if "planning" in capabilities:
            parts.append("Planning: Created execution plan")
            
        if "tools" in capabilities:
            tools = agent.get("tools", [])
            if tools:
                parts.append(f"Tools: Available {len(tools)} tool(s)")
                
        if "memory" in capabilities:
            parts.append("Memory: Context loaded")
            
        parts.append(f"Result: Processed '{task}'")
        
        return " | ".join(parts)
        
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        """Stream agent events."""
        for event in self._event_history[-10:]:
            yield event
            
    def close(self) -> None:
        """Clean up resources."""
        self.agents.clear()
        self.memories.clear()
        self.skills.clear()
        self.conversations.clear()
        self._event_history.clear()


# FastAPI integration
def create_microsoft_agent_app(bridge: MicrosoftAgentBridge):
    """Create a FastAPI app for Microsoft Agent bridge."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from typing import Dict, Any, List, Optional
    
    app = FastAPI(title="Microsoft Agent Bridge", version="0.1.0")
    
    class CreateAgentInput(BaseModel):
        agent_id: Optional[str] = None
        config: Dict[str, Any] = {}
        
    class InvokeInput(BaseModel):
        agent_id: str
        task: str = ""
        
    class ToolInput(BaseModel):
        tool: Dict[str, Any] = {}
        
    class MemoryInput(BaseModel):
        agent_id: str
        content: str = ""
        memory_type: str = "working"
        
    @app.post("/agents/create")
    def create_agent(req: CreateAgentInput):
        return bridge.invoke({
            "type": "agent_create",
            "agent_id": req.agent_id,
            "config": req.config,
        })
        
    @app.post("/agents/invoke")
    def invoke_agent(req: InvokeInput):
        return bridge.invoke({
            "type": "agent_invoke",
            "agent_id": req.agent_id,
            "task": req.task,
        })
        
    @app.get("/agents")
    def list_agents():
        return bridge.invoke({"type": "agents_list"})
        
    @app.get("/agents/{agent_id}/state")
    def get_state(agent_id: str):
        return bridge.invoke({
            "type": "state_get",
            "agent_id": agent_id,
        })
        
    @app.post("/agents/{agent_id}/memory")
    def store_memory(agent_id: str, req: MemoryInput):
        return bridge.invoke({
            "type": "memory_store",
            "agent_id": agent_id,
            "content": req.content,
            "memory_type": req.memory_type,
        })
        
    @app.get("/agents/{agent_id}/memory")
    def recall_memory(agent_id: str, query: str = ""):
        return bridge.invoke({
            "type": "memory_recall",
            "agent_id": agent_id,
            "query": query,
        })
        
    @app.post("/tools/register")
    def register_tool(req: ToolInput):
        return bridge.invoke({
            "type": "tool_register",
            "tool": req.tool,
        })
        
    @app.get("/tools")
    def list_tools():
        return bridge.invoke({"type": "tools_list"})
        
    @app.get("/stream")
    def stream():
        return {"events": list(bridge.stream())}
        
    return app