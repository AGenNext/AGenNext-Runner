"""
AutoGPT Bridge for AGenNext Runtime Core.

Provides integration with AutoGPT for autonomous agent execution,
self-prompting, and continuous task completion.
"""

import json
import time
from typing import Any, Callable, Dict, Generator, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class AUTOGPTMode(Enum):
    FAST = "fast"
    BALANCED = "balanced"
    DEEP = "deep"


class CommandType(Enum):
    SEARCH = "search"
    BROWSE = "browse"
    WRITE = "write"
    READ = "read"
    EXECUTE = "execute"
    ANALYZE = "analyze"


@dataclass
class AITask:
    """AutoGPT task definition."""
    id: str
    goal: str
    status: str = "pending"
    iterations: int = 0
    max_iterations: int = 5
    commands: List[Dict[str, Any]] = field(default_factory=list)
    results: List[str] = field(default_factory=list)


@dataclass
class CommandResult:
    """Result from a command execution."""
    command: str
    result: str
    success: bool = True
    error: Optional[str] = None


class AutoGPTBridge:
    """Bridge for AutoGPT execution."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.tasks: Dict[str, AITask] = {}
        self.agents: Dict[str, Dict[str, Any]] = {}
        self._event_history: List[Dict[str, Any]] = []
        
    def init(self, config: Dict[str, Any]) -> None:
        """Initialize the AutoGPT bridge."""
        self.config = config
        
    def _generate_commands(self, goal: str) -> List[Dict[str, Any]]:
        """Generate commands based on goal."""
        # Simple command generation (in production, use AI)
        commands = []
        
        if "search" in goal.lower() or "find" in goal.lower():
            commands.append({
                "command": "search",
                "args": {"query": goal},
            })
            
        if "write" in goal.lower() or "create" in goal.lower():
            commands.append({
                "command": "write",
                "args": {"content": "Generated content"},
            })
            
        if "analyze" in goal.lower() or "review" in goal.lower():
            commands.append({
                "command": "analyze",
                "args": {"subject": goal},
            })
            
        # Default command
        if not commands:
            commands.append({
                "command": "execute",
                "args": {"action": goal},
            })
            
        return commands
        
    def invoke(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an AutoGPT action."""
        action_type = action.get("type", "invoke")
        
        if action_type == "agent_create":
            # Create AutoGPT agent
            agent_id = action.get("agent_id", f"autogpt_{len(self.agents)}")
            agent_config = action.get("config", {})
            
            self.agents[agent_id] = {
                "id": agent_id,
                "name": agent_config.get("name", "AutoGPT Agent"),
                "goals": agent_config.get("goals", []),
                "mode": AUTOGPTMode(agent_config.get("mode", "balanced")),
                "max_iterations": agent_config.get("max_iterations", 5),
                "commands": agent_config.get("commands", []),
            }
            
            return {
                "status": "created",
                "agent_id": agent_id,
                "name": self.agents[agent_id]["name"],
            }
            
        elif action_type == "task_create":
            # Create a task
            task_id = action.get("task_id", f"task_{len(self.tasks)}")
            task_def = action.get("task", {})
            
            task = AITask(
                id=task_id,
                goal=task_def.get("goal", ""),
                max_iterations=task_def.get("max_iterations", 5),
            )
            
            # Generate initial commands
            task.commands = self._generate_commands(task.goal)
            
            self.tasks[task_id] = task
            
            return {
                "status": "created",
                "task_id": task_id,
                "goal": task.goal,
                "commands": len(task.commands),
            }
            
        elif action_type == "task_execute":
            # Execute AutoGPT task (single iteration)
            task_id = action.get("task_id")
            
            if task_id not in self.tasks:
                return {"status": "error", "error": "Task not found"}
                
            task = self.tasks[task_id]
            
            if task.iterations >= task.max_iterations:
                return {
                    "status": "completed",
                    "task_id": task_id,
                    "iterations": task.iterations,
                    "results": task.results,
                }
            
            task.iterations += 1
            
            # Execute commands
            results = []
            for cmd in task.commands:
                result = f"Executed {cmd.get('command')}: {cmd.get('args', {})}"
                results.append(result)
                task.results.append(result)
                
            # Generate feedback and next steps
            feedback = f"Iteration {task.iterations}: Completed {len(task.commands)} commands"
            
            self._event_history.append({
                "type": "task_execute",
                "task_id": task_id,
                "iteration": task.iterations,
                "results": results,
            })
            
            return {
                "status": "ok",
                "task_id": task_id,
                "iteration": task.iterations,
                "results": results,
                "feedback": feedback,
                "completed": task.iterations >= task.max_iterations,
            }
            
        elif action_type == "task_run":
            # Run full task to completion
            task_id = action.get("task_id")
            
            if task_id not in self.tasks:
                return {"status": "error", "error": "Task not found"}
                
            task = self.tasks[task_id]
            
            all_results = []
            while task.iterations < task.max_iterations:
                task.iterations += 1
                
                # Execute commands
                for cmd in task.commands:
                    result = f"Iteration {task.iterations}: {cmd.get('command')}"
                    task.results.append(result)
                    all_results.append(result)
                    
                # Generate new commands based on results
                task.commands = self._generate_commands(f"Continue: {task.goal}")
                
            self._event_history.append({
                "type": "task_run",
                "task_id": task_id,
                "iterations": task.iterations,
                "results": all_results,
            })
            
            return {
                "status": "completed",
                "task_id": task_id,
                "iterations": task.iterations,
                "results": task.results,
            }
            
        elif action_type == "task_get":
            # Get task status
            task_id = action.get("task_id")
            
            if task_id not in self.tasks:
                return {"status": "error", "error": "Task not found"}
                
            task = self.tasks[task_id]
            
            return {
                "status": "ok",
                "task_id": task_id,
                "goal": task.goal,
                "status": task.status,
                "iterations": task.iterations,
                "max_iterations": task.max_iterations,
                "results": task.results,
            }
            
        elif action_type == "goals_set":
            # Set agent goals
            agent_id = action.get("agent_id")
            goals = action.get("goals", [])
            
            if agent_id in self.agents:
                self.agents[agent_id]["goals"] = goals
                
            return {
                "status": "ok",
                "agent_id": agent_id,
                "goals": goals,
            }
            
        elif action_type == "agent_run":
            # Run agent with goals
            agent_id = action.get("agent_id")
            
            if agent_id not in self.agents:
                return {"status": "error", "error": "Agent not found"}
                
            agent = self.agents[agent_id]
            goals = agent.get("goals", [])
            
            results = []
            for goal in goals:
                task_id = f"task_{goal[:10]}"
                task = AITask(
                    id=task_id,
                    goal=goal,
                    max_iterations=agent.get("max_iterations", 5),
                )
                task.commands = self._generate_commands(goal)
                
                # Run iterations
                for _ in range(task.max_iterations):
                    task.iterations += 1
                    task.results.append(f"Processed: {goal}")
                    
                results.append({
                    "goal": goal,
                    "iterations": task.iterations,
                    "results": task.results,
                })
                
            return {
                "status": "completed",
                "agent_id": agent_id,
                "goals_processed": len(goals),
                "results": results,
            }
            
        elif action_type == "tasks_list":
            # List all tasks
            return {
                "status": "ok",
                "tasks": [
                    {
                        "id": task.id,
                        "goal": task.goal,
                        "status": task.status,
                        "iterations": task.iterations,
                    }
                    for task in self.tasks.values()
                ],
            }
            
        elif action_type == "agents_list":
            # List all agents
            return {
                "status": "ok",
                "agents": [
                    {
                        "id": agent_id,
                        "name": agent.get("name"),
                        "goals_count": len(agent.get("goals", [])),
                    }
                    for agent_id, agent in self.agents.items()
                ],
            }
            
        return {"status": "unknown_action", "action": action}
        
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        """Stream AutoGPT events."""
        for event in self._event_history[-10:]:
            yield event
            
    def close(self) -> None:
        """Clean up resources."""
        self.tasks.clear()
        self.agents.clear()
        self._event_history.clear()


