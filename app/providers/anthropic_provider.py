from .model_provider import ModelProvider
from typing import List, Dict, Any
from dotenv import load_dotenv
import os
from langchain_anthropic import ChatAnthropic

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

class AnthropicProvider(ModelProvider):
    """Anthropic Claude model provider that returns LangChain ChatAnthropic directly"""
    
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022", api_key: str = ANTHROPIC_API_KEY, **kwargs):
        super().__init__(model_name, **kwargs)
        self.api_key = api_key
        self.kwargs = kwargs
    
    def get_langchain_model(self) -> ChatAnthropic:
        """Return a LangChain ChatAnthropic model"""
        return ChatAnthropic(
            model=self.model_name,
            api_key=self.api_key,
            temperature=self.kwargs.get("temperature", 0.1),
            max_tokens=self.kwargs.get("max_tokens", 2024)
        )
    
    async def create_completion(self, messages: List[Dict], tools: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Create completion using Anthropic API - kept for backward compatibility"""
        try:
            model = self.get_langchain_model()
            response = await model.ainvoke(messages)
            return {"content": response.content, "response": response}
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def supports_tools(self) -> bool:
        """Anthropic supports tool calling"""
        return True

