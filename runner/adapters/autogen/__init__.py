from runner.adapters.base import GenericAdapter

class Adapter(GenericAdapter):
    name = "autogen"
    task_type = "tool_call" if "autogen" in ["langchain","autogen","semantic_kernel"] else ("memory_op" if "autogen"=="llamaindex" else "workflow_step")
