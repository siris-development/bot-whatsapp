from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from app.tool import react_graph_memory

app = FastAPI()

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]  # Accepts a list of message dicts
    thread_id:  str

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    result = react_graph_memory.invoke({"messages": request.messages}, config)
    return result


