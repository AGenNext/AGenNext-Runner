from runner.core import UnsupportedFramework
from runner.adapters.langchain import Adapter as LangChainAdapter
from runner.adapters.langgraph import Adapter as LangGraphAdapter
from runner.adapters.crewai import Adapter as CrewAIAdapter
from runner.adapters.autogen import Adapter as AutoGenAdapter
from runner.adapters.semantic_kernel import Adapter as SemanticKernelAdapter
from runner.adapters.llamaindex import Adapter as LlamaIndexAdapter
from runner.adapters.custom import Adapter as CustomAdapter


def get_adapter(framework: str):
    mapping = {
        "langchain": LangChainAdapter(),
        "langgraph": LangGraphAdapter(),
        "crewai": CrewAIAdapter(),
        "autogen": AutoGenAdapter(),
        "semantic_kernel": SemanticKernelAdapter(),
        "llamaindex": LlamaIndexAdapter(),
        "custom": CustomAdapter(),
    }
    if framework not in mapping:
        raise UnsupportedFramework(framework)
    return mapping[framework]


def list_frameworks():
    return ["langchain", "langgraph", "crewai", "autogen", "semantic_kernel", "llamaindex", "custom"]
