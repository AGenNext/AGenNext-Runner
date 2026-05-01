"""
MetaGPT Bridge for AGenNext Runtime Core.
Provides integration with MetaGPT for SOP-driven multi-agent collaboration,
role assignment, and structured team workflows.
"""
import json
import time
import uuid
from typing import Any, Dict, Generator, List, Optional
from dataclasses import dataclass, field
from enum import Enum

class RoleType(Enum):
    ARCHITECT = "architect"
    PROJECT_MANAGER = "project_manager"
    ENGINEER = "engineer"
    REVIEWER = "reviewer"
    QA = "qa"
    CUSTOM = "custom"

class SOPPhase(Enum):
    REQUIREMENT = "requirement"
    ANALYSIS = "analysis"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    DEPLOYMENT = "deployment"

@dataclass
class Role:
    """MetaGPT role definition."""
    name: str
    role_type: RoleType = RoleType.CUSTOM
    instructions: str = ""
    constraints: List[str] = field(default_factory=list)

@dataclass
class SOPWorkflow:
    """SOP (Standard Operating Procedure) workflow."""
    name: str
    phases: List[SOPPhase] = field(default_factory=list)
    max_retries: int = 3

@dataclass
class TeamMember:
    """Team member in a MetaGPT team."""
    id: str
    role: Role
    status: str = "idle"
    tasks_completed: int = 0
    last_active: float = field(default_factory=time.time)

class MetaGPTBridge:
    """Bridge for MetaGPT execution."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.teams: Dict[str, Dict[str, Any]] = {}
        self.roles: Dict[str, Role] = {}
        self.sops: Dict[str, SOPWorkflow] = {}
        self._event_history: List[Dict[str, Any]] = []
        
    def init(self, config: Dict[str, Any]) -> None:
        """Initialize the MetaGPT bridge."""
        self.config = config
        
    def invoke(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a MetaGPT action."""
        action_type = action.get("type", "invoke")
        
        if action_type == "role_create":
            # Create a role
            role_id = action.get("role_id", f"role_{uuid.uuid4().hex[:8]}")
            role_def = action.get("role", {})
            
            role = Role(
                name=role_def.get("name", "Role"),
                role_type=RoleType(role_def.get("role_type", "custom")),
                instructions=role_def.get("instructions", ""),
                constraints=role_def.get("constraints", []),
            )
            self.roles[role_id] = role
            return {"status": "created", "role_id": role_id, "name": role.name}
        
        elif action_type == "sop_create":
            # Create SOP workflow
            sop_id = action.get("sop_id", f"sop_{uuid.uuid4().hex[:8]}")
            sop_def = action.get("sop", {})
            
            sop = SOPWorkflow(
                name=sop_def.get("name", "SOP"),
                phases=[SOPPhase(p) for p in sop_def.get("phases", [])],
                max_retries=sop_def.get("max_retries", 3),
            )
            self.sops[sop_id] = sop
            return {"status": "created", "sop_id": sop_id, "name": sop.name, "phases": [p.value for p in sop.phases]}
        
        elif action_type == "team_create":
            # Create team
            team_id = action.get("team_id", f"team_{uuid.uuid4().hex[:8]}")
            team_def = action.get("team", {})
            
            self.teams[team_id] = {
                "id": team_id,
                "name": team_def.get("name", "Team"),
                "members": {},
                "sop_id": team_def.get("sop_id"),
                "current_phase": None,
                "status": "initialized",
            }
            return {"status": "created", "team_id": team_id, "name": team_def.get("name")}
        
        elif action_type == "team_member_add":
            # Add member to team
            team_id = action.get("team_id")
            role_id = action.get("role_id")
            
            if team_id not in self.teams:
                return {"status": "error", "error": "Team not found"}
            if role_id not in self.roles:
                return {"status": "error", "error": "Role not found"}
            
            member = TeamMember(id=role_id, role=self.roles[role_id])
            self.teams[team_id]["members"][role_id] = member
            return {"status": "added", "team_id": team_id, "member_id": role_id}
        
        elif action_type == "team_execute_phase":
            # Execute SOP phase
            team_id = action.get("team_id")
            phase = action.get("phase")
            context = action.get("context", {})
            
            if team_id not in self.teams:
                return {"status": "error", "error": "Team not found"}
            
            team = self.teams[team_id]
            
            # Execute phase for each member
            results = []
            for member_id, member in team["members"].items():
                member.status = "working"
                result = f"[{member.role.name}] Executing {phase}"
                member.tasks_completed += 1
                member.last_active = time.time()
                results.append({"member": member_id, "result": result, "completed": True})
            
            team["current_phase"] = phase
            team["status"] = "phase_complete"
            
            self._event_history.append({
                "type": "phase_execute", "team_id": team_id, "phase": phase,
                "member_count": len(team["members"]), "results": results,
            })
            
            return {
                "status": "completed", "team_id": team_id, "phase": phase,
                "results": results, "members_executed": len(results),
            }
        
        elif action_type == "team_workflow_run":
            # Run full workflow
            team_id = action.get("team_id")
            initial_context = action.get("context", {})
            
            if team_id not in self.teams:
                return {"status": "error", "error": "Team not found"}
            
            team = self.teams[team_id]
            sop_id = team.get("sop_id")
            
            if sop_id and sop_id in self.sops:
                sop = self.sops[sop_id]
                phases = sop.phases
            else:
                phases = list(SOPPhase)
            
            all_results = {}
            for phase in phases:
                team["current_phase"] = phase.value
                phase_results = []
                for member_id, member in team["members"].items():
                    member.status = "working"
                    result = f"[{member.role.name}] {phase.value}"
                    member.tasks_completed += 1
                    phase_results.append({"member": member_id, "result": result})
                all_results[phase.value] = phase_results
            
            team["status"] = "workflow_complete"
            
            return {
                "status": "completed", "team_id": team_id,
                "phases_completed": len(phases), "results": all_results,
            }
        
        elif action_type == "team_status":
            # Get team status
            team_id = action.get("team_id")
            
            if team_id not in self.teams:
                return {"status": "error", "error": "Team not found"}
            
            team = self.teams[team_id]
            return {
                "status": "ok", "team_id": team_id,
                "name": team["name"], "status": team["status"],
                "current_phase": team["current_phase"],
                "members": {
                    mid: {"role": m.role.name, "status": m.status, "tasks": m.tasks_completed}
                    for mid, m in team["members"].items()
                },
            }
        
        elif action_type == "roles_list":
            return {"status": "ok", "roles": [{"id": k, "name": v.name, "type": v.role_type.value} for k, v in self.roles.items()]}
        
        elif action_type == "sops_list":
            return {"status": "ok", "sops": [{"id": k, "name": v.name, "phases": len(v.phases)} for k, v in self.sops.items()]}
        
        elif action_type == "teams_list":
            return {"status": "ok", "teams": [{"id": k, "name": v["name"], "status": v["status"]} for k, v in self.teams.items()]}
        
        return {"status": "unknown_action", "action": action}
    
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        for event in self._event_history[-10:]:
            yield event
    
    def close(self) -> None:
        self.teams.clear()
        self.roles.clear()
        self.sops.clear()
        self._event_history.clear()

