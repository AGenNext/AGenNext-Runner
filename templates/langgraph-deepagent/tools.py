def tool(risk="low", requires_approval=False):
    def _wrap(fn):
        fn.__agentnext_tool__ = {"risk": risk, "requires_approval": requires_approval, "id": fn.__name__}
        return fn
    return _wrap

@tool(risk="low")
def search_docs(query: str) -> str:
    return f"Search results for: {query}"

@tool(risk="medium", requires_approval=True)
def create_ticket(title: str, body: str) -> str:
    return f"Created ticket: {title}"
