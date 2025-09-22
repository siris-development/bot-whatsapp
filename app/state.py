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
    
    # User information
    users: List[User]
    userSelection: Optional[str]  # User's selection input
    selectedUser: Optional[User]
    retry_count: Optional[int]  # Track retry attempts
    
    # System information
    nit: Optional[str]
    idResolucion: Optional[int]
    decision: Optional[str]
    
    # Tools
    tools: Optional[List[BaseTool]]
    
    @classmethod
    def create_from_params(cls, params: dict) -> dict:
        """Create a state dictionary from parameters"""
        from langchain_core.messages import HumanMessage
        
        # Handle messages properly - convert to HumanMessage if string
        messages = params.get("messages", [])
        if isinstance(messages, str):
            messages = [HumanMessage(content=messages)]
        elif isinstance(messages, list) and messages and isinstance(messages[0], str):
            messages = [HumanMessage(content=msg) for msg in messages]
        
        return {
            "sessionId": params.get("sessionId"),
            "phoneNumberId": params.get("phoneNumberId"),
            "to": params.get("to"),
            "messages": messages,
            "modelProvider": params.get("modelProvider"),
            "users": params.get("users", []),
            "selectedUser": params.get("selectedUser"),
            "userSelection": params.get("userSelection"),
            "retry_count": params.get("retry_count", 0),
            "nit": params.get("nit"),
            "idResolucion": params.get("idResolucion"),
            "decision": params.get("decision"),
            "tools": params.get("tools", [])
        }
