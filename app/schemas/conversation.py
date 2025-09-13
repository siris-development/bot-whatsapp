from pydantic import BaseModel
from typing import List
from app.schemas.user import User

class ConversationInit(BaseModel):
    nit: str
    to: str
    users: List[User]
    msgInit: str
    phoneNumberId: str
    idResolucion: int
    modelProvider: str

class ConversationContinue(BaseModel):
    to: str
    phoneNumberId: str
    message: str
    modelProvider: str