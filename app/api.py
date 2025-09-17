from fastapi import FastAPI
from app.mcp_graph import invoke_graph
from tools.send_to_whatsapp import send_to_whatsapp
from app.schemas.conversation import ConversationInit, ConversationContinue
from app.redis_client import get_redis_history, clear_redis_history
from app.schemas.whatsapp_response import WhatsAppMessage, WhatsAppResponse
from langchain_core.messages import SystemMessage
from utils.constants import generate_session_id

app = FastAPI()

@app.post("/conversation/init")
async def start_conversation(payload: ConversationInit):
    session_id = generate_session_id(payload.to, payload.phoneNumberId)

    # Create proper graph parameters for State
    graph_params = {
        "sessionId": session_id,
        "messages": [SystemMessage(content=payload.msgInit)],
        "modelProvider": payload.modelProvider,
        "users": payload.users,
        "selected_user": None,
        "nit": payload.nit,
        "idResolucion": payload.idResolucion
    }
        
    response = await invoke_graph(graph_params)
    content, usage_metadata = process_ai_response(response)

    # Create WhatsApp response object
    whatsapp_response = create_whatsapp_response(session_id, payload.phoneNumberId, payload.to, content, usage_metadata)
    
    # Send the message to WhatsApp
    success = send_to_whatsapp(content, session_id, payload.phoneNumberId, payload.to)
    
    if success:
        return {"message": "Conversation initialized and message sent to WhatsApp successfully", "session_id": session_id, "whatsapp_response": whatsapp_response}
    else:
        return {"error": "Failed to send message to WhatsApp", "session_id": session_id, "whatsapp_response": whatsapp_response}

@app.post("/conversation/mcp")
async def process_with_mcp(payload: ConversationContinue):
    """Process message using MCP tools and send response to WhatsApp"""
    session_id = generate_session_id(payload.to, payload.phoneNumberId)
    
    try:
        # Verificar permisos del usuario    
        history = get_redis_history(session_id)
        if not history:
            return {"error": "Session not found"}

        history.add_message(SystemMessage(content=f"User: {payload.user.model_dump()}"))
        history.add_user_message(payload.message)

        # Create proper graph parameters for State
        graph_params = {
            "sessionId": session_id,
            "messages": history.messages,
            "modelProvider": payload.modelProvider,
            "users": [payload.user],  # Single user for MCP processing
            "selected_user": payload.user,
            "nit": None,
            "idResolucion": None
        }
        
        response = await invoke_graph(graph_params)
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


def process_ai_response(response: dict) -> tuple[str, dict]:
    """Extract AI response content and usage metadata."""
    print(f"Response from graph: {response}")
    messages = response.get("messages", [])
    if not messages:
        return "No response generated", None
    
    # Get the last message (should be AI response)
    ai_response = messages[-1]
    print(f"AI Response: {ai_response}")
    
    # Check if it's actually an AI message
    if hasattr(ai_response, 'type') and ai_response.type == 'human':
        # If the last message is human, look for the previous AI message
        ai_messages = [msg for msg in messages if hasattr(msg, 'type') and msg.type == 'ai']
        if ai_messages:
            ai_response = ai_messages[-1]
        else:
            return "Error: No AI response found", None
    
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