# FastAPI integration
def create_autogpt_app(bridge: AutoGPTBridge):
    """Create a FastAPI app for AutoGPT bridge."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from typing import Dict, Any, List, Optional
    
    app = FastAPI(title="AutoGPT Bridge", version="0.1.0")
    
    class CreateAgentInput(BaseModel):
        agent_id: Optional[str] = None
        config: Dict[str, Any] = {}
        
    class CreateTaskInput(BaseModel):
        task_id: Optional[str] = None
        task: Dict[str, Any]
        
    @app.post("/agents/create")
    def create_agent(req: CreateAgentInput):
        return bridge.invoke({
            "type": "agent_create",
            "agent_id": req.agent_id,
            "config": req.config,
        })
        
    @app.post("/tasks/create")
    def create_task(req: CreateTaskInput):
        return bridge.invoke({
            "type": "task_create",
            "task_id": req.task_id,
            "task": req.task,
        })
        
    @app.post("/tasks/{task_id}/execute")
    def execute_task(task_id: str):
        return bridge.invoke({
            "type": "task_execute",
            "task_id": task_id,
        })
        
    @app.post("/tasks/{task_id}/run")
    def run_task(task_id: str):
        return bridge.invoke({
            "type": "task_run",
            "task_id": task_id,
        })
        
    @app.get("/tasks/{task_id}")
    def get_task(task_id: str):
        return bridge.invoke({
            "type": "task_get",
            "task_id": task_id,
        })
        
    @app.get("/tasks")
    def list_tasks():
        return bridge.invoke({"type": "tasks_list"})
        
    @app.get("/agents")
    def list_agents():
        return bridge.invoke({"type": "agents_list"})
        
    @app.post("/agents/{agent_id}/run")
    def run_agent(agent_id: str):
        return bridge.invoke({
            "type": "agent_run",
            "agent_id": agent_id,
        })
        
    @app.get("/stream")
    def stream():
        return {"events": list(bridge.stream())}
        
    return app