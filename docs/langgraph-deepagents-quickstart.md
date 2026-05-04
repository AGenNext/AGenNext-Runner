# LangGraph + Deep Agents Quickstart

You write a LangGraph Deep Agent.
AgentNext Runner handles local dev, identity, authorization, tool approval, and Kernel handoff.
Platform stores config in production.
Kernel stores traces/audit and executes only prevalidated work.

```bash
agentnext init support-agent --template langgraph-deepagent
cd support-agent
pip install -r requirements.txt
agentnext dev
agentnext invoke "Search docs and create a ticket"
agentnext package
```
