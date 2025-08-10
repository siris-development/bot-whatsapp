from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.agent_workflow import graph
from app.tool import react_graph_memory

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str
    # Optionally add more fields if your message objects have them

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]  # Accepts a list of message dicts
    thread_id: Optional[str] = "1"

@app.get("/")
def agent():
    return graph.invoke({"user_name": "Diego", "prompt": "Hola, necesito agendar una cita"})

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    result = react_graph_memory.invoke({"messages": request.messages}, config)
    return result


