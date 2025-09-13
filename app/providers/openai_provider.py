from .model_provider import ModelProvider
from typing import List, Dict, Any
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class OpenAIProvider(ModelProvider):
    """OpenAI model provider that returns LangChain ChatOpenAI directly"""
    
    def __init__(self, model_name: str = "gpt-4o-mini", api_key: str = OPENAI_API_KEY, base_url: str = None, **kwargs):
        super().__init__(model_name, **kwargs)
        self.api_key = api_key
        self.base_url = base_url
        self.kwargs = kwargs
    
    def get_langchain_model(self) -> ChatOpenAI:
        """Return a LangChain ChatOpenAI model"""
        return ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self.kwargs.get("temperature", 0.1),
            max_tokens=self.kwargs.get("max_tokens", 2024)
        )
    
    async def create_completion(self, messages: List[Dict], tools: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Create completion using OpenAI API - kept for backward compatibility"""
        try:
            model = self.get_langchain_model()
            response = await model.ainvoke(messages)
            return {"content": response.content, "response": response}
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def supports_tools(self) -> bool:
        """OpenAI supports tool calling"""
        return True
