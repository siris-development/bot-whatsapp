from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain.schema import SystemMessage

from app.services.get_citas_disponibles import get_citas_disponibles
from app.services.get_especialidades import get_especialidades
from app.services.get_sedes import get_sedes
from app.services.guardar_cita import guardar_cita
from utils.constants import system_prompt_agent

tools = [
    get_especialidades,
    get_sedes,
    get_citas_disponibles,
    guardar_cita
]

tool_node = ToolNode(tools)

# Crea el modelo Ollama
model = init_chat_model("gpt-oss:20b", model_provider="ollama")
model_with_tools = model.bind_tools(tools)

def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END


def call_model(state: MessagesState):
    tools_description = [tool.name for tool in tools]
    
    # Crear el mensaje de sistema explícito
    system_message = SystemMessage(content=system_prompt_agent(tools_description))
    
    # Combinar el system prompt con el historial del estado
    messages = [system_message] + state["messages"]
    
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}


builder = StateGraph(MessagesState)
builder.add_node("call_model", call_model)
builder.add_node("tools", tool_node)

builder.add_edge(START, "call_model")
builder.add_conditional_edges("call_model", should_continue, ["tools", END])
builder.add_edge("tools", "call_model")

graph = builder.compile()
