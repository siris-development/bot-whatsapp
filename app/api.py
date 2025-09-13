from fastapi import FastAPI
from app.mcp_graph import send_to_whatsapp, invoke_mcp_graph
from app.schemas.conversation import ConversationInit, ConversationContinue
from app.redis_client import get_redis_history, clear_redis_history
from app.schemas.whatsapp_response import WhatsAppMessage, WhatsAppResponse
from langchain_core.messages import SystemMessage
import asyncio

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

async def invoke_graph_with_params(session_id: str, phone_number_id: str, to: str, messages: list, provider_type: str) -> dict:
    """Invoke the MCP graph with common parameters and user context."""
    graph_params = {
        "sessionId": session_id,
        "phoneNumberId": phone_number_id,
        "to": to,
        "messages": messages,
        "provider_type": provider_type
    }
    
    return await invoke_mcp_graph(graph_params)

@app.post("/conversation/init")
async def start_conversation(payload: ConversationInit):
    session_id = generate_session_id(payload.to, payload.phoneNumberId)

    # Verificar permisos del usuario
    history = get_redis_history(session_id)

    # Agregar mensajes del sistema como SystemMessage para mejor compatibilidad
    history.add_message(SystemMessage(content=f"NIT: {payload.nit}"))
    history.add_message(SystemMessage(content=f"Users: {[u.model_dump() for u in payload.users]}"))
    history.add_message(SystemMessage(content=f"idResolucion: {payload.idResolucion}"))

    print(f"Session {session_id}: Added system messages to history")
    print(f"History messages count: {len(history.messages)}")

    response = await invoke_graph_with_params(session_id, payload.phoneNumberId, payload.to, [payload.msgInit], payload.modelProvider)
    content, usage_metadata = process_ai_response(response)

    return create_whatsapp_response(session_id, payload.phoneNumberId, payload.to, content, usage_metadata)

@app.post("/conversation/continue")
async def continue_conversation(payload: ConversationContinue):
    session_id = generate_session_id(payload.to, payload.phoneNumberId)

    # Verificar permisos del usuario    
    history = get_redis_history(session_id)
    if not history:
        return {"error": "Session not found"}
    
    history.add_user_message(payload.message)

    response = await invoke_graph_with_params(session_id, payload.phoneNumberId, payload.to, history.messages, payload.modelProvider)
    content, usage_metadata = process_ai_response(response)

    return create_whatsapp_response(session_id, payload.phoneNumberId, payload.to, content, usage_metadata)

@app.post("/conversation/mcp")
async def process_with_mcp(payload: ConversationContinue):
    """Process message using MCP tools and send response to WhatsApp"""
    session_id = generate_session_id(payload.to, payload.phoneNumberId)
    
    try:
        # Verificar permisos del usuario    
        history = get_redis_history(session_id)
        if not history:
            return {"error": "Session not found"}
        
        history.add_user_message(payload.message)

        response = await invoke_graph_with_params(session_id, payload.phoneNumberId, payload.to, history.messages, payload.modelProvider)
        content, usage_metadata = process_ai_response(response)

        # Create WhatsApp response object
        whatsapp_response = create_whatsapp_response(session_id, payload.phoneNumberId, payload.to, content, usage_metadata)
        
        # Send the message to WhatsApp
        success = send_to_whatsapp(content, session_id, payload.phoneNumberId, payload.to)
        
        if success:
            return {"message": "Message processed and sent to WhatsApp successfully", "session_id": session_id, "whatsapp_response": whatsapp_response}
        else:
            return {"error": "Failed to send message to WhatsApp", "session_id": session_id, "whatsapp_response": whatsapp_response}
            
    except Exception as e:
        return {"error": f"Error processing message: {str(e)}", "session_id": session_id}

@app.post("/conversation/clear-history/{session_id}")
def clear_history(session_id: str):
    # Verificar que el usuario solo puede limpiar su propio historial
    try:
        clear_redis_history(session_id)
        return {"message": "History cleared successfully"}
    except Exception as e:
        return {"error": f"Failed to clear history: {str(e)}", "session_id": session_id}
