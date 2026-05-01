"""
Microsoft AutoGen Bridge for AGenNext Runtime Core.

Provides integration with AutoGen for multi-agent conversations,
group chat, and automated task solving.
"""

import json
import time
from typing import Any, Dict, Generator, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class AgentType(Enum):
    ASSISTANT = "assistant"
    USERPROXY = "userproxy"
    GROUP = "group"
    SPEAKER = "speaker"


class AgentRole(Enum):
    ASSISTANT = "assistant"
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


@dataclass
class AgentConfig:
    """Configuration for an AutoGen agent."""
    name: str
    agent_type: AgentType = AgentType.ASSISTANT
    role: AgentRole = AgentRole.ASSISTANT
    llm_config: Optional[Dict[str, Any]] = None
    system_message: str = ""
    code_execution: bool = False
    human_input_mode: str = "NEVER"


@dataclass
class Message:
    """Chat message."""
    role: str
    content: str
    sender: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class GroupChatConfig:
    """Group chat configuration."""
    agents: List[AgentConfig] = field(default_factory=list)
    speaker_selection_method: str = "round_robin"
    max_round: int = 10
    allow_termination: bool = True


class AutoGenBridge:
    """Bridge for Microsoft AutoGen execution."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.agents: Dict[str, AgentConfig] = {}
        self.conversations: Dict[str, List[Message]] = {}
        self.group_chats: Dict[str, GroupChatConfig] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._autogen_enabled: bool = False
        
    def init(self, config: Dict[str, Any]) -> None:
        """Initialize the AutoGen bridge."""
        self.config = config
        
        # Try to import autogen
        try:
            from autogen import ConversableAgent, UserProxyAgent
            
            self._autogen_enabled = True
            self._ConversableAgent = ConversableAgent
            self._UserProxyAgent = UserProxyAgent
            
        except ImportError:
            self._autogen_enabled = False
            
    def _create_assistant_agent(self, name: str, config: AgentConfig):
        """Create an assistant agent."""
        if not self._autogen_enabled:
            return None
            
        try:
            from autogen import ConversableAgent
            
            return ConversableAgent(
                name=name,
                llm_config=config.llm_config or {
                    "model": "gpt-4",
                    "api_key": "mock",
                },
                system_message=config.system_message,
                code_execution_mode=config.code_execution,
            )
        except:
            return None
            
    def _create_user_agent(self, name: str):
        """Create a user proxy agent."""
        if not self._autogen_enabled:
            return None
            
        try:
            from autogen import UserProxyAgent
            
            return UserProxyAgent(
                name=name,
                human_input_mode="NEVER",
            )
        except:
            return None
            
    def invoke(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an AutoGen action."""
        action_type = action.get("type", "invoke")
        
        if action_type == "agent_create":
            # Create an agent
            agent_name = action.get("agent_name")
            agent_config = action.get("config", {})
            
            config = AgentConfig(
                name=agent_name,
                agent_type=AgentType(agent_config.get("type", "assistant")),
                role=AgentRole(agent_config.get("role", "assistant")),
                llm_config=agent_config.get("llm_config"),
                system_message=agent_config.get("system_message", ""),
                code_execution=agent_config.get("code_execution", False),
                human_input_mode=agent_config.get("human_input_mode", "NEVER"),
            )
            
            self.agents[agent_name] = config
            
            # Initialize conversation
            if agent_name not in self.conversations:
                self.conversations[agent_name] = []
                
            return {
                "status": "created",
                "agent_name": agent_name,
                "agent_type": config.agent_type.value,
            }
            
        elif action_type == "agent_chat":
            # Single agent chat
            agent_name = action.get("agent_name")
            message = action.get("message", "")
            
            if agent_name not in self.agents:
                return {"status": "error", "error": "Agent not found"}
                
            if not self._autogen_enabled:
                # Mock response
                response = f"[AutoGen {agent_name}] {message}"
                
                self.conversations[agent_name].append(Message(
                    role="user",
                    content=message,
                    sender="user",
                ))
                self.conversations[agent_name].append(Message(
                    role="assistant",
                    content=response,
                    sender=agent_name,
                ))
                
                return {
                    "status": "ok",
                    "response": response,
                    "agent_name": agent_name,
                }
                
            try:
                from autogen import ConversableAgent
                
                agent = self._create_assistant_agent(agent_name, self.agents[agent_name])
                reply = agent.generate_reply(
                    messages=[{"role": "user", "content": message}]
                )
                
                self.conversations[agent_name].append(Message(
                    role="user",
                    content=message,
                    sender="user",
                ))
                self.conversations[agent_name].append(Message(
                    role="assistant",
                    content=str(reply),
                    sender=agent_name,
                ))
                
                self._event_history.append({
                    "type": "agent_chat",
                    "agent_name": agent_name,
                    "message": message,
                    "response": str(reply),
                })
                
                return {
                    "status": "ok",
                    "response": str(reply),
                    "agent_name": agent_name,
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "agent_name": agent_name,
                }
                
        elif action_type == "group_create":
            # Create group chat
            group_id = action.get("group_id", f"group_{len(self.group_chats)}")
            group_config = action.get("config", {})
            
            agents = []
            for agent_name in group_config.get("agents", []):
                if agent_name in self.agents:
                    agents.append(self.agents[agent_name])
                else:
                    # Create default config
                    agents.append(AgentConfig(name=agent_name))
                    
            config = GroupChatConfig(
                agents=agents,
                speaker_selection_method=group_config.get("speaker_selection_method", "round_robin"),
                max_round=group_config.get("max_round", 10),
                allow_termination=group_config.get("allow_termination", True),
            )
            
            self.group_chats[group_id] = config
            
            return {
                "status": "created",
                "group_id": group_id,
                "agent_count": len(agents),
            }
            
        elif action_type == "group_chat":
            # Execute group chat
            group_id = action.get("group_id")
            message = action.get("message", "")
            
            if group_id not in self.group_chats:
                return {"status": "error", "error": "Group not found"}
                
            if not self._autogen_enabled:
                # Mock group response
                responses = [
                    f"[{agent.name}] Response to: {message}"
                    for agent in self.group_chats[group_id].agents
                ]
                
                return {
                    "status": "completed",
                    "responses": responses,
                    "group_id": group_id,
                    "rounds": 1,
                }
                
            try:
                from autogen import GroupChat, GroupChatManager
                
                group_config = self.group_chats[group_id]
                
                # Create agents
                agents = []
                for agent_config in group_config.agents:
                    agent = self._create_assistant_agent(
                        agent_config.name, 
                        agent_config
                    )
                    if agent:
                        agents.append(agent)
                        
                if not agents:
                    return {"status": "error", "error": "No agents available"}
                    
                # Create group chat
                group_chat = GroupChat(
                    agents=agents,
                    max_round=group_config.max_round,
                    speaker_selection_method=group_config.speaker_selection_method,
                )
                
                manager = GroupChatManager(groupchat=group_chat)
                
                # Initiate chat
                result = manager.initiate_chat(
                    message=message,
                    summary_method="last_msg",
                )
                
                return {
                    "status": "completed",
                    "summary": str(result),
                    "group_id": group_id,
                    "rounds": group_chat.agent_names,
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "group_id": group_id,
                }
                
        elif action_type == "group_select_speaker":
            # Manually select next speaker
            group_id = action.get("group_id")
            speaker_name = action.get("speaker_name")
            
            if group_id not in self.group_chats:
                return {"status": "error", "error": "Group not found"}
                
            return {
                "status": "ok",
                "group_id": group_id,
                "next_speaker": speaker_name,
            }
            
        elif action_type == "conversation_get":
            # Get conversation history
            agent_name = action.get("agent_name")
            
            if agent_name not in self.conversations:
                return {"status": "error", "error": "Conversation not found"}
                
            messages = [
                {"role": m.role, "content": m.content, "sender": m.sender}
                for m in self.conversations[agent_name]
            ]
            
            return {
                "status": "ok",
                "agent_name": agent_name,
                "messages": messages,
            }
            
        elif action_type == "conversation_clear":
            # Clear conversation
            agent_name = action.get("agent_name")
            
            if agent_name in self.conversations:
                self.conversations[agent_name] = []
                
            return {
                "status": "ok",
                "agent_name": agent_name,
            }
            
        elif action_type == "agents_list":
            # List all agents
            return {
                "status": "ok",
                "agents": [
                    {
                        "name": name,
                        "type": config.agent_type.value,
                        "role": config.role.value,
                    }
                    for name, config in self.agents.items()
                ],
            }
            
        return {"status": "unknown_action", "action": action}
        
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        """Stream chat events."""
        for event in self._event_history[-10:]:
            yield event
            
    def close(self) -> None:
        """Clean up resources."""
        self.agents.clear()
        self.conversations.clear()
        self.group_chats.clear()
        self._event_history.clear()


# FastAPI integration
def create_autogen_app(bridge: AutoGenBridge):
    """Create a FastAPI app for AutoGen bridge."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    
    app = FastAPI(title="AutoGen Bridge", version="0.1.0")
    
    class InvokeInput(BaseModel):
        type: str = "invoke"
        agent_name: str = ""
        message: str = ""
        
    @app.post("/invoke")
    def invoke(req: InvokeInput):
        return bridge.invoke(req.model_dump(exclude={"type"}))
        
    @app.get("/agents")
    def list_agents():
        return bridge.invoke({"type": "agents_list"})
        
    @app.get("/groups")
    def list_groups():
        return {"groups": list(bridge.group_chats.keys())}
        
    @app.get("/conversation/{agent_name}")
    def get_conversation(agent_name: str):
        return bridge.invoke({
            "type": "conversation_get",
            "agent_name": agent_name,
        })
        
    @app.get("/stream")
    def stream():
        return {"events": list(bridge.stream())}
        
    return app