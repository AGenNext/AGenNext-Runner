"""
LangGraph Bridge for AGenNext Runtime Core.

Provides integration with LangGraph for agentic workflow execution,
node-based streaming, and state management.
"""

import os
from typing import Any, Dict, Generator, Optional
from dataclasses import dataclass, field
from enum import Enum


class NodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class GraphNode:
    """Represents a node in the LangGraph."""
    name: str
    status: NodeStatus = NodeStatus.PENDING
    input: Dict[str, Any] = field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LangGraphBridge:
    """Bridge for LangGraph agent execution."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.graph: Optional[Any] = None
        self.nodes: Dict[str, GraphNode] = {}
        self.state: Dict[str, Any] = {}
        self.checkpointer: Optional[Any] = None
        
    def init(self, config: Dict[str, Any]) -> None:
        """Initialize the LangGraph bridge."""
        self.config = config
        
        # Try to import langgraph
        try:
            from langgraph.graph import StateGraph, END
            from langgraph.prebuilt import create_react_agent
            
            # Build default graph based on config
            builder = StateGraph(config.get("schema", dict))
            
            # Add nodes
            for node_name in config.get("nodes", []):
                builder.add_node(node_name, self._default_node)
            
            # Add edges
            edges = config.get("edges", [])
            for i, edge in enumerate(edges):
                if i < len(edges) - 1:
                    builder.add_edge(edge, edges[i + 1])
                else:
                    builder.add_edge(edge, END)
            
            self.graph = builder.compile()
            
        except ImportError:
            # Fallback: create mock graph
            self.graph = None
            
    def _default_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Default node handler."""
        return state
        
    def invoke(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a LangGraph invocation."""
        action_type = action.get("type", "run")
        
        if action_type == "run":
            # Run the graph
            input_data = action.get("input", {})
            thread_config = action.get("config", {})
            
            if self.graph:
                try:
                    result = self.graph.invoke(input_data, thread_config)
                    return {
                        "status": "completed",
                        "result": result,
                        "node_outputs": self._get_node_outputs(),
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "error": str(e),
                    }
            else:
                # Mock execution
                self.state = input_data
                return {
                    "status": "completed",
                    "result": input_data,
                    "node_outputs": {},
                }
                
        elif action_type == "stream":
            # Return stream iterator
            return {
                "status": "streaming",
                "stream_url": "/stream",
            }
            
        elif action_type == "get_state":
            # Get current state
            thread_id = action.get("thread_id")
            if self.checkpointer and thread_id:
                state = self.checkpointer.get(thread_id)
            else:
                state = self.state
            return {
                "status": "ok",
                "state": state,
            }
            
        elif action_type == "update_state":
            # Update state
            updates = action.get("updates", {})
            self.state.update(updates)
            return {
                "status": "ok",
                "state": self.state,
            }
            
        return {"status": "unknown_action", "action": action}
        
    def _get_node_outputs(self) -> Dict[str, Any]:
        """Get outputs from all nodes."""
        return {
            name: {
                "status": node.status.value,
                "output": node.output,
            }
            for name, node in self.nodes.items()
        }
        
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        """Stream node events."""
        if self.graph:
            for chunk in self.graph.stream(self.state):
                yield {
                    "type": "node_chunk",
                    "node": chunk.get("node"),
                    "chunk": chunk,
                }
        else:
            yield {"type": "no_graph", "status": "uninitialized"}
            
    def close(self) -> None:
        """Clean up resources."""
        self.graph = None
        self.nodes.clear()
        self.state.clear()


# FastAPI integration
def create_langgraph_app(bridge: LangGraphBridge):
    """Create a FastAPI app for LangGraph bridge."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    
    app = FastAPI(title="LangGraph Bridge", version="0.1.0")
    
    class InvokeInput(BaseModel):
        type: str = "run"
        input: Dict[str, Any] = {}
        config: Dict[str, Any] = {}
        
    @app.post("/invoke")
    def invoke(req: InvokeInput):
        return bridge.invoke(req.model_dump(exclude={"type"}))
        
    @app.get("/stream")
    def stream():
        return {"status": "stream", "events": list(bridge.stream())}
        
    @app.get("/state")
    def get_state():
        return {"state": bridge.state}
        
    return app