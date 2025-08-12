from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, START
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from utils.constants import system_prompt_tool
from utils.read_sample_data import get_phone_numbers, get_service_names, get_department_names, get_professionals, get_schedules_by_professional

tools = [
    get_phone_numbers, 
    get_service_names, 
    get_department_names, 
    get_professionals, 
    get_schedules_by_professional
]

# Crea el modelo Ollama
llm = ChatOllama(model="llama3.1:8b")

def assistant(state: MessagesState):
    tools_description = [tool.name for tool in tools]
    system_message = SystemMessage(content=system_prompt_tool(tools_description))
    
    return {"messages": [llm.invoke([system_message] + state["messages"])]}

# Grafo
builder = StateGraph(MessagesState)

builder.add_node('assistant', assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, 'assistant')
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

graph = builder.compile()
