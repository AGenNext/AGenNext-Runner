from runner.adapters.base import GenericAdapter

class Adapter(GenericAdapter):
    name = "semantic_kernel"
    task_type = "tool_call" if "semantic_kernel" in ["langchain","autogen","semantic_kernel"] else ("memory_op" if "semantic_kernel"=="llamaindex" else "workflow_step")
