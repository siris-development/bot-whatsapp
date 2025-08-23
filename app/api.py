from fastapi import FastAPI
from app.graph import graph
from app.schemas.conversation import ConversationInit, ConversationContinue, ConversationError
from app.redis_client import get_redis_history
from app.schemas.whatsapp_response import WhatsAppMessage, WhatsAppResponse

app = FastAPI()

@app.post("/conversation/init")
def start_conversation(payload: ConversationInit):
    if(not payload.isValid):
        return ConversationError(
            isValid=payload.isValid,
            message=payload.message,
            msgInit=payload.msgInit)

    session_id = payload.messageId

    history = get_redis_history(session_id)
    history.clear()  # Limpiar el historial si ya existe

    # Guardar los datos iniciales en el historial
    history.add_ai_message(f"NIT: {payload.nit}")
    history.add_ai_message(f"Users: {[u.model_dump() for u in payload.users]}")
    history.add_ai_message(f"IdResolucion: {payload.idResolucion}")

    # Llamar a tu graph
    response = graph.invoke({
        "sessionId": session_id,
        "messages": [payload.msgInit],
    })

    ai_response = response["messages"][-1]
    usage_metadata = getattr(ai_response, 'usage_metadata', None)

    return WhatsAppResponse(
        sessionId=session_id,
        messages=[WhatsAppMessage(type="text", content=str(ai_response.content), usage_metadata=usage_metadata)]
    )


@app.post("/conversation/continue/{session_id}")
def continue_conversation(session_id: str, payload: ConversationContinue):
    history = get_redis_history(session_id)
    if not history:
        return {"error": "Session not found"}
    
    history.add_user_message(payload.message)

    response = graph.invoke({
        "sessionId": session_id,
        "messages": history.messages,
    })

    ai_response = response["messages"][-1]

    return WhatsAppResponse(
        sessionId=session_id,
        messages=[WhatsAppMessage(type="text", content=str(ai_response.content))]
    )

@app.post("/conversation/clear-history/{session_id}")
def clear_history(session_id: str):
    history = get_redis_history(session_id)  
    history.clear()

    return {"message": "History cleared successfully"}