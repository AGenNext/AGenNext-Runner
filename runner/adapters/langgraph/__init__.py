from runner.adapters.base import GenericAdapter

class Adapter(GenericAdapter):
    name = "langgraph"
    task_type = "tool_call" if "langgraph" in ["langchain","autogen","semantic_kernel"] else ("memory_op" if "langgraph"=="llamaindex" else "workflow_step")
