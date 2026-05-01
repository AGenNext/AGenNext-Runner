"""
Pydantic Bridge for AGenNext Runtime Core.

Provides integration with Pydantic for data validation, schema generation,
and AI response modeling.
"""

import json
import time
from typing import Any, Callable, Dict, Generator, List, Optional, Type
from dataclasses import dataclass, field
from enum import Enum


class ValidationMode(Enum):
    STRICT = "strict"
    LAX = "lax"
    WARN = "warn"


class SchemaFormat(Enum):
    JSON = "json"
    TYPESCRIPT = "typescript"
    PYTHON = "python"
    OPENAPI = "openapi"


@dataclass
class FieldSchema:
    """Schema for a field."""
    name: str
    field_type: str
    required: bool = True
    default: Any = None
    description: str = ""
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    enum: List[Any] = field(default_factory=list)


@dataclass
class ModelSchema:
    """Schema for a Pydantic model."""
    name: str
    description: str = ""
    fields: Dict[str, FieldSchema] = field(default_factory=dict)


class PydanticBridge:
    """Bridge for Pydantic validation and schema generation."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.schemas: Dict[str, ModelSchema] = {}
        self.validations: Dict[str, List[Dict[str, Any]]] = {}
        self._event_history: List[Dict[str, Any]] = []
        
    def init(self, config: Dict[str, Any]) -> None:
        """Initialize the Pydantic bridge."""
        self.config = config
        
    def invoke(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Pydantic action."""
        action_type = action.get("type", "invoke")
        
        if action_type == "schema_create":
            # Create a schema
            schema_name = action.get("name")
            schema_def = action.get("schema", {})
            
            model_schema = ModelSchema(
                name=schema_name,
                description=schema_def.get("description", ""),
            )
            
            for field_name, field_def in schema_def.get("fields", {}).items():
                model_schema.fields[field_name] = FieldSchema(
                    name=field_name,
                    field_type=field_def.get("type", "str"),
                    required=field_def.get("required", True),
                    default=field_def.get("default"),
                    description=field_def.get("description", ""),
                    pattern=field_def.get("pattern"),
                    min_length=field_def.get("min_length"),
                    max_length=field_def.get("max_length"),
                    minimum=field_def.get("minimum"),
                    maximum=field_def.get("maximum"),
                    enum=field_def.get("enum", []),
                )
                
            self.schemas[schema_name] = model_schema
            
            return {
                "status": "created",
                "schema_name": schema_name,
                "field_count": len(model_schema.fields),
            }
            
        elif action_type == "schema_validate":
            # Validate data against schema
            schema_name = action.get("schema_name")
            data = action.get("data", {})
            mode = action.get("mode", "strict")
            
            if schema_name not in self.schemas:
                return {"status": "error", "error": "Schema not found"}
                
            schema = self.schemas[schema_name]
            errors = []
            warnings = []
            
            for field_name, field_def in schema.fields.items():
                value = data.get(field_name)
                
                # Required check
                if field_def.required and value is None:
                    errors.append(f"Field '{field_name}' is required")
                    continue
                    
                if value is None:
                    continue
                    
                # Type check
                expected_type = field_def.field_type.lower()
                if expected_type == "str" and not isinstance(value, str):
                    errors.append(f"Field '{field_name}' must be string")
                elif expected_type == "int" and not isinstance(value, int):
                    errors.append(f"Field '{field_name}' must be integer")
                elif expected_type == "float" and not isinstance(value, (int, float)):
                    errors.append(f"Field '{field_name}' must be number")
                elif expected_type == "bool" and not isinstance(value, bool):
                    errors.append(f"Field '{field_name}' must be boolean")
                elif expected_type == "list" and not isinstance(value, list):
                    errors.append(f"Field '{field_name}' must be list")
                elif expected_type == "dict" and not isinstance(value, dict):
                    errors.append(f"Field '{field_name}' must be object")
                    
                # String validations
                if isinstance(value, str):
                    if field_def.min_length and len(value) < field_def.min_length:
                        errors.append(f"Field '{field_name}' must be at least {field_def.min_length} chars")
                    if field_def.max_length and len(value) > field_def.max_length:
                        errors.append(f"Field '{field_name}' must be at most {field_def.max_length} chars")
                    if field_def.pattern:
                        import re
                        if not re.match(field_def.pattern, value):
                            errors.append(f"Field '{field_name}' doesn't match pattern")
                            
                # Numeric validations
                if isinstance(value, (int, float)):
                    if field_def.minimum is not None and value < field_def.minimum:
                        errors.append(f"Field '{field_name}' must be >= {field_def.minimum}")
                    if field_def.maximum is not None and value > field_def.maximum:
                        errors.append(f"Field '{field_name}' must be <= {field_def.maximum}")
                        
                # Enum validation
                if field_def.enum and value not in field_def.enum:
                    errors.append(f"Field '{field_name}' must be one of: {field_def.enum}")
            
            valid = len(errors) == 0
            
            result = {
                "status": "valid" if valid else "invalid",
                "schema_name": schema_name,
                "valid": valid,
                "errors": errors,
                "warnings": warnings,
            }
            
            # Store validation result
            if schema_name not in self.validations:
                self.validations[schema_name] = []
            self.validations[schema_name].append(result)
            
            return result
            
        elif action_type == "schema_generate":
            # Generate Pydantic model code
            schema_name = action.get("schema_name")
            format_ = action.get("format", "python")
            
            if schema_name not in self.schemas:
                return {"status": "error", "error": "Schema not found"}
                
            schema = self.schemas[schema_name]
            
            if format_ == "python":
                code = self._generate_python(schema)
            elif format_ == "typescript":
                code = self._generate_typescript(schema)
            elif format_ == "json":
                code = self._generate_json(schema)
            elif format_ == "openapi":
                code = self._generate_openapi(schema)
            else:
                code = self._generate_python(schema)
                
            return {
                "status": "ok",
                "schema_name": schema_name,
                "format": format_,
                "code": code,
            }
            
        elif action_type == "schema_list":
            # List all schemas
            return {
                "status": "ok",
                "schemas": [
                    {
                        "name": name,
                        "description": schema.description,
                        "field_count": len(schema.fields),
                    }
                    for name, schema in self.schemas.items()
                ],
            }
            
        elif action_type == "schema_get":
            # Get schema details
            schema_name = action.get("schema_name")
            
            if schema_name not in self.schemas:
                return {"status": "error", "error": "Schema not found"}
                
            schema = self.schemas[schema_name]
            
            return {
                "status": "ok",
                "schema": {
                    "name": schema.name,
                    "description": schema.description,
                    "fields": {
                        name: {
                            "type": f.field_type,
                            "required": f.required,
                            "default": f.default,
                            "description": f.description,
                        }
                        for name, f in schema.fields.items()
                    },
                },
            }
            
        elif action_type == "schema_delete":
            # Delete schema
            schema_name = action.get("schema_name")
            
            if schema_name in self.schemas:
                del self.schemas[schema_name]
                
            return {
                "status": "ok",
                "schema_name": schema_name,
            }
            
        elif action_type == "validation_history":
            # Get validation history
            schema_name = action.get("schema_name")
            
            if schema_name and schema_name in self.validations:
                return {
                    "status": "ok",
                    "validations": self.validations[schema_name],
                }
            else:
                return {
                    "status": "ok",
                    "validations": sum(self.validations.values(), []),
                }
                
        return {"status": "unknown_action", "action": action}
        
    def _generate_python(self, schema: ModelSchema) -> str:
        """Generate Python Pydantic model code."""
        lines = [
            f"\"\"\"{schema.description}\"\"\"",
            "from pydantic import BaseModel, Field",
            "from typing import Optional",
            "",
            f"class {schema.name}(BaseModel):",
        ]
        
        for field_name, field_def in schema.fields.items():
            type_hint = field_def.field_type
            if type_hint == "str":
                type_hint = "str"
            elif type_hint == "int":
                type_hint = "int"
            elif type_hint == "float":
                type_hint = "float"
            elif type_hint == "bool":
                type_hint = "bool"
            elif type_hint == "list":
                type_hint = "list"
            elif type_hint == "dict":
                type_hint = "dict"
                
            if not field_def.required:
                type_hint = f"Optional[{type_hint}]"
                
            default = ""
            if field_def.default is not None:
                if isinstance(field_def.default, str):
                    default = f' = "{field_def.default}"'
                else:
                    default = f" = {field_def.default}"
            elif not field_def.required:
                default = " = None"
                
            description = field_def.description
            if description:
                lines.append(f'    {field_name}: {type_hint} = Field(default{default}, description="{description}")'.replace("default=", "").replace("= None", ""))
            else:
                lines.append(f"    {field_name}: {type_hint}{default}")
                
        return "\n".join(lines)
        
    def _generate_typescript(self, schema: ModelSchema) -> str:
        """Generate TypeScript interface."""
        lines = [
            f"/** {schema.description} */",
            f"export interface {schema.name} {{",
        ]
        
        for field_name, field_def in schema.fields.items():
            optional = "" if field_def.required else "?"
            type_hint = field_def.field_type
            if type_hint == "str":
                type_hint = "string"
            elif type_hint in ("int", "float"):
                type_hint = "number"
            elif type_hint == "bool":
                type_hint = "boolean"
            elif type_hint == "list":
                type_hint = "any[]"
            elif type_hint == "dict":
                type_hint = "Record<string, any>"
                
            lines.append(f"    {field_name}{optional}: {type_hint};")
            
        lines.append("}")
        return "\n".join(lines)
        
    def _generate_json(self, schema: ModelSchema) -> str:
        """Generate JSON Schema."""
        schema_dict = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": schema.name,
            "description": schema.description,
            "type": "object",
            "properties": {},
            "required": [],
        }
        
        for field_name, field_def in schema.fields.items():
            prop = {"description": field_def.description}
            
            type_map = {
                "str": "string",
                "int": "integer", 
                "float": "number",
                "bool": "boolean",
                "list": "array",
                "dict": "object",
            }
            prop["type"] = type_map.get(field_def.field_type, field_def.field_type)
            
            if field_def.default is not None:
                prop["default"] = field_def.default
            if field_def.min_length:
                prop["minLength"] = field_def.min_length
            if field_def.max_length:
                prop["maxLength"] = field_def.max_length
            if field_def.minimum is not None:
                prop["minimum"] = field_def.minimum
            if field_def.maximum is not None:
                prop["maximum"] = field_def.maximum
            if field_def.enum:
                prop["enum"] = field_def.enum
                
            schema_dict["properties"][field_name] = prop
            
            if field_def.required:
                schema_dict["required"].append(field_name)
                
        return json.dumps(schema_dict, indent=2)
        
    def _generate_openapi(self, schema: ModelSchema) -> str:
        """Generate OpenAPI schema."""
        schema_dict = {
            "type": "object",
            "title": schema.name,
            "description": schema.description,
            "properties": {},
            "required": [],
        }
        
        for field_name, field_def in schema.fields.items():
            prop = {"description": field_def.description}
            
            type_map = {
                "str": "string",
                "int": "integer",
                "float": "number",
                "bool": "boolean",
                "list": "array",
                "dict": "object",
            }
            prop["type"] = type_map.get(field_def.field_type, field_def.field_type)
            
            if field_def.default is not None:
                prop["example"] = field_def.default
                
            schema_dict["properties"][field_name] = prop
            
            if field_def.required:
                schema_dict["required"].append(field_name)
                
        return json.dumps(schema_dict, indent=2)
        
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        """Stream validation events."""
        for event in self._event_history[-10:]:
            yield event
            
    def close(self) -> None:
        """Clean up resources."""
        self.schemas.clear()
        self.validations.clear()
        self._event_history.clear()


