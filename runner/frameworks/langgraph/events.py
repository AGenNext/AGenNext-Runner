def normalize_graph_output(output):
    if isinstance(output, dict):
        return output
    return {"output": str(output)}
