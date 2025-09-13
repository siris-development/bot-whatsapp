from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ModelProvider(ABC):
    """Abstract base class for AI model providers"""
    
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.kwargs = kwargs
    
    @abstractmethod
    async def create_completion(self, messages: List[Dict], tools: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Create a completion with the model"""
        pass
    
    @abstractmethod
    def supports_tools(self) -> bool:
        """Check if the provider supports tool calling"""
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "provider": self.__class__.__name__,
            "model": self.model_name,
            "supports_tools": self.supports_tools()
        }

