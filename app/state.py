from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from langchain_core.tools import BaseTool
from typing import List, Optional
from app.schemas.user import User

# Define model providers as a literal type
ModelProvider = Literal["ollama", "openai", "anthropic"]

class State(TypedDict):
    # Session information
    sessionId: str
    phoneNumberId: str
    to: str
    messages: Annotated[list[AnyMessage], add_messages]
    
    # Model configuration
    modelProvider: ModelProvider    
    
    # System information
    decision: Optional[str]
    
    # Tools
    tools: Optional[List[BaseTool]]
    
    @classmethod
    def create_from_params(cls, params: dict) -> 'State':
        """Create State from parameters"""
        return cls(
            sessionId=params.get("sessionId", ""),
            phoneNumberId=params.get("phoneNumberId", ""),
            to=params.get("to", ""),
            messages=params.get("messages", []),
            modelProvider=params.get("modelProvider", "openai"),
            decision=params.get("decision"),
            tools=params.get("tools")
        )