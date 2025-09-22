from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from app.schemas.user import User

# Define model providers as a literal type to match State
ModelProvider = Literal["ollama", "openai", "anthropic"]

class WhatsAppBotInput(BaseModel):
    """Input schema for WhatsApp Bot LangServe integration"""
    
    # Core conversation fields that the chain expects
    input: str = Field(description="The user's message/input for the conversation")
    
    # WhatsApp-specific fields
    nit: str = Field(description="Company NIT identifier")
    to: str = Field(description="WhatsApp recipient phone number")
    phoneNumberId: str = Field(description="WhatsApp phone number ID")
    idResolucion: int = Field(description="Resolution ID for the appointment system")
    
    # User management
    users: List[User] = Field(default=[], description="List of users for appointment scheduling")
    
    # Model configuration
    modelProvider: ModelProvider = Field(default="openai", description="AI model provider (openai, anthropic, ollama)")
        
    # User selection and state
    userSelection: Optional[str] = Field(default=None, description="User's selection input for user identification")
    selectedUser: Optional[User] = Field(default=None, description="Currently selected user")
        
    # Optional fields for backward compatibility
    msgInit: Optional[str] = Field(default=None, description="Initial message to start the conversation (deprecated, use input)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "input": "Hola, quiero agendar una cita médica",
                "nit": "900410267",
                "to": "3106400794", 
                "phoneNumberId": "672067049329170",
                "idResolucion": 2,
                "modelProvider": "openai",
                "userSelection": "1",
                "users": [
                    {
                        "idUsuario": 1,
                        "numDocUsr": "12345678",
                        "nombreCompleto": "Juan Pérez",
                        "puedeAgendar": "SI",
                        "msgStatus": "Usuario autorizado para agendar citas"
                    }
                ]
            }
        }
