from runner.frameworks.langgraph.loader import load_entrypoint
from runner.frameworks.langgraph.events import normalize_graph_output


class DeepAgentsLangGraphAdapter:
    def __init__(self, project_dir: str = "."):
        self.project_dir = project_dir

    def invoke(self, message: str, cfg: dict) -> dict:
        entrypoint = cfg["agent"]["entrypoint"]
        graph = load_entrypoint(entrypoint, self.project_dir)
        payload = {"messages": [{"role": "user", "content": message}]}

        if hasattr(graph, "invoke"):
            out = graph.invoke(payload)
        elif hasattr(graph, "ainvoke"):
            raise RuntimeError("ainvoke-only graph not supported in sync local harness")
        elif hasattr(graph, "stream"):
            chunks = list(graph.stream(payload))
            out = chunks[-1] if chunks else {}
        else:
            raise RuntimeError("Unsupported graph interface")

        return {
            "result": normalize_graph_output(out),
            "metadata": {
                "framework": "langgraph",
                "sdk": cfg["agent"].get("sdk", "deepagents"),
                "agent_id": cfg["agent"]["id"],
                "entrypoint": entrypoint,
                "streaming": cfg.get("runtime", {}).get("streaming", True),
            },
        }