# FastAPI integration
def create_pydantic_app(bridge: PydanticBridge):
    """Create a FastAPI app for Pydantic bridge."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from typing import Dict, Any, List, Optional
    
    app = FastAPI(title="Pydantic Bridge", version="0.1.0")
    
    class SchemaInput(BaseModel):
        name: str
        schema: Dict[str, Any]
        
    class ValidateInput(BaseModel):
        schema_name: str
        data: Dict[str, Any]
        mode: str = "strict"
        
    class GenerateInput(BaseModel):
        schema_name: str
        format: str = "python"
        
    @app.post("/schemas/create")
    def create_schema(req: SchemaInput):
        return bridge.invoke({
            "type": "schema_create",
            "name": req.name,
            "schema": req.schema,
        })
        
    @app.post("/schemas/validate")
    def validate(req: ValidateInput):
        return bridge.invoke({
            "type": "schema_validate",
            "schema_name": req.schema_name,
            "data": req.data,
            "mode": req.mode,
        })
        
    @app.post("/schemas/generate")
    def generate(req: GenerateInput):
        return bridge.invoke({
            "type": "schema_generate",
            "schema_name": req.schema_name,
            "format": req.format,
        })
        
    @app.get("/schemas")
    def list_schemas():
        return bridge.invoke({"type": "schema_list"})
        
    @app.get("/schemas/{schema_name}")
    def get_schema(schema_name: str):
        return bridge.invoke({
            "type": "schema_get",
            "schema_name": schema_name,
        })
        
    @app.delete("/schemas/{schema_name}")
    def delete_schema(schema_name: str):
        return bridge.invoke({
            "type": "schema_delete",
            "schema_name": schema_name,
        })
        
    @app.get("/validations")
    def validation_history(schema_name: Optional[str] = None):
        return bridge.invoke({
            "type": "validation_history",
            "schema_name": schema_name,
        })
        
    return app