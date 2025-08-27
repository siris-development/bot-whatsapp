from pydantic import BaseModel
from typing import List, Optional

class WhatsAppMessage(BaseModel):
    type: str = "text"   # podría ser "text", "image", "interactive"
    content: str
    usage_metadata: Optional[dict] = None

class WhatsAppResponse(BaseModel):
    sessionId: str
    phoneNumberId: Optional[str] = None
    to: Optional[str] = None
    messages: List[WhatsAppMessage]