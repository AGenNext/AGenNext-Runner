"""
AgentGPT Bridge for AGenNext Runtime Core.

Provides integration with AgentGPT for web-based autonomous agent creation,
execution, and management.
"""

import json
import time
import uuid
from typing import Any, Dict, Generator, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class AgentGPTStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class TaskPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


@dataclass
class AgentGPTConfig:
    """AgentGPT agent configuration."""
    name: str
    description: str = ""
    goals: List[str] = field(default_factory=list)
    model: str = "gpt-4"
    max_steps: int = 100
    verbose: bool = True
    allow_downloads: bool = False
    headless: bool = False


@dataclass
class TaskItem:
    """Task in AgentGPT."""
    id: str
    title: str
    description: str = ""
    status: str = "pending"
    priority: TaskPriority = TaskPriority.NORMAL
    result: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


@dataclass
class ExecutionStep:
    """Single step in agent execution."""
    step_number: int
    thought: str
    action: str
    result: str
    timestamp: float = field(default_factory=time.time)


class AgentGPTBridge:
    """Bridge for AgentGPT execution."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.agents: Dict[str, AgentGPTConfig] = {}
        self.executions: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, List[TaskItem]] = {}
        self._event_history: List[Dict[str, Any]] = []
        
    def init(self, config: Dict[str, Any]) -> None:
        """Initialize the AgentGPT bridge."""
        self.config = config
        
    def invoke(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an AgentGPT action."""
        action_type = action.get("type", "invoke")
        
        if action_type == "agent_create":
            # Create AgentGPT agent
            agent_id = action.get("agent_id", f"agentgpt_{uuid.uuid4().hex[:8]}")
            agent_config = action.get("config", {})
            
            agent = AgentGPTConfig(
                name=agent_config.get("name", "AgentGPT Agent"),
                description=agent_config.get("description", ""),
                goals=agent_config.get("goals", []),
                model=agent_config.get("model", "gpt-4"),
                max_steps=agent_config.get("max_steps", 100),
                verbose=agent_config.get("verbose", True),
                allow_downloads=agent_config.get("allow_downloads", False),
                headless=agent_config.get("headless", False),
            )
            
            self.agents[agent_id] = agent
            self.tasks[agent_id] = []
            
            return {
                "status": "created",
                "agent_id": agent_id,
                "name": agent.name,
                "goals": agent.goals,
            }
            
        elif action_type == "agent_start":
            # Start agent execution
            agent_id = action.get("agent_id")
            
            if agent_id not in self.agents:
                return {"status": "error", "error": "Agent not found"}
                
            agent = self.agents[agent_id]
            
            # Create execution context
            execution_id = f"exec_{uuid.uuid4().hex[:8]}"
            self.executions[execution_id] = {
                "id": execution_id,
                "agent_id": agent_id,
                "status": AgentGPTStatus.RUNNING.value,
                "current_step": 0,
                "max_steps": agent.max_steps,
                "goals": agent.goals,
                "results": [],
                "steps": [],
                "started_at": time.time(),
            }
            
            return {
                "status": "started",
                "execution_id": execution_id,
                "agent_id": agent_id,
            }
            
        elif action_type == "agent_step":
            # Execute single step
            execution_id = action.get("execution_id")
            
            if execution_id not in self.executions:
                return {"status": "error", "error": "Execution not found"}
                
            execution = self.executions[execution_id]
            
            if execution["status"] != AgentGPTStatus.RUNNING.value:
                return {"status": "error", "error": "Execution not running"}
                
            execution["current_step"] += 1
            
            # Simulate step
            thought = f"Analyzing goal {execution['current_step']}/{execution['max_steps']}"
            action = "process_goal"
            result = f"Completed step {execution['current_step']}"
            
            step = ExecutionStep(
                step_number=execution["current_step"],
                thought=thought,
                action=action,
                result=result,
            )
            
            execution["steps"].append({
                "step": step.step_number,
                "thought": step.thought,
                "action": step.action,
                "result": step.result,
            })
            execution["results"].append(result)
            
            # Check completion
            completed = execution["current_step"] >= execution["max_steps"]
            if completed:
                execution["status"] = AgentGPTStatus.COMPLETED.value
                execution["completed_at"] = time.time()
                
            self._event_history.append({
                "type": "agent_step",
                "execution_id": execution_id,
                "step": execution["current_step"],
            })
            
            return {
                "status": "ok",
                "execution_id": execution_id,
                "step": execution["current_step"],
                "thought": thought,
                "action": action,
                "result": result,
                "completed": completed,
            }
            
        elif action_type == "agent_pause":
            # Pause execution
            execution_id = action.get("execution_id")
            
            if execution_id in self.executions:
                self.executions[execution_id]["status"] = AgentGPTStatus.PAUSED.value
                
            return {
                "status": "paused",
                "execution_id": execution_id,
            }
            
        elif action_type == "agent_resume":
            # Resume execution
            execution_id = action.get("execution_id")
            
            if execution_id in self.executions:
                self.executions[execution_id]["status"] = AgentGPTStatus.RUNNING.value
                
            return {
                "status": "resumed",
                "execution_id": execution_id,
            }
            
        elif action_type == "agent_stop":
            # Stop execution
            execution_id = action.get("execution_id")
            
            if execution_id in self.executions:
                self.executions[execution_id]["status"] = AgentGPTStatus.COMPLETED.value
                self.executions[execution_id]["stopped_at"] = time.time()
                
            return {
                "status": "stopped",
                "execution_id": execution_id,
            }
            
        elif action_type == "execution_status":
            # Get execution status
            execution_id = action.get("execution_id")
            
            if execution_id not in self.executions:
                return {"status": "error", "error": "Execution not found"}
                
            execution = self.executions[execution_id]
            
            return {
                "status": "ok",
                "execution": {
                    "id": execution["id"],
                    "agent_id": execution["agent_id"],
                    "status": execution["status"],
                    "current_step": execution["current_step"],
                    "max_steps": execution["max_steps"],
                    "goals": execution["goals"],
                    "results": execution["results"][-5:],  # Last 5
                },
            }
            
        elif action_type == "goals_set":
            # Set agent goals
            agent_id = action.get("agent_id")
            goals = action.get("goals", [])
            
            if agent_id in self.agents:
                self.agents[agent_id].goals = goals
                
            return {
                "status": "ok",
                "agent_id": agent_id,
                "goals": goals,
            }
            
        elif action_type == "task_add":
            # Add task to agent
            agent_id = action.get("agent_id")
            task_def = action.get("task", {})
            
            task = TaskItem(
                id=task_def.get("id", f"task_{uuid.uuid4().hex[:8]}"),
                title=task_def.get("title", ""),
                description=task_def.get("description", ""),
                priority=TaskPriority(task_def.get("priority", "normal")),
            )
            
            if agent_id not in self.tasks:
                self.tasks[agent_id] = []
                
            self.tasks[agent_id].append(task)
            
            return {
                "status": "added",
                "task_id": task.id,
                "agent_id": agent_id,
            }
            
        elif action_type == "task_complete":
            # Complete a task
            task_id = action.get("task_id")
            result = action.get("result", "")
            
            # Find task
            for agent_id, tasks in self.tasks.items():
                for task in tasks:
                    if task.id == task_id:
                        task.status = "completed"
                        task.result = result
                        task.completed_at = time.time()
                        break
                        
            return {
                "status": "completed",
                "task_id": task_id,
            }
            
        elif action_type == "tasks_list":
            # List agent tasks
            agent_id = action.get("agent_id")
            
            tasks = self.tasks.get(agent_id, [])
            
            return {
                "status": "ok",
                "tasks": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "status": t.status,
                        "priority": t.priority.value,
                    }
                    for t in tasks
                ],
            }
            
        elif action_type == "agents_list":
            # List all agents
            return {
                "status": "ok",
                "agents": [
                    {
                        "id": agent_id,
                        "name": agent.name,
                        "goals_count": len(agent.goals),
                        "model": agent.model,
                    }
                    for agent_id, agent in self.agents.items()
                ],
            }
            
        return {"status": "unknown_action", "action": action}
        
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        """Stream AgentGPT events."""
        for event in self._event_history[-10:]:
            yield event
            
    def close(self) -> None:
        """Clean up resources."""
        self.agents.clear()
        self.executions.clear()
        self.tasks.clear()
        self._event_history.clear()


