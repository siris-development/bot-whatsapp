from pydantic import BaseModel
from typing import List, Optional

from app.schemas.user import User

class ConversationInit(BaseModel):
    isValid: bool
    nit: str
    messageId: str
    users: List[User]
    msgInit: str
    idResolucion: int

class ConversationError(BaseModel):
    isValid: bool
    message: str
    msgInit: str

class ConversationContinue(BaseModel):
    messages: List[str]