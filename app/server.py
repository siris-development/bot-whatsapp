from fastapi import FastAPI
from langchain_core import __version__

# Import our WhatsApp bot components
from app.graph import invoke_graph
from app.schemas.whatsapp_bot_input import WhatsAppBotInput
from app.redis_utils import test_redis_connection, create_redis_session_factory, store_session_params, get_session_params
from app.schemas.whatsapp_response import create_whatsapp_response
from tools.send_to_whatsapp import send_to_whatsapp

# Define the minimum required version as (0, 1, 0)
MIN_VERSION_LANGCHAIN_CORE = (0, 1, 0)

# Split the version string by "." and convert to integers
LANGCHAIN_CORE_VERSION = tuple(map(int, __version__.split(".")))

if LANGCHAIN_CORE_VERSION < MIN_VERSION_LANGCHAIN_CORE:
    raise RuntimeError(
        f"Minimum required version of langchain-core is {MIN_VERSION_LANGCHAIN_CORE}, "
        f"but found {LANGCHAIN_CORE_VERSION}"
    )

app = FastAPI(
    title="WhatsApp Appointment Bot Server",
    version="1.0",
    description="A WhatsApp bot designed to automate the appointment scheduling process using graph-based architecture with LangServe integration",
)

# Add a custom endpoint for WhatsAppBotInput
@app.post("/whatsapp-bot/invoke")
async def whatsapp_bot_invoke(request: WhatsAppBotInput):
    """Custom endpoint for WhatsAppBotInput that handles the full object with manual Redis history"""
    try:
        # Create Redis session for this user
        redis_factory = create_redis_session_factory()
        chat_history = redis_factory(request.to, request.phoneNumberId)
        
        # Add the current user message to history
        chat_history.add_user_message(request.input)
        
        # Check if we have existing session parameters
        existing_params = get_session_params(request.to, request.phoneNumberId)
        
        # If no existing params, store the new ones
        if not existing_params:
            session_params = {
                "nit": request.nit,
                "idResolucion": request.idResolucion,
                "modelProvider": request.modelProvider,
                "users": [user.model_dump() if hasattr(user, 'model_dump') else user for user in request.users]
            }
            store_session_params(request.to, request.phoneNumberId, session_params)
            print(f"📝 Stored initial session params: NIT={request.nit}, Users={len(request.users)}")
        else:
            print(f"📖 Using existing session params: NIT={existing_params.get('nit')}")
        
        # Convert WhatsAppBotInput to graph parameters (minimal state)
        graph_params = {
            "input": request.input,
            "to": request.to,
            "phoneNumberId": request.phoneNumberId,
            "modelProvider": request.modelProvider
        }
        
        # Call invoke_graph directly with chat history
        result = await invoke_graph(graph_params, chat_history=chat_history)
        
        ai_response = result["messages"][-1]
        # usage_metadata = getattr(ai_response, 'usage_metadata', None)

        # Add the AI response to history
        chat_history.add_ai_message(ai_response.content)

        session_id = request.to + "_" + request.phoneNumberId
        
        whatsapp_response = create_whatsapp_response(session_id, request.phoneNumberId, request.to, ai_response.content)
        print(whatsapp_response)

        message_sent = send_to_whatsapp(ai_response.content, session_id)

        if not message_sent:
            return {"message": "Failed to send message to WhatsApp"}
        
        # Return the result
        return {"message": "Message sent to WhatsApp"}
            
    except Exception as e:
        print(f"Error in whatsapp_bot_invoke: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# Health check endpoint
@app.get("/healthz")
async def healthz():
    redis_status = "connected" if test_redis_connection() else "disconnected"
    return {
        "status": "ok",
        "redis": redis_status
    }

# Root endpoint
@app.get("/")
async def root():
    redis_status = "connected" if test_redis_connection() else "disconnected"
    return {
        "service": "WhatsApp Appointment Bot Server",
        "status": "running",
        "description": "A WhatsApp bot for automated appointment scheduling with Redis chat history",
        "docs": "/docs",
        "health": "/healthz",
        "redis_status": redis_status,
        "endpoints": {
            "whatsapp_bot": "/whatsapp-bot/invoke",
        },
        "test_endpoint": "POST /whatsapp-bot/invoke with WhatsAppBotInput payload"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)