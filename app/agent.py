
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_ollama.chat_models import ChatOllama
from app.models.agent_state import AgentState
from app.services.get_citas_disponibles import get_citas_disponibles
from app.services.get_especialidades import get_especialidades
from app.services.get_sedes import get_sedes
from app.services.guardar_cita import guardar_cita
from utils.constants import system_prompt_agent

tools = [
    get_citas_disponibles,
    get_especialidades,
    get_sedes,
    guardar_cita
]

# Crea el modelo Ollama
llm = ChatOllama(model="llama3.1:8b")
llm_with_tools = llm.bind_tools(tools)

def should_continue(state):
    return "continue" if state["messages"][-1].tool_calls else "end"

def call_model(state, config):
    tools_description = [tool.name for tool in tools]
    system_message = SystemMessage(content=system_prompt_agent(tools_description))
    return {"messages": [llm_with_tools.invoke([system_message] + state["messages"], config=config)]}

def _invoke_tool(tool_call):
    tool_map = {tool.name: tool for tool in tools}
    tool = tool_map.get(tool_call["name"])
    result = tool.invoke(tool_call["args"])
    return ToolMessage(content=result, tool_call_id=tool_call["id"])

tool_executor = RunnableLambda(_invoke_tool)

def call_tools(state):
    last_message = state["messages"][-1]
    return {"messages": tool_executor.batch(last_message.tool_calls)}

# Grafo
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("action", call_tools)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"continue": "action", "end": END})
workflow.add_edge("action", "agent")

graph = workflow.compile()