def create_metagpt_bridge():
    from fastapi import FastAPI
    from pydantic import BaseModel
    app = FastAPI(title="MetaGPT Bridge", version="0.1.0")
    bridge = MetaGPTBridge()
    
    @app.post("/roles/create")
    def create_role(req: dict): return bridge.invoke({"type": "role_create", "role": req})
    
    @app.post("/sops/create")
    def create_sop(req: dict): return bridge.invoke({"type": "sop_create", "sop": req})
    
    @app.post("/teams/create")
    def create_team(req: dict): return bridge.invoke({"type": "team_create", "team": req})
    
    @app.post("/teams/{team_id}/members/add")
    def add_member(team_id: str, req: dict): return bridge.invoke({"type": "team_member_add", "team_id": team_id, "role_id": req.get("role_id")})
    
    @app.post("/teams/{team_id}/phase")
    def execute_phase(team_id: str, req: dict): return bridge.invoke({"type": "team_execute_phase", "team_id": team_id, "phase": req.get("phase")})
    
    @app.post("/teams/{team_id}/run")
    def run_workflow(team_id: str, req: dict): return bridge.invoke({"type": "team_workflow_run", "team_id": team_id, "context": req})
    
    @app.get("/teams/{team_id}")
    def team_status(team_id: str): return bridge.invoke({"type": "team_status", "team_id": team_id})
    
    @app.get("/roles")
    def list_roles(): return bridge.invoke({"type": "roles_list"})
    
    @app.get("/sops")
    def list_sops(): return bridge.invoke({"type": "sops_list"})
    
    @app.get("/teams")
    def list_teams(): return bridge.invoke({"type": "teams_list"})
    
    return app, bridge