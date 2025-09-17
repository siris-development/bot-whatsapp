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
    # phoneNumberId: str
    # to: str
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
            "messages": params.get("messages"),
            "modelProvider": params.get("modelProvider"),
            "users": params.get("users"),
            "selectedUser": params.get("selectedUser"),
            "userSelection": params.get("userSelection"),
            "nit": params.get("nit"),
            "idResolucion": params.get("idResolucion"),
            "decision": params.get("decision")
        }

""" 
{
    "sessionId": "123",
    "messages": ["Hola"],
    "modelProvider": "openai",
    "users": [
        {
            "idUsuario": 25,
            "numDocUsr": "25000000",
            "nombreCompleto": "JOJOA JOJOA AVELINO AVELINO",
            "msgStatus": "Hola, JOJOA JOJOA AVELINO AVELINO, Lo sentimos, usted no es base propia de la IPS. Por favor, contacte al servicio de atención al cliente.",
            "puedeAgendar": "NO"
        },
        {
            "idUsuario": 29,
            "numDocUsr": "29000000",
            "nombreCompleto": "TAIMBUD TAIMBUD ABELINA ABELINA",
            "msgStatus": "Hola, TAIMBUD TAIMBUD ABELINA ABELINA, Bienvenido a la plataforma de agendamiento de citas. Por favor, seleccione una opción para continuar.",
            "puedeAgendar": "SI"
        }
    ],
    "nit": "1234567890",
    "idResolucion": 2
} 
"""

""" 
{
    "sessionId": "123",
    "messages": ["Quiero agendar una cita"],
    "modelProvider": "openai",
    "users": [
        {
            "idUsuario": 25,
            "numDocUsr": "25000000",
            "nombreCompleto": "JOJOA JOJOA AVELINO AVELINO",
            "msgStatus": "Hola, JOJOA JOJOA AVELINO AVELINO, Lo sentimos, usted no es base propia de la IPS. Por favor, contacte al servicio de atención al cliente.",
            "puedeAgendar": "NO"
        },
        {
            "idUsuario": 29,
            "numDocUsr": "29000000",
            "nombreCompleto": "TAIMBUD TAIMBUD ABELINA ABELINA",
            "msgStatus": "Hola, TAIMBUD TAIMBUD ABELINA ABELINA, Bienvenido a la plataforma de agendamiento de citas. Por favor, seleccione una opción para continuar.",
            "puedeAgendar": "NO"
        }
    ],
    "selectedUser": {
        "idUsuario": 29,
        "numDocUsr": "29000000",
        "nombreCompleto": "TAIMBUD TAIMBUD ABELINA ABELINA",
        "msgStatus": "Hola, TAIMBUD TAIMBUD ABELINA ABELINA, Bienvenido a la plataforma de agendamiento de citas. Por favor, seleccione una opción para continuar.",
        "puedeAgendar": "SI"
    },
    "userSelection": "TAIMBUD",
    "nit": "1234567890",
    "idResolucion": 2,
    "decision": "approved"
} 
"""