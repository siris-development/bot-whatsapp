from fastapi import FastAPI
from app.graph import graph
from app.schemas.conversation import ConversationInit, ConversationContinue, ConversationError
from app.redis_client import save_session, get_session

app = FastAPI()

@app.post("/conversation/init")
def start_conversation(payload: ConversationInit):
    if(not payload.isValid):
        return ConversationError(
            isValid=payload.isValid,
            message=payload.message,
            msgInit=payload.msgInit)

    session_id = payload.messageId

    # Estado inicial en Redis
    session_data = {
        "isValid": payload.isValid,
        "nit": payload.nit,
        "users": [u.model_dump() for u in payload.users],
        "msgInit": payload.msgInit,
        "resolucionId": payload.resolucionId,
    }
    save_session(session_id, session_data)

    # Llamar a tu graph
    response = graph.invoke({
        "sessionId": session_id,
        "nit": payload.nit,
        "users": session_data["users"],
        "msgInit": payload.msgInit,
        "resolucionId": payload.resolucionId,
    })

    return {"sessionId": session_id, "response": response}


@app.post("/conversation/continue/{session_id}")
def continue_conversation(session_id: str, payload: ConversationContinue):
    session_data = get_session(session_id)
    if not session_data:
        return {"error": "Session not found"}

    # Agregar nuevos mensajes al historial
    session_data["messages"].extend(payload.messages)
    save_session(session_id, session_data)

    response = graph.invoke({
        "nit": session_data["nit"],
        "users": session_data["users"],
        "resolucionId": session_data["resolucionId"],
        "messages": session_data["messages"]
    })

    return {"sessionId": session_id, "response": response}