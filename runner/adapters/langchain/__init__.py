from runner.adapters.base import GenericAdapter

class Adapter(GenericAdapter):
    name = "langchain"
    task_type = "tool_call" if "langchain" in ["langchain","autogen","semantic_kernel"] else ("memory_op" if "langchain"=="llamaindex" else "workflow_step")
