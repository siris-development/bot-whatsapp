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

def create_whatsapp_response(session_id: str, phone_number_id: str, to: str, content: str, usage_metadata: dict = None) -> WhatsAppResponse:
    """Create a WhatsAppResponse object."""
    return WhatsAppResponse(
        sessionId=session_id,
        phoneNumberId=phone_number_id,
        to=to,
        messages=[WhatsAppMessage(type="text", content=content, usage_metadata=usage_metadata)]
    )