# FastAPI integration
def create_agentgpt_app(bridge: AgentGPTBridge):
    """Create a FastAPI app for AgentGPT bridge."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from typing import Dict, Any, List, Optional
    
    app = FastAPI(title="AgentGPT Bridge", version="0.1.0")
    
    class CreateAgentInput(BaseModel):
        agent_id: Optional[str] = None
        config: Dict[str, Any]
        
    class StartAgentInput(BaseModel):
        agent_id: str
        
    @app.post("/agents/create")
    def create_agent(req: CreateAgentInput):
        return bridge.invoke({
            "type": "agent_create",
            "agent_id": req.agent_id,
            "config": req.config,
        })
        
    @app.post("/agents/start")
    def start_agent(req: StartAgentInput):
        return bridge.invoke({
            "type": "agent_start",
            "agent_id": req.agent_id,
        })
        
    @app.post("/executions/{execution_id}/step")
    def step(execution_id: str):
        return bridge.invoke({
            "type": "agent_step",
            "execution_id": execution_id,
        })
        
    @app.post("/executions/{execution_id}/pause")
    def pause(execution_id: str):
        return bridge.invoke({
            "type": "agent_pause",
            "execution_id": execution_id,
        })
        
    @app.post("/executions/{execution_id}/resume")
    def resume(execution_id: str):
        return bridge.invoke({
            "type": "agent_resume",
            "execution_id": execution_id,
        })
        
    @app.post("/executions/{execution_id}/stop")
    def stop(execution_id: str):
        return bridge.invoke({
            "type": "agent_stop",
            "execution_id": execution_id,
        })
        
    @app.get("/executions/{execution_id}")
    def status(execution_id: str):
        return bridge.invoke({
            "type": "execution_status",
            "execution_id": execution_id,
        })
        
    @app.get("/agents")
    def list_agents():
        return bridge.invoke({"type": "agents_list"})
        
    @app.get("/agents/{agent_id}/tasks")
    def list_tasks(agent_id: str):
        return bridge.invoke({
            "type": "tasks_list",
            "agent_id": agent_id,
        })
        
    @app.get("/stream")
    def stream():
        return {"events": list(bridge.stream())}
        
    return app