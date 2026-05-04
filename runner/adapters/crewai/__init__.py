from runner.adapters.base import GenericAdapter

class Adapter(GenericAdapter):
    name = "crewai"
    task_type = "tool_call" if "crewai" in ["langchain","autogen","semantic_kernel"] else ("memory_op" if "crewai"=="llamaindex" else "workflow_step")
