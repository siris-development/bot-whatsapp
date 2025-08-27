from pydantic import BaseModel
from typing import List
from app.schemas.user import User

class ConversationInit(BaseModel):
    isValid: bool
    message: str
    msgInit: str
    nit: str
    to: str
    users: List[User]
    phoneNumberId: str
    resolucionId: int

class ConversationContinue(BaseModel):
    to: str
    phoneNumberId: str
    message: str