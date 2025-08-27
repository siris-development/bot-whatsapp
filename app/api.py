from fastapi import FastAPI
from app.graph import graph
from app.schemas.conversation import ConversationInit, ConversationContinue
from app.redis_client import get_redis_history
from app.schemas.whatsapp_response import WhatsAppMessage, WhatsAppResponse

app = FastAPI()

def generate_session_id(to: str, phone_number_id: str) -> str:
    """Generate a session ID from phone number and recipient."""
    return f"{to}_{phone_number_id}"

def process_ai_response(response: dict) -> tuple[str, dict]:
    """Extract AI response content and usage metadata."""
    ai_response = response["messages"][-1]
    usage_metadata = getattr(ai_response, 'usage_metadata', None)
    return str(ai_response.content), usage_metadata

def create_whatsapp_response(session_id: str, phone_number_id: str, to: str, content: str, usage_metadata: dict = None) -> WhatsAppResponse:
    """Create a WhatsAppResponse object."""
    return WhatsAppResponse(
        sessionId=session_id,
        phoneNumberId=phone_number_id,
        to=to,
        messages=[WhatsAppMessage(type="text", content=content, usage_metadata=usage_metadata)]
    )

def invoke_graph_with_params(session_id: str, phone_number_id: str, to: str, messages: list) -> dict:
    """Invoke the graph with common parameters."""
    return graph.invoke({
        "sessionId": session_id,
        "phoneNumberId": phone_number_id,
        "to": to,
        "messages": messages
    })

@app.post("/conversation/init")
def start_conversation(payload: ConversationInit):
    session_id = generate_session_id(payload.to, payload.phoneNumberId)

    history = get_redis_history(session_id)
    history.clear()

    history.add_ai_message(f"NIT: {payload.nit}")
    history.add_ai_message(f"Users: {[u.model_dump() for u in payload.users]}")
    history.add_ai_message(f"ResolucionId: {payload.resolucionId}")

    response = invoke_graph_with_params(session_id, payload.phoneNumberId, payload.to, [payload.msgInit])
    content, usage_metadata = process_ai_response(response)

    return create_whatsapp_response(session_id, payload.phoneNumberId, payload.to, content, usage_metadata)


@app.post("/conversation/continue")
def continue_conversation(payload: ConversationContinue):
    session_id = generate_session_id(payload.to, payload.phoneNumberId)

    history = get_redis_history(session_id)
    if not history:
        return {"error": "Session not found"}
    
    history.add_user_message(payload.message)

    response = invoke_graph_with_params(session_id, payload.phoneNumberId, payload.to, history.messages)
    content, usage_metadata = process_ai_response(response)

    return create_whatsapp_response(session_id, payload.phoneNumberId, payload.to, content, usage_metadata)

@app.post("/conversation/clear-history/{session_id}")
def clear_history(session_id: str):
    history = get_redis_history(session_id)  
    history.clear()

    return {"message": "History cleared successfully"}