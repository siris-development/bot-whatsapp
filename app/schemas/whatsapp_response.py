from pydantic import BaseModel
from typing import List

class WhatsAppMessage(BaseModel):
    type: str = "text"   # podría ser "text", "image", "interactive"
    content: str
    usage_metadata: dict = None

class WhatsAppResponse(BaseModel):
    sessionId: str
    messages: List[WhatsAppMessage]