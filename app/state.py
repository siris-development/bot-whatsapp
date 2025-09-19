from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
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
    
    # System information
    nit: Optional[str]
    idResolucion: Optional[int]
    decision: Optional[str]
    
    @classmethod
    def create_from_params(cls, params: dict) -> dict:
        """Create a state dictionary from parameters"""
        return {
            "sessionId": params.get("sessionId"),
            "phoneNumberId": params.get("phoneNumberId"),
            "to": params.get("to"),
            "messages": params.get("messages", "msgInit"),
            "modelProvider": params.get("modelProvider"),
            "users": params.get("users"),
            "selectedUser": params.get("selectedUser"),
            "userSelection": params.get("userSelection"),
            "nit": params.get("nit"),
            "idResolucion": params.get("idResolucion"),
            "decision": params.get("decision")
        }
