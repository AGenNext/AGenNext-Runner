import os
from typing import Optional, Any
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

class ModelSelection(BaseModel):
    model_name: str
    provider: str
    is_compatible: bool
    explanation: Optional[str] = None

def get_best_llm(task_description: str) -> Any:
    """
    Chooses the best available LLM for a particular task.
    """
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    master_key = os.getenv("LITELLM_MASTER_KEY")
    
    print(f"DEBUG: Selecting LLM. Keys set: Anthropic={bool(anthropic_api_key)}, OpenAI={bool(openai_api_key)}, Google={bool(google_api_key)}, Master={bool(master_key)}")

    # Priority 1: Google (likely valid key)
    if google_api_key:
        try:
            print("DEBUG: Using direct Google (gemini-pro)")
            return ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=google_api_key)
        except Exception as e:
            print(f"DEBUG: Google error: {e}")
            pass

    # Priority 2: Autonomyx Gateway (fallback)
    if master_key:
        try:
            direct_url = "http://15.235.211.93:4000/v1"
            print(f"DEBUG: Using Gateway at {direct_url}")
            return ChatOpenAI(
                model="gpt-4o-mini",
                base_url=direct_url,
                api_key=master_key,
                timeout=30
            )
        except Exception as e:
            print(f"DEBUG: Gateway error: {e}")
            pass

    # Fallback to other direct providers
    if anthropic_api_key and "sk-ant" in anthropic_api_key:
        try:
            return ChatAnthropic(model="claude-3-5-sonnet-20240620", anthropic_api_key=anthropic_api_key)
        except Exception:
            pass
            
    if openai_api_key and not openai_api_key.startswith("sk-agn"): # Real OpenAI key
        try:
            return ChatOpenAI(model="gpt-4o", api_key=openai_api_key)
        except Exception:
            pass

    return None

def explain_incompatibility():
    return """
I am sorry, but I cannot process your request at this time.
No compatible Large Language Models (LLMs) are currently configured or available.
Please ensure that at least one of the following environment variables is set:
- LITELLM_MASTER_KEY (for Autonomyx Gateway)
- ANTHROPIC_API_KEY
- OPENAI_API_KEY
- GOOGLE_API_KEY
"""
