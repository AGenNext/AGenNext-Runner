from runner.adapters.base import GenericAdapter

class Adapter(GenericAdapter):
    name = "custom"
    task_type = "tool_call" if "custom" in ["langchain","autogen","semantic_kernel"] else ("memory_op" if "custom"=="llamaindex" else "workflow_step")
