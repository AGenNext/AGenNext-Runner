"""
AgentField Bridge for AGenNext Runtime Core.

Provides integration with AgentField (formerly AgentOps) for form-based
agent execution with field validation, autosave, and state management.
"""

import json
import time
from typing import Any, Dict, Generator, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class FieldType(Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    EMAIL = "email"
    PHONE = "phone"
    SELECT = "select"
    MULTISELECT = "multiselect"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    FILE = "file"
    DATE = "date"
    DATETIME = "datetime"


class ValidationLevel(Enum):
    NONE = "none"
    WARN = "warn"
    ERROR = "error"


@dataclass
class FieldDefinition:
    """Definition of a form field."""
    name: str
    field_type: FieldType = FieldType.TEXT
    label: str = ""
    placeholder: str = ""
    required: bool = False
    default_value: Any = None
    options: List[str] = field(default_factory=list)
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    validation_level: ValidationLevel = ValidationLevel.ERROR
    help_text: str = ""
    

@dataclass
class FieldValue:
    """Value of a form field with validation."""
    name: str
    value: Any = None
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    last_modified: float = field(default_factory=time.time)


@dataclass
class FormState:
    """State of an AgentField form."""
    form_id: str
    fields: Dict[str, FieldValue] = field(default_factory=dict)
    status: str = "draft"  # draft, submitting, submitted, error
    version: int = 1
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    submitted_at: Optional[float] = None
    autosave_enabled: bool = True
    autosave_interval: int = 30  # seconds


class AgentFieldBridge:
    """Bridge for AgentField form execution."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.field_definitions: Dict[str, FieldDefinition] = {}
        self.form_states: Dict[str, FormState] = {}
        self._event_history: List[Dict[str, Any]] = []
        
    def init(self, config: Dict[str, Any]) -> None:
        """Initialize the AgentField bridge."""
        self.config = config
        
        # Parse field definitions
        field_defs = config.get("fields", [])
        for fd in field_defs:
            if isinstance(fd, dict):
                name = fd.get("name", "")
                if name:
                    self.field_definitions[name] = FieldDefinition(
                        name=name,
                        field_type=FieldType(fd.get("type", "text")),
                        label=fd.get("label", ""),
                        placeholder=fd.get("placeholder", ""),
                        required=fd.get("required", False),
                        default_value=fd.get("default"),
                        options=fd.get("options", []),
                        min_length=fd.get("min_length"),
                        max_length=fd.get("max_length"),
                        pattern=fd.get("pattern"),
                        validation_level=ValidationLevel(
                            fd.get("validation_level", "error")
                        ),
                        help_text=fd.get("help_text", ""),
                    )
                    
    def _validate_field(self, field_def: FieldValue) -> FieldValue:
        """Validate a single field value."""
        definition = self.field_definitions.get(field_def.name)
        if not definition:
            return field_def
            
        # Required check
        if definition.required and (field_def.value is None or field_def.value == ""):
            field_def.errors.append(f"{definition.label} is required")
            field_def.is_valid = False
            
        # Type-specific validation
        if field_def.value is not None:
            if definition.field_type == FieldType.EMAIL:
                if "@" not in str(field_def.value):
                    field_def.errors.append("Invalid email format")
                    field_def.is_valid = False
                    
            elif definition.field_type == FieldType.NUMBER:
                try:
                    float(str(field_def.value))
                except ValueError:
                    field_def.errors.append("Must be a number")
                    field_def.is_valid = False
                    
            elif definition.field_type in (FieldType.TEXT, FieldType.TEXTAREA):
                if definition.min_length and len(str(field_def.value)) < definition.min_length:
                    field_def.errors.append(
                        f"Minimum {definition.min_length} characters"
                    )
                    field_def.is_valid = False
                    
                if definition.max_length and len(str(field_def.value)) > definition.max_length:
                    field_def.errors.append(
                        f"Maximum {definition.max_length} characters"
                    )
                    field_def.is_valid = False
                    
            elif definition.field_type == FieldType.PATTERN:
                if definition.pattern:
                    import re
                    if not re.match(definition.pattern, str(field_def.value)):
                        field_def.errors.append("Pattern mismatch")
                        field_def.is_valid = False
        
        return field_def
        
    def invoke(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an AgentField action."""
        action_type = action.get("type", "form_init")
        
        if action_type == "form_init":
            # Create new form
            form_id = action.get("form_id", f"form_{int(time.time())}")
            initial_values = action.get("values", {})
            
            form_state = FormState(
                form_id=form_id,
                autosave_enabled=action.get("autosave", True),
                autosave_interval=action.get("autosave_interval", 30),
            )
            
            # Initialize fields with values
            for name, value in initial_values.items():
                field_val = FieldValue(name=name, value=value)
                if name in self.field_definitions:
                    field_val = self._validate_field(field_val)
                form_state.fields[name] = field_val
                
            self.form_states[form_id] = form_state
            self._event_history.append({
                "type": "form_init",
                "form_id": form_id,
                "timestamp": time.time(),
            })
            
            return {
                "status": "ok",
                "form_id": form_id,
                "form_state": asdict(form_state),
            }
            
        elif action_type == "form_update":
            # Update field values
            form_id = action.get("form_id")
            updates = action.get("updates", {})
            
            if form_id not in self.form_states:
                return {"status": "error", "error": "Form not found"}
                
            form_state = self.form_states[form_id]
            
            for name, value in updates.items():
                field_val = FieldValue(name=name, value=value)
                if name in self.field_definitions:
                    field_val = self._validate_field(field_val)
                form_state.fields[name] = field_val
                
            form_state.updated_at = time.time()
            form_state.version += 1
            
            self._event_history.append({
                "type": "form_update",
                "form_id": form_id,
                "timestamp": time.time(),
            })
            
            return {
                "status": "ok",
                "form_id": form_id,
                "version": form_state.version,
                "fields": {
                    name: asdict(fv) 
                    for name, fv in form_state.fields.items()
                },
            }
            
        elif action_type == "form_validate":
            # Validate entire form
            form_id = action.get("form_id")
            
            if form_id not in self.form_states:
                return {"status": "error", "error": "Form not found"}
                
            form_state = self.form_states[form_id]
            all_valid = True
            all_errors = []
            all_warnings = []
            
            for name, field_val in form_state.fields.items():
                if name in self.field_definitions:
                    field_val = self._validate_field(field_val)
                    form_state.fields[name] = field_val
                    
                if not field_val.is_valid:
                    all_valid = False
                    all_errors.extend(field_val.errors)
                all_warnings.extend(field_val.warnings)
                
            return {
                "status": "ok" if all_valid else "invalid",
                "form_id": form_id,
                "valid": all_valid,
                "errors": all_errors,
                "warnings": all_warnings,
            }
            
        elif action_type == "form_submit":
            # Submit form
            form_id = action.get("form_id")
            
            if form_id not in self.form_states:
                return {"status": "error", "error": "Form not found"}
                
            form_state = self.form_states[form_id]
            form_state.status = "submitting"
            
            # Validate first
            for name, field_val in form_state.fields.items():
                if name in self.field_definitions:
                    field_val = self._validate_field(field_val)
                    form_state.fields[name] = field_val
                    
                    if not field_val.is_valid:
                        form_state.status = "error"
                        return {
                            "status": "error",
                            "form_id": form_id,
                            "errors": field_val.errors,
                        }
            
            form_state.status = "submitted"
            form_state.submitted_at = time.time()
            
            self._event_history.append({
                "type": "form_submit",
                "form_id": form_id,
                "timestamp": time.time(),
            })
            
            return {
                "status": "submitted",
                "form_id": form_id,
                "submitted_at": form_state.submitted_at,
            }
            
        elif action_type == "form_get":
            # Get form state
            form_id = action.get("form_id")
            
            if form_id not in self.form_states:
                return {"status": "error", "error": "Form not found"}
                
            return {
                "status": "ok",
                "form": asdict(self.form_states[form_id]),
            }
            
        elif action_type == "form_delete":
            # Delete form
            form_id = action.get("form_id")
            
            if form_id in self.form_states:
                del self.form_states[form_id]
                
            return {"status": "ok", "form_id": form_id}
            
        return {"status": "unknown_action", "action": action}
        
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        """Stream form events (autosave, validation, etc.)."""
        for event in self._event_history[-10:]:  # Last 10 events
            yield event
            
    def close(self) -> None:
        """Clean up resources."""
        self.form_states.clear()
        self.field_definitions.clear()
        self._event_history.clear()


# FastAPI integration
def create_agentfield_app(bridge: AgentFieldBridge):
    """Create a FastAPI app for AgentField bridge."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    
    app = FastAPI(title="AgentField Bridge", version="0.1.0")
    
    class InvokeInput(BaseModel):
        type: str = "form_init"
        form_id: Optional[str] = None
        values: Dict[str, Any] = {}
        updates: Dict[str, Any] = {}
        autosave: bool = True
        
    @app.post("/invoke")
    def invoke(req: InvokeInput):
        return bridge.invoke(req.model_dump(exclude={"type"}))
        
    @app.get("/forms")
    def list_forms():
        return {
            "forms": list(bridge.form_states.keys())
        }
        
    @app.get("/stream")
    def stream():
        return {"events": list(bridge.stream())}
        
    return app