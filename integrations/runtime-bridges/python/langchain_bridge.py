"""
LangChain Bridge for AGenNext Runtime Core.

Provides integration with LangChain for LLM chain execution,
tool calling, memory management, and RAG pipelines.
"""

import os
from typing import Any, Dict, Generator, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ChainType(Enum):
    LLM = "llm"
    CHAT = "chat"
    CONVERSATIONAL = "conversational"
    RAG = "rag"
    TOOL_CALLING = "tool_calling"
    JSON = "json"
    SQL = "sql"


class MemoryType(Enum):
    BUFFER = "buffer"
    BUFFER_WINDOW = "buffer_window"
    SUMMARY = "summary"
    KG = "knowledge_graph"


@dataclass
class Tool:
    """LangChain tool definition."""
    name: str
    description: str
    func: Any = None
    schema: Optional[Dict[str, Any]] = None


@dataclass  
class ChainConfig:
    """Configuration for a LangChain."""
    chain_type: ChainType = ChainType.LLM
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2048
    tools: List[Tool] = field(default_factory=list)
    memory_type: Optional[MemoryType] = None
    system_prompt: str = ""
    rag_config: Optional[Dict[str, Any]] = None


class LangChainBridge:
    """Bridge for LangChain execution."""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.chains: Dict[str, ChainConfig] = {}
        self.memory: Dict[str, Any] = {}
        self.messages: Dict[str, List[Dict[str, str]]] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._llm: Optional[Any] = None
        
    def init(self, config: Dict[str, Any]) -> None:
        """Initialize the LangChain bridge."""
        self.config = config
        
        # Try to import langchain
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage, AIMessage, SystemMessage
            
            model = config.get("model", "gpt-4")
            api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
            
            self._llm = ChatOpenAI(
                model=model,
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 2048),
                api_key=api_key,
            )
            
        except ImportError:
            self._llm = None
            
    def _create_chain(self, chain_type: ChainType, config: Dict[str, Any]):
        """Create a LangChain based on type."""
        if not self._llm:
            return None
            
        try:
            if chain_type == ChainType.LLM:
                from langchain.schema import SystemMessage
                from langchain import PromptTemplate
                
                template = config.get("template", "{input}")
                prompt = PromptTemplate.from_template(template)
                from langchain import LLMChain
                return LLMChain(llm=self._llm, prompt=prompt)
                
            elif chain_type == ChainType.CHAT:
                from langchain import Chat PromptTemplate
                from langchain import MessagesPlaceholder
                
                system_prompt = config.get("system_prompt", "You are a helpful assistant.")
                prompt = ChatPromptTemplate.from_messages([
                    SystemMessage(content=system_prompt),
                    MessagesPlaceholder(variable_name="history"),
                    HumanMessagePromptTemplate.from_template("{input}"),
                ])
                from langchain import LLMChain
                return LLMChain(llm=self._llm, prompt=prompt)
                
            elif chain_type == ChainType.TOOL_CALLING:
                from langchain import AgentExecutor, create_tool_calling_agent
                from langchain.tools import Tool as LangChainTool
                
                tools = []
                for tool_config in config.get("tools", []):
                    tool = LangChainTool(
                        name=tool_config["name"],
                        description=tool_config["description"],
                        func=tool_config.get("func"),
                    )
                    tools.append(tool)
                    
                prompt = config.get("prompt", "You have access to tools.")
                agent = create_tool_calling_agent(self._llm, tools, prompt)
                return AgentExecutor(agent=agent, tools=tools)
                
            elif chain_type == ChainType.RAG:
                # RAG chain with embeddings + vectorstore
                from langchain import StuffDocumentsChain, create_retrieval_chain
                from langchain.embeddings import OpenAIEmbeddings
                from langchain.vectorstores import FAISS
                from langchain.text_splitter import CharacterTextSplitter
                from langchain import Document
                
                # Create vector store
                docs = config.get("documents", [])
                if docs:
                    text_splitter = CharacterTextSplitter(
                        chunk_size=config.get("chunk_size", 1000),
                        chunk_overlap=config.get("chunk_overlap", 200),
                    )
                    split_docs = text_splitter.split_documents([
                        Document(page_content=d) for d in docs
                    ])
                    
                    embeddings = OpenAIEmbeddings(
                        api_key=config.get("api_key") or os.getenv("OPENAI_API_KEY")
                    )
                    vectorstore = FAISS.from_documents(split_docs, embeddings)
                    retriever = vectorstore.as_retriever()
                    
                    return create_retrieval_chain(
                        self._llm.get_chain(),
                        retriever
                    )
                    
        except ImportError:
            pass
            
        return None
        
    def invoke(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a LangChain action."""
        action_type = action.get("type", "invoke")
        
        if action_type == "chain_create":
            # Create a new chain
            chain_id = action.get("chain_id", f"chain_{len(self.chains)}")
            config = action.get("config", {})
            
            chain_type = ChainType(config.get("chain_type", "llm"))
            chain_config = ChainConfig(
                chain_type=chain_type,
                model=config.get("model", "gpt-4"),
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 2048),
                system_prompt=config.get("system_prompt", ""),
            )
            
            chain = self._create_chain(chain_type, config)
            
            self.chains[chain_id] = chain_config
            self.messages[chain_id] = []
            
            return {
                "status": "created",
                "chain_id": chain_id,
                "chain_type": chain_type.value,
            }
            
        elif action_type == "invoke":
            # Invoke a chain
            chain_id = action.get("chain_id", "default")
            prompt = action.get("prompt", "")
            inputs = action.get("inputs", {"input": prompt})
            
            if chain_id not in self.chains:
                # Create default chain
                chain_id = "default"
                self.chains[chain_id] = ChainConfig()
                self.messages[chain_id] = []
                
            chain_config = self.chains.get(chain_id)
            
            if not self._llm:
                # Mock response
                return {
                    "status": "ok",
                    "response": f"Mock: {prompt}",
                    "chain_id": chain_id,
                }
                
            try:
                if chain_config and chain_config.chain_type == ChainType.CHAT:
                    history = self.messages.get(chain_id, [])
                    result = self._llm.invoke(prompt)
                    
                    # Add to history
                    self.messages[chain_id].append({
                        "role": "user",
                        "content": prompt,
                    })
                    self.messages[chain_id].append({
                        "role": "assistant", 
                        "content": result.content,
                    })
                    
                    self._event_history.append({
                        "type": "invoke",
                        "chain_id": chain_id,
                        "prompt": prompt,
                        "response": result.content,
                    })
                    
                    return {
                        "status": "ok",
                        "response": result.content,
                        "chain_id": chain_id,
                        "message_count": len(self.messages[chain_id]),
                    }
                else:
                    result = self._llm.invoke(prompt)
                    return {
                        "status": "ok",
                        "response": result.content,
                        "chain_id": chain_id,
                    }
                    
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "chain_id": chain_id,
                }
                
        elif action_type == "stream":
            # Stream response
            chain_id = action.get("chain_id", "default")
            prompt = action.get("prompt", "")
            
            if not self._llm:
                yield {"content": f"Mock: {prompt}"}
                return
                
            try:
                for chunk in self._llm.stream(prompt):
                    yield {
                        "content": chunk.content,
                        "chain_id": chain_id,
                    }
            except Exception as e:
                yield {"error": str(e)}
                
        elif action_type == "tools_list":
            # List available tools
            return {
                "status": "ok",
                "tools": [
                    {"name": "search", "description": "Search the web"},
                    {"name": "calculator", "description": "Basic math operations"},
                    {"name": "weather", "description": "Get weather info"},
                ],
            }
            
        elif action_type == "memory_get":
            # Get conversation memory
            chain_id = action.get("chain_id", "default")
            messages = self.messages.get(chain_id, [])
            return {
                "status": "ok",
                "chain_id": chain_id,
                "messages": messages,
            }
            
        elif action_type == "memory_clear":
            # Clear conversation memory
            chain_id = action.get("chain_id", "default")
            if chain_id in self.messages:
                self.messages[chain_id] = []
            return {
                "status": "ok",
                "chain_id": chain_id,
            }
            
        return {"status": "unknown_action", "action": action}
        
    def stream(self) -> Generator[Dict[str, Any], None, None]:
        """Stream response tokens."""
        for event in self._event_history[-10:]:
            yield event
            
    def close(self) -> None:
        """Clean up resources."""
        self.chains.clear()
        self.messages.clear()
        self.memory.clear()
        self._event_history.clear()


# FastAPI integration
def create_langchain_app(bridge: LangChainBridge):
    """Create a FastAPI app for LangChain bridge."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from typing import Optional
    
    app = FastAPI(title="LangChain Bridge", version="0.1.0")
    
    class InvokeInput(BaseModel):
        type: str = "invoke"
        chain_id: str = "default"
        prompt: str = ""
        inputs: Dict[str, Any] = {}
        
    @app.post("/invoke")
    def invoke(req: InvokeInput):
        return bridge.invoke(req.model_dump(exclude={"type"}))
        
    @app.get("/chains")
    def list_chains():
        return {"chains": list(bridge.chains.keys())}
        
    @app.get("/stream")
    def stream():
        return {"events": list(bridge.stream())}
        
    @app.get("/memory/{chain_id}")
    def get_memory(chain_id: str):
        return bridge.invoke({
            "type": "memory_get",
            "chain_id": chain_id,
        })
        
    return app