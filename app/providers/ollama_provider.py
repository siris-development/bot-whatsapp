from typing import List, Dict, Any
from .model_provider import ModelProvider
from dotenv import load_dotenv
import os
from langchain_ollama import ChatOllama

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")

class OllamaProvider(ModelProvider):
    """Ollama model provider that returns LangChain ChatOllama directly"""
    
    def __init__(self, model_name: str = "gpt-oss:20b", base_url: str = OLLAMA_BASE_URL, **kwargs):
        super().__init__(model_name, **kwargs)
        self.base_url = base_url.rstrip('/') if base_url else None
        self.kwargs = kwargs
    
    def get_langchain_model(self) -> ChatOllama:
        """Return a LangChain ChatOllama model"""
        return ChatOllama(
            model=self.model_name,
            base_url=self.base_url,
            temperature=self.kwargs.get("temperature", 0.1),
            num_predict=self.kwargs.get("max_tokens", 2024)
        )
    
    async def create_completion(self, messages: List[Dict], tools: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Create completion using Ollama API - kept for backward compatibility"""
        try:
            model = self.get_langchain_model()
            response = await model.ainvoke(messages)
            return {"content": response.content, "response": response}
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def supports_tools(self) -> bool:
        """Ollama supports tool calling"""
        return True

