from typing import Any, Dict
from runner.core import ValidationResult


class GenericAdapter:
    name = "generic"
    task_type = "external_call"

    async def validate_request(self, request: Dict[str, Any], config: Dict[str, Any]) -> ValidationResult:
        if not isinstance(request.get("payload"), dict):
            return ValidationResult(False, "payload_must_be_object")
        return ValidationResult(True)

    async def normalize(self, request: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(request.get("payload", {}))
        for key in ("framework", "adapter", "native_framework_payload"):
            payload.pop(key, None)
        return {
            "type": self.task_type,
            "tool": payload.get("tool", ""),
            "input": payload,
        }

    async def denormalize_result(self, kernel_result: Dict[str, Any], config: Dict[str, Any]) -> Any:
        return {"framework": self.name, "result": kernel_result}
