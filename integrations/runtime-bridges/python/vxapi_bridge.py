"""
VxAPI Bridge for AGenNext Runtime Core.

Provides integration with VxAPI (Vertex AI API) for Google AI models,
Gemini execution, and cloud-based AI operations.
"""

import json
import time
from typing import Any, Dict, Generator, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class VXModelFamily(Enum):
    GEMINI = "gemini"
    CLAUDE = "claude"
    GPT = "gpt"


class VXSafetyLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class VXConfig:
    """VxAPI configuration."""
    model_family: VXModelFamily = VXModelFamily.GEMINI
    model_name: str = "gemini-2.0-flash"
    temperature: float = 0.7
    max_tokens: int = 8192
    top_p: float = 0.95
    top_k: int = 40
    safety_level: VXSafetyLevel = VXSafetyLevel.MEDIUM
    system_prompt: str = ""


@dataclass
class VXResponse:
    """VxAPI response."""
    content: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    safety_ratings: List[Dict[str, str]] = field(default_factory=list)


class VxAPIBridge:
    """Bridge for VxAPI (Vertex AI) execution."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._vx_enabled: bool = False
        
    def init(self, config: Dict[str, Any]) -> None:
        """Initialize the VxAPI bridge."""
        self.config = config
        
        # Try to import google-generativeai or anthropic
        try:
            import google.generativeai
            self._vx_enabled = True
            self._google = google.generativeai
        except ImportError:
            try:
                import anthropic
                self._vx_enabled = True
                self._anthropic = anthropic
            except ImportError:
                pass
            
    def _call_gemini(self, message: str, config: VXConfig) -> VXResponse:
        """Call Google Gemini."""
        try:
            import google.generativeai as genai
            
            # Configure
            genai.configure(api_key=self.config.get("api_key", "mock"))
            
            model = genai.GenerativeModel(config.model_name)
            
            # Generate
            generation_config = {
                "temperature": config.temperature,
                "max_output_tokens": config.max_tokens,
                "top_p": config.top_p,
                "top_k": config.top_k,
            }
            
            response = model.generate_content(
                message,
                generation_config=generation_config,
            )
            
            return VXResponse(
                content=response.text,
                usage={"input_tokens": 100, "output_tokens": 100},
                finish_reason="stop",
            )
            
        except Exception as e:
            return VXResponse(
                content=f"Error: {str(e)}",
                usage={},
                finish_reason="error",
            )
            
    def _call_anthropic(self, message: str, config: VXConfig) -> VXResponse:
        """Call Anthropic Claude."""
        try:
            import anthropic
            
            client = anthropic.Anthropic(
                api_key=self.config.get("api_key", "mock")
            )
            
            response = client.messages.create(
                model=config.model_name,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=[{"role": "user", "content": message}],
            )
            
            return VXResponse(
                content=response.content[0].text,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                finish_reason=str(response.stop_reason),
            )
            
        except Exception as e:
            return VXResponse(
                content=f"Error: {str(e)}",
                usage={},
                finish_reason="error",
            )
            
    def invoke(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a VxAPI action."""
        action_type = action.get("type", "invoke")
        
        if action_type == "invoke":
            # Invoke model
            conv_id = action.get("conv_id", "default")
            message = action.get("message", "")
            model_config = action.get("config", {})
            
            if conv_id not in self.conversations:
                self.conversations[conv_id] = []
                
            config = VXConfig(
                model_family=VXModelFamily(model_config.get("model_family", "gemini")),
                model_name=model_config.get("model_name", "gemini-2.0-flash"),
                temperature=model_config.get("temperature", 0.7),
                max_tokens=model_config.get("max_tokens", 8192),
            )
            
            # Add to conversation
            self.conversations[conv_id].append({
                "role": "user",
                "content": message,
            })
            
            # Call appropriate model
            if config.model_family == VXModelFamily.GEMINI:
                response = self._call_gemini(message, config)
            elif config.model_family == VXModelFamily.CLAUDE:
                response = self._call_anthropic(message, config)
            else:
                response = VXResponse(content=f"[VxAPI] {message}")
            
            # Add response
            self.conversations[conv_id].append({
                "role": "assistant",
                "content": response.content,
            })
            
            self._event_history.append({
                "type": "invoke",
                "conv_id": conv_id,
                "model": config.model_name,
            })
            
            return {
                "status": "ok",
                "response": response.content,
                "usage": response.usage,
                "finish_reason": response.finish_reason,
                "conv_id": conv_id,
            }
            
        elif action_type == "stream":
            # Stream response
            conv_id = action.get("conv_id", "default")
            message = action.get("message", "")
            
            for chunk in f"[VxAPI Stream] {message}".split():
                yield {"type": "chunk", "content": chunk + " "}
                
        elif action_type == "conversation_get":
            # Get conversation
            conv_id = action.get("conv_id", "default")
            messages = self.conversations.get(conv_id, [])
            
            return {
                "status": "ok",
                "conv_id": conv_id,
                "messages": messages,
            }
            
        elif action_type == "conversation_clear":
            # Clear conversation
            conv_id = action.get("conv_id", "default")
            self.conversations[conv_id] = []
            
            return {
                "status": "ok",
                "conv_id": conv_id,
            }
            
        return {"status": "unknown_action", "action": action}
        
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        """Stream VxAPI events."""
        for event in self._event_history[-10:]:
            yield event
            
    def close(self) -> None:
        """Clean up resources."""
        self.conversations.clear()
        self._event_history.clear()


# FastAPI integration
def create_vxapi_app(bridge: VxAPIBridge):
    """Create a FastAPI app for VxAPI bridge."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from typing import Optional, Dict, Any
    
    app = FastAPI(title="VxAPI Bridge", version="0.1.0")
    
    class ChatInput(BaseModel):
        conv_id: str = "default"
        message: str = ""
        config: Dict[str, Any] = {}
        
    @app.post("/invoke")
    def invoke(req: ChatInput):
        return bridge.invoke({
            "type": "invoke",
            "conv_id": req.conv_id,
            "message": req.message,
            "config": req.config,
        })
        
    @app.get("/conversations/{conv_id}")
    def get_conversation(conv_id: str):
        return bridge.invoke({
            "type": "conversation_get",
            "conv_id": conv_id,
        })
        
    @app.delete("/conversations/{conv_id}")
    def clear_conversation(conv_id: str):
        return bridge.invoke({
            "type": "conversation_clear",
            "conv_id": conv_id,
        })
        
    @app.get("/stream")
    def stream():
        return {"events": list(bridge.stream())}
        
    return app