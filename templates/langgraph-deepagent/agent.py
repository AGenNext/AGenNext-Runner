from deepagents import create_deep_agent
from tools import search_docs, create_ticket

agent = create_deep_agent(
    model="openai:gpt-5-mini",
    tools=[search_docs, create_ticket],
    system_prompt="You are a helpful AgentNext Deep Agent.",
)
