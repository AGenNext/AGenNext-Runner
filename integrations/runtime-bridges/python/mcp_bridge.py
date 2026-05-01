"""
MCP (Model Context Protocol) Bridge for AGenNext Runtime Core.

Provides integration with MCP protocol for AI tools, resources,
prompts, and server management.
"""

import json
import time
from typing import Any, Callable, Dict, Generator, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


class MCPMethod(Enum):
    TOOLS_LIST = "tools_list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_RENDER = "prompts/render"
    COMPLETE = "complete"


@dataclass
class ToolDefinition:
    """MCP tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    handler: Optional[Callable] = None


@dataclass
class Resource:
    """MCP resource."""
    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"


@dataclass
class Prompt:
    """MCP prompt template."""
    name: str
    description: str = ""
    arguments: List[Dict[str, Any]] = field(default_factory=list)
    template: str = ""


@dataclass
class MCPServerConfig:
    """MCP server configuration."""
    name: str
    command: str = ""
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    url: str = ""


class MCPToolHandler:
    """Base class for MCP tool handlers."""
    
    @abstractmethod
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        pass


class MCPBridge:
    """Bridge for MCP protocol execution."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.tools: Dict[str, ToolDefinition] = {}
        self.resources: Dict[str, Resource] = {}
        self.prompts: Dict[str, Prompt] = {}
        self.servers: Dict[str, MCPServerConfig] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._mcp_enabled: bool = False
        
    def init(self, config: Dict[str, Any]) -> None:
        """Initialize the MCP bridge."""
        self.config = config
        
        # Register default MCP tools
        self._register_default_tools()
        
    def _register_default_tools(self):
        """Register default MCP-compliant tools."""
        
        # Tools
        self.tools["mcp_tools_list"] = ToolDefinition(
            name="mcp_tools_list",
            description="List all available MCP tools",
            input_schema={
                "type": "object",
                "properties": {},
            },
            handler=lambda _: self._list_tools(),
        )
        
        self.tools["mcp_tools_call"] = ToolDefinition(
            name="mcp_tools_call",
            description="Call an MCP tool by name",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Tool name to call"},
                    "arguments": {"type": "object", "description": "Tool arguments"},
                },
                "required": ["name"],
            },
            handler=self._call_tool,
        )
        
        # Resources
        self.tools["mcp_resources_list"] = ToolDefinition(
            name="mcp_resources_list",
            description="List all available MCP resources",
            input_schema={
                "type": "object",
                "properties": {},
            },
            handler=lambda _: self._list_resources(),
        )
        
        self.tools["mcp_resources_read"] = ToolDefinition(
            name="mcp_resources_read",
            description="Read an MCP resource by URI",
            input_schema={
                "type": "object",
                "properties": {
                    "uri": {"type": "string", "description": "Resource URI to read"},
                },
                "required": ["uri"],
            },
            handler=self._read_resource,
        )
        
        # Prompts
        self.tools["mcp_prompts_list"] = ToolDefinition(
            name="mcp_prompts_list",
            description="List all available MCP prompts",
            input_schema={
                "type": "object",
                "properties": {},
            },
            handler=lambda _: self._list_prompts(),
        )
        
        self.tools["mcp_prompts_render"] = ToolDefinition(
            name="mcp_prompts_render",
            description="Render an MCP prompt with arguments",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Prompt name"},
                    "arguments": {"type": "object", "description": "Prompt arguments"},
                },
                "required": ["name"],
            },
            handler=self._render_prompt,
        )
        
        # Server
        self.tools["mcp_complete"] = ToolDefinition(
            name="mcp_complete",
            description="Complete MCP server initialization",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Server name"},
                },
                "required": ["name"],
            },
            handler=self._complete_server,
        )
        
    def _list_tools(self, filter_: Optional[str] = None) -> Dict[str, Any]:
        """List MCP tools."""
        tools = [
            {
                "name": name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            }
            for name, tool in self.tools.items()
            if not filter_ or filter_ in name
        ]
        
        return {
            "tools": tools,
        }
        
    def _call_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool."""
        name = arguments.get("name")
        args = arguments.get("arguments", {})
        
        if name not in self.tools:
            return {"error": f"Tool '{name}' not found"}
            
        tool = self.tools[name]
        
        try:
            if tool.handler:
                result = tool.handler(args)
                self._event_history.append({
                    "type": "tool_call",
                    "tool": name,
                    "arguments": args,
                    "result": result,
                })
                return result
            else:
                return {"error": f"Tool '{name}' has no handler"}
                
        except Exception as e:
            return {"error": str(e)}
            
    def _list_resources(self) -> Dict[str, Any]:
        """List MCP resources."""
        resources = [
            {
                "uri": r.uri,
                "name": r.name,
                "description": r.description,
                "mimeType": r.mime_type,
            }
            for r in self.resources.values()
        ]
        
        return {"resources": resources}
        
    def _read_resource(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Read an MCP resource."""
        uri = arguments.get("uri")
        
        if uri not in self.resources:
            return {"error": f"Resource '{uri}' not found"}
            
        resource = self.resources[uri]
        
        # Return resource contents
        return {
            "contents": [
                {
                    "uri": resource.uri,
                    "mimeType": resource.mime_type,
                    "text": f"Resource: {resource.name}",
                }
            ]
        }
        
    def _list_prompts(self) -> Dict[str, Any]:
        """List MCP prompts."""
        prompt_list = [
            {
                "name": p.name,
                "description": p.description,
                "arguments": p.arguments,
            }
            for p in self.prompts.values()
        ]
        
        return {"prompts": prompt_list}
        
    def _render_prompt(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Render an MCP prompt."""
        name = arguments.get("name")
        args = arguments.get("arguments", {})
        
        if name not in self.prompts:
            return {"error": f"Prompt '{name}' not found"}
            
        prompt = self.prompts[name]
        
        # Simple template rendering
        try:
            rendered = prompt.template.format(**args)
        except KeyError:
            rendered = prompt.template
            
        return {
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": rendered,
                    }
                }
            ]
        }
        
    def _complete_server(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Complete MCP server initialization."""
        name = arguments.get("name", "default")
        
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"listChanged": True},
                "prompts": {"listChanged": True},
            },
            "serverInfo": {
                "name": name,
                "version": "0.1.0",
            },
        }
        
    def invoke(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP action."""
        action_type = action.get("type", "invoke")
        
        if action_type == "initialize":
            # MCP initialize (handshake)
            client_info = action.get("client_info", {})
            
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"listChanged": True},
                    "prompts": {"listChanged": True},
                },
                "serverInfo": {
                    "name": "agennext-mcp-bridge",
                    "version": "0.1.0",
                },
                "instructions": "Use tools/call to execute MCP tools",
            }
            
        elif action_type == "tools/list":
            # List tools (MCP protocol)
            return self._list_tools()
            
        elif action_type == "tools/call":
            # Call tool (MCP protocol)
            name = action.get("name")
            arguments = action.get("arguments", {})
            
            return self._call_tool({"name": name, "arguments": arguments})
            
        elif action_type == "resources/list":
            # List resources (MCP protocol)
            return self._list_resources()
            
        elif action_type == "resources/read":
            # Read resource (MCP protocol)
            uri = action.get("uri")
            
            return self._read_resource({"uri": uri})
            
        elif action_type == "prompts/list":
            # List prompts (MCP protocol)
            return self._list_prompts()
            
        elif action_type == "prompts/render":
            # Render prompt (MCP protocol)
            name = action.get("name")
            arguments = action.get("arguments", {})
            
            return self._render_prompt({"name": name, "arguments": arguments})
            
        elif action_type == "tool_register":
            # Register a custom tool
            tool_def = action.get("tool", {})
            name = tool_def.get("name")
            
            if name:
                self.tools[name] = ToolDefinition(
                    name=name,
                    description=tool_def.get("description", ""),
                    input_schema=tool_def.get("inputSchema", {}),
                )
                
                return {"status": "registered", "tool": name}
            
        elif action_type == "resource_register":
            # Register a custom resource
            resource_def = action.get("resource", {})
            uri = resource_def.get("uri")
            
            if uri:
                self.resources[uri] = Resource(
                    uri=uri,
                    name=resource_def.get("name", uri),
                    description=resource_def.get("description", ""),
                    mime_type=resource_def.get("mimeType", "text/plain"),
                )
                
                return {"status": "registered", "uri": uri}
            
        elif action_type == "prompt_register":
            # Register a custom prompt
            prompt_def = action.get("prompt", {})
            name = prompt_def.get("name")
            
            if name:
                self.prompts[name] = Prompt(
                    name=name,
                    description=prompt_def.get("description", ""),
                    arguments=prompt_def.get("arguments", []),
                    template=prompt_def.get("template", ""),
                )
                
                return {"status": "registered", "prompt": name}
            
        return {"status": "unknown_action", "action": action}
        
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        """Stream MCP events."""
        for event in self._event_history[-10:]:
            yield event
            
    def close(self) -> None:
        """Clean up resources."""
        self.tools.clear()
        self.resources.clear()
        self.prompts.clear()
        self.servers.clear()
        self._event_history.clear()


# FastAPI integration with MCP protocol
def create_mcp_bridge_app(bridge: MCPBridge):
    """Create a FastAPI app for MCP bridge."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from typing import Optional, List, Dict, Any
    
    app = FastAPI(title="MCP Bridge", version="2024-11-05")
    
    class InitializeInput(BaseModel):
        protocolVersion: str
        capabilities: Dict[str, Any]
        clientInfo: Optional[Dict[str, Any]] = None
        
    class ToolCallInput(BaseModel):
        name: str
        arguments: Dict[str, Any] = {}
        
    class ResourceReadInput(BaseModel):
        uri: str
        
    class PromptRenderInput(BaseModel):
        name: str
        arguments: Dict[str, Any] = {}
    
    @app.post("/mcp")
    async def mcp_endpoint(request: dict):
        """MCP protocol endpoint - handles all MCP methods."""
        # Route based on method
        method = request.get("method", "")
        params = request.get("params", {})
        
        if method == "initialize":
            return bridge.invoke({
                "type": "initialize",
                "client_info": params.get("clientInfo", {}),
            })
        elif method == "tools/list":
            return bridge.invoke({"type": "tools/list"})
        elif method == "tools/call":
            return bridge.invoke({
                "type": "tools/call",
                "name": params.get("name"),
                "arguments": params.get("arguments", {}),
            })
        elif method == "resources/list":
            return bridge.invoke({"type": "resources/list"})
        elif method == "resources/read":
            return bridge.invoke({"type": "resources/read", "uri": params.get("uri")})
        elif method == "prompts/list":
            return bridge.invoke({"type": "prompts/list"})
        elif method == "prompts/render":
            return bridge.invoke({
                "type": "prompts/render",
                "name": params.get("name"),
                "arguments": params.get("arguments", {}),
            })
        else:
            return {"error": f"Unknown method: {method}"}
            
    @app.post("/initialize")
    def initialize(req: InitializeInput):
        return bridge.invoke({
            "type": "initialize",
            "client_info": req.clientInfo,
        })
        
    @app.get("/tools")
    def list_tools():
        return bridge.invoke({"type": "tools/list"})
        
    @app.post("/tools/call")
    def call_tool(req: ToolCallInput):
        return bridge.invoke({
            "type": "tools/call",
            "name": req.name,
            "arguments": req.arguments,
        })
        
    @app.get("/resources")
    def list_resources():
        return bridge.invoke({"type": "resources/list"})
        
    @app.post("/resources/read")
    def read_resource(req: ResourceReadInput):
        return bridge.invoke({
            "type": "resources/read",
            "uri": req.uri,
        })
        
    @app.get("/prompts")
    def list_prompts():
        return bridge.invoke({"type": "prompts/list"})
        
    @app.post("/prompts/render")
    def render_prompt(req: PromptRenderInput):
        return bridge.invoke({
            "type": "prompts/render",
            "name": req.name,
            "arguments": req.arguments,
        })
        
    @app.get("/stream")
    def stream():
        return {"events": list(bridge.stream())}
        
    return app