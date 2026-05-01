"""
OpenAI Agents SDK Bridge for AGenNext Runtime Core.

Provides integration with OpenAI Agents SDK for building agents with
tools, handoffs, structured outputs, and streaming.
"""

import json
import time
import uuid
from typing import Any, Callable, Dict, Generator, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class AgentCapability(Enum):
    TOOLS = "tools"
    HANDOFFS = "handoffs"
    STREAMING = "streaming"
    GUARDRAILS = "guardrails"


class GuardrailLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class OpenAITool:
    """OpenAI agent tool definition."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    handler: Optional[Callable] = None


@dataclass
class AgentInstruction:
    """Agent instruction/prompt."""
    content: str
    source: str = "system"


@dataclass
class Handoff:
    """Handoff configuration."""
    target_agent: str
    condition: str = ""
    description: str = ""


class OpenAIAgentBridge:
    """Bridge for OpenAI Agents SDK."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.tools: Dict[str, OpenAITool] = {}
        self._event_history: List[Dict[str, Any]] = []
        
    def init(self, config: Dict[str, Any]) -> None:
        """Initialize the OpenAI Agents bridge."""
        self.config = config
        
    def invoke(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an OpenAI Agents action."""
        action_type = action.get("type", "invoke")
        
        if action_type == "agent_create":
            # Create OpenAI agent
            agent_id = action.get("agent_id", f"openai_agent_{uuid.uuid4().hex[:8]}")
            agent_config = action.get("config", {})
            
            self.agents[agent_id] = {
                "id": agent_id,
                "name": agent_config.get("name", "OpenAI Agent"),
                "description": agent_config.get("description", ""),
                "instructions": agent_config.get("instructions", ""),
                "model": agent_config.get("model", "gpt-4o"),
                "tools": agent_config.get("tools", []),
                "handoffs": agent_config.get("handoffs", []),
                "guardrails": agent_config.get("guardrails", []),
                "max_turns": agent_config.get("max_turns", 10),
                "temperature": agent_config.get("temperature", 0.7),
                "stream_enabled": agent_config.get("streaming", False),
            }
            
            self.conversations[agent_id] = []
            
            return {
                "status": "created",
                "agent_id": agent_id,
                "name": self.agents[agent_id]["name"],
                "model": self.agents[agent_id]["model"],
            }
            
        elif action_type == "agent_invoke":
            # Invoke agent with message
            agent_id = action.get("agent_id")
            message = action.get("message", "")
            
            if agent_id not in self.agents:
                return {"status": "error", "error": "Agent not found"}
                
            agent = self.agents[agent_id]
            
            # Add to conversation
            self.conversations[agent_id].append({
                "role": "user",
                "content": message,
                "timestamp": time.time(),
            })
            
            # Process message (in production, call OpenAI Agents SDK)
            response = self._process_message(agent, message)
            
            # Add response
            self.conversations[agent_id].append({
                "role": "assistant",
                "content": response["content"],
                "timestamp": time.time(),
            })
            
            self._event_history.append({
                "type": "agent_invoke",
                "agent_id": agent_id,
                "message": message,
                "response": response,
            })
            
            return {
                "status": "ok",
                "agent_id": agent_id,
                "response": response,
            }
            
        elif action_type == "agent_stream":
            # Stream agent response
            agent_id = action.get("agent_id")
            message = action.get("message", "")
            
            if agent_id not in self.agents:
                return {"status": "error", "error": "Agent not found"}
                
            agent = self.agents[agent_id]
            
            # Stream response tokens
            for token in f"[OpenAI Agent] {message}".split():
                yield {"type": "content", "token": token}
                
        elif action_type == "tool_register":
            # Register a tool
            tool_def = action.get("tool", {})
            tool_name = tool_def.get("name")
            
            if tool_name:
                tool = OpenAITool(
                    name=tool_name,
                    description=tool_def.get("description", ""),
                    parameters=tool_def.get("parameters", {}),
                )
                self.tools[tool_name] = tool
                
                return {
                    "status": "registered",
                    "tool": tool_name,
                }
            
        elif action_type == "tool_execute":
            # Execute a tool
            tool_name = action.get("tool_name")
            arguments = action.get("arguments", {})
            
            if tool_name not in self.tools:
                return {"status": "error", "error": f"Tool '{tool_name}' not found"}
                
            tool = self.tools[tool_name]
            
            try:
                if tool.handler:
                    result = tool.handler(arguments)
                else:
                    result = {"status": "executed", "tool": tool_name, "args": arguments}
                    
                self._event_history.append({
                    "type": "tool_execute",
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": result,
                })
                
                return result
            except Exception as e:
                return {"status": "error", "error": str(e)}
            
        elif action_type == "handoff_trigger":
            # Trigger handoff to another agent
            source_agent_id = action.get("source_agent")
            target_agent_id = action.get("target_agent")
            context = action.get("context", {})
            
            if source_agent_id not in self.agents:
                return {"status": "error", "error": "Source agent not found"}
            if target_agent_id not in self.agents:
                return {"status": "error", "error": "Target agent not found"}
                
            return {
                "status": "handoff",
                "source": source_agent_id,
                "target": target_agent_id,
                "context": context,
            }
            
        elif action_type == "guardrail_check":
            # Check guardrails
            agent_id = action.get("agent_id")
            input_text = action.get("input", "")
            
            # Simple guardrail check (in production, use actual guardrails)
            blocked = False
            blocked_reason = ""
            
            # Check for blocked words
            blocked_words = ["dangerous", "harmful", "illegal"]
            for word in blocked_words:
                if word in input_text.lower():
                    blocked = True
                    blocked_reason = f"Blocked word: {word}"
                    break
                    
            return {
                "status": "ok",
                "passed": not blocked,
                "blocked": blocked,
                "reason": blocked_reason,
            }
            
        elif action_type == "structured_output":
            # Get structured output from agent
            agent_id = action.get("agent_id")
            schema = action.get("schema", {})
            message = action.get("message", "")
            
            # Generate structured response based on schema
            output = {}
            for key, prop in schema.get("properties", {}).items():
                output[key] = f"Sample {prop.get('type', 'value')}"
                
            return {
                "status": "ok",
                "agent_id": agent_id,
                "output": output,
            }
            
        elif action_type == "conversation_get":
            # Get conversation
            agent_id = action.get("agent_id")
            
            if agent_id not in self.conversations:
                return {"status": "error", "error": "Conversation not found"}
                
            return {
                "status": "ok",
                "agent_id": agent_id,
                "messages": self.conversations[agent_id][-20:],
            }
            
        elif action_type == "conversation_clear":
            # Clear conversation
            agent_id = action.get("agent_id")
            
            if agent_id in self.conversations:
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
                        "name": agent.get("name"),
                        "model": agent.get("model"),
                        "tools_count": len(agent.get("tools", [])),
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
                    for tool in self.tools.values()
                ],
            }
            
        return {"status": "unknown_action", "action": action}
        
    def _process_message(self, agent: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Process message with agent."""
        # Build response based on agent config
        tools = agent.get("tools", [])
        
        response_content = f"[{agent['name']}] Processing: {message}"
        
        # Simulate tool calls if tools available
        tool_calls = []
        if tools:
            tool_calls = [
                {"name": t, "arguments": {}}
                for t in tools[:2]  # Limit to 2
            ]
            response_content += f" (using {len(tool_calls)} tools)"
        
        return {
            "content": response_content,
            "tool_calls": tool_calls,
            "usage": {
                "input_tokens": len(message.split()),
                "output_tokens": len(response_content.split()),
            },
        }
        
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        """Stream agent events."""
        for event in self._event_history[-10:]:
            yield event
            
    def close(self) -> None:
        """Clean up resources."""
        self.agents.clear()
        self.conversations.clear()
        self.tools.clear()
        self._event_history.clear()


# FastAPI integration
def create_openai_agents_app(bridge: OpenAIAgentBridge):
    """Create a FastAPI app for OpenAI Agents bridge."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from typing import Dict, Any, List, Optional
    
    app = FastAPI(title="OpenAI Agents Bridge", version="0.1.0")
    
    class CreateAgentInput(BaseModel):
        agent_id: Optional[str] = None
        config: Dict[str, Any]
        
    class InvokeInput(BaseModel):
        agent_id: str
        message: str = ""
        
    class ToolInput(BaseModel):
        tool: Dict[str, Any] = {}
        
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
            "message": req.message,
        })
        
    @app.get("/agents")
    def list_agents():
        return bridge.invoke({"type": "agents_list"})
        
    @app.get("/agents/{agent_id}/conversation")
    def get_conversation(agent_id: str):
        return bridge.invoke({
            "type": "conversation_get",
            "agent_id": agent_id,
        })
        
    @app.delete("/agents/{agent_id}/conversation")
    def clear_conversation(agent_id: str):
        return bridge.invoke({
            "type": "conversation_clear",
            "agent_id": agent_id,
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
        
    @app.post("/guardrails/check")
    def check_guardrail(req: InvokeInput):
        return bridge.invoke({
            "type": "guardrail_check",
            "agent_id": req.agent_id,
            "input": req.message,
        })
        
    @app.get("/stream")
    def stream():
        return {"events": list(bridge.stream())}
        
    return app