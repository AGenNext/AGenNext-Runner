"""
CrewAI Bridge for AGenNext Runtime Core.

Provides integration with CrewAI for multi-agent crew orchestration,
task management, and collaborative AI workflows.
"""

import json
import time
from typing import Any, Dict, Generator, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class CrewMethod(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentConfig:
    """CrewAI agent configuration."""
    role: str
    goal: str
    backstory: str = ""
    verbose: bool = False
    allow_delegation: bool = False
    max_iterations: int = 10


@dataclass
class Task:
    """CrewAI task."""
    description: str
    agent_role: str
    expected_output: str = ""
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    assigned_at: Optional[float] = None
    completed_at: Optional[float] = None


@dataclass
class CrewConfig:
    """Crew configuration."""
    agents: List[AgentConfig] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    method: CrewMethod = CrewMethod.SEQUENTIAL
    verbose: bool = True
    max_iterations: int = 10
    process: str = "sequential"


class CrewAIBridge:
    """Bridge for CrewAI execution."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.agents: Dict[str, AgentConfig] = {}
        self.tasks: Dict[str, Task] = {}
        self.crews: Dict[str, CrewConfig] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._crewai_enabled: bool = False
        
    def init(self, config: Dict[str, Any]) -> None:
        """Initialize the CrewAI bridge."""
        self.config = config
        
        # Try to import crewai
        try:
            from crewai import Agent, Task, Process
            
            self._crewai_enabled = True
            self._Agent = Agent
            self._Task = Task
            self._Process = Process
            
        except ImportError:
            self._crewai_enabled = False
            
    def invoke(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a CrewAI action."""
        action_type = action.get("type", "invoke")
        
        if action_type == "agent_create":
            # Create an agent
            agent_id = action.get("agent_id")
            agent_config = action.get("config", {})
            
            config = AgentConfig(
                role=agent_config.get("role", "Helper"),
                goal=agent_config.get("goal", "Help with tasks"),
                backstory=agent_config.get("backstory", "You are a helpful AI assistant."),
                verbose=agent_config.get("verbose", False),
                allow_delegation=agent_config.get("allow_delegation", False),
                max_iterations=agent_config.get("max_iterations", 10),
            )
            
            self.agents[agent_id] = config
            
            return {
                "status": "created",
                "agent_id": agent_id,
                "role": config.role,
            }
            
        elif action_type == "task_create":
            # Create a task
            task_id = action.get("task_id")
            task_config = action.get("config", {})
            
            task = Task(
                description=task_config.get("description", ""),
                agent_role=task_config.get("agent_role", "Helper"),
                expected_output=task_config.get("expected_output", ""),
            )
            
            self.tasks[task_id] = task
            
            return {
                "status": "created",
                "task_id": task_id,
                "description": task.description,
            }
            
        elif action_type == "crew_create":
            # Create a crew
            crew_id = action.get("crew_id", f"crew_{len(self.crews)}")
            crew_config = action.get("config", {})
            
            # Get agent configs
            agent_ids = crew_config.get("agents", [])
            agents = []
            for agent_id in agent_ids:
                if agent_id in self.agents:
                    agents.append(self.agents[agent_id])
                else:
                    agents.append(AgentConfig(role=agent_id))
                    
            # Get tasks
            task_ids = crew_config.get("tasks", [])
            tasks = []
            for task_id in task_ids:
                if task_id in self.tasks:
                    tasks.append(self.tasks[task_id])
                    
            config = CrewConfig(
                agents=agents,
                tasks=tasks,
                method=CrewMethod(crew_config.get("method", "sequential")),
                verbose=crew_config.get("verbose", True),
                max_iterations=crew_config.get("max_iterations", 10),
                process=crew_config.get("process", "sequential"),
            )
            
            self.crews[crew_id] = config
            
            return {
                "status": "created",
                "crew_id": crew_id,
                "agent_count": len(agents),
                "task_count": len(tasks),
            }
            
        elif action_type == "crew_kickoff":
            # Execute crew
            crew_id = action.get("crew_id")
            inputs = action.get("inputs", {})
            
            if crew_id not in self.crews:
                return {"status": "error", "error": "Crew not found"}
                
            crew_config = self.crews[crew_id]
            
            if not self._crewai_enabled:
                # Mock execution
                results = []
                for task in crew_config.tasks:
                    results.append({
                        "task": task.description,
                        "status": "completed",
                        "output": f"[Mock CrewAI] Task completed: {task.description}",
                    })
                    
                self._event_history.append({
                    "type": "crew_kickoff",
                    "crew_id": crew_id,
                    "results": results,
                })
                
                return {
                    "status": "completed",
                    "crew_id": crew_id,
                    "results": results,
                    "final_output": "Mock crew execution completed",
                }
                
            try:
                from crewai import Crew, Process
                from crewai import Agent as CrewAgent
                from crewai import Task as CrewTask
                
                # Create crew agents
                crew_agents = []
                for agent_config in crew_config.agents:
                    agent = CrewAgent(
                        role=agent_config.role,
                        goal=agent_config.goal,
                        backstory=agent_config.backstory,
                        verbose=agent_config.verbose,
                        allow_delegation=agent_config.allow_delegation,
                    )
                    crew_agents.append(agent)
                    
                # Create crew tasks
                crew_tasks = []
                for task in crew_config.tasks:
                    crew_task = CrewTask(
                        description=task.description,
                        agent=crew_agents[0] if crew_agents else None,
                        expected_output=task.expected_output,
                    )
                    crew_tasks.append(crew_task)
                    
                # Create crew
                process = Process.SEQUENTIAL
                if crew_config.method == CrewMethod.PARALLEL:
                    process = Process.PARALLEL
                elif crew_config.method == CrewMethod.HIERARCHICAL:
                    process = Process.HIERARCHICAL
                    
                crew = Crew(
                    agents=crew_agents,
                    tasks=crew_tasks,
                    process=process,
                    verbose=crew_config.verbose,
                )
                
                # Kickoff
                result = crew.kickoff(inputs=inputs)
                
                return {
                    "status": "completed",
                    "crew_id": crew_id,
                    "result": str(result),
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "crew_id": crew_id,
                }
                
        elif action_type == "crew_stream":
            # Stream crew execution
            crew_id = action.get("crew_id")
            inputs = action.get("inputs", {})
            
            if crew_id not in self.crews:
                return {"status": "error", "error": "Crew not found"}
                
            # Return stream iterator
            return {
                "status": "streaming",
                "crew_id": crew_id,
                "stream_url": f"/crews/{crew_id}/stream",
            }
            
        elif action_type == "agents_list":
            # List all agents
            return {
                "status": "ok",
                "agents": [
                    {
                        "id": agent_id,
                        "role": config.role,
                        "goal": config.goal,
                    }
                    for agent_id, config in self.agents.items()
                ],
            }
            
        elif action_type == "tasks_list":
            # List all tasks
            return {
                "status": "ok",
                "tasks": [
                    {
                        "id": task_id,
                        "description": task.description,
                        "agent_role": task.agent_role,
                        "status": task.status.value,
                    }
                    for task_id, task in self.tasks.items()
                ],
            }
            
        elif action_type == "crews_list":
            # List all crews
            return {
                "status": "ok",
                "crews": [
                    {
                        "id": crew_id,
                        "agent_count": len(config.agents),
                        "task_count": len(config.tasks),
                        "method": config.method.value,
                    }
                    for crew_id, config in self.crews.items()
                ],
            }
            
        return {"status": "unknown_action", "action": action}
        
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        """Stream crew events."""
        for event in self._event_history[-10:]:
            yield event
            
    def close(self) -> None:
        """Clean up resources."""
        self.agents.clear()
        self.tasks.clear()
        self.crews.clear()
        self._event_history.clear()


# FastAPI integration
def create_crewai_app(bridge: CrewAIBridge):
    """Create a FastAPI app for CrewAI bridge."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    
    app = FastAPI(title="CrewAI Bridge", version="0.1.0")
    
    class InvokeInput(BaseModel):
        type: str = "invoke"
        agent_id: str = ""
        crew_id: str = ""
        
    @app.post("/invoke")
    def invoke(req: InvokeInput):
        return bridge.invoke(req.model_dump(exclude={"type"}))
        
    @app.get("/agents")
    def list_agents():
        return bridge.invoke({"type": "agents_list"})
        
    @app.get("/tasks")
    def list_tasks():
        return bridge.invoke({"type": "tasks_list"})
        
    @app.get("/crews")
    def list_crews():
        return bridge.invoke({"type": "crews_list"})
        
    @app.get("/crews/{crew_id}/stream")
    def crew_stream(crew_id: str):
        return bridge.invoke({
            "type": "crew_stream",
            "crew_id": crew_id,
        })
        
    @app.get("/stream")
    def stream():
        return {"events": list(bridge.stream())}
        
    return app