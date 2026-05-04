from runner.adapters.base import GenericAdapter

class Adapter(GenericAdapter):
    name = "llamaindex"
    task_type = "tool_call" if "llamaindex" in ["langchain","autogen","semantic_kernel"] else ("memory_op" if "llamaindex"=="llamaindex" else "workflow_step")
