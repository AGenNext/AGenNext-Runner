"""Python runtime bridge template for AGenNext Kernels."""

class KernelBridge:
    def init(self, config: dict) -> None:
        self.config = config

    def invoke(self, action: dict) -> dict:
        return {"status": "todo", "action": action}

    def stream(self):
        yield {"status": "todo", "event": "stream-not-implemented"}

    def close(self) -> None:
        return None
