from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from app.config import tools, llm_with_tools
from app.redis_client import get_session

from app.state import State
from utils.constants import system_prompt_agent

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage

def build_graph() -> StateGraph:
    graph_builder = StateGraph(State)

    def call_model(state: State):
        session_data = get_session(state["sessionId"])
        nit = session_data["nit"]
        users = session_data["users"]
        resolucionId = session_data["resolucionId"]

        tools_description = [tool.name for tool in tools]

        # Mensaje de sistema con tu prompt dinámico
        system_message_content = system_prompt_agent(
            tools_description=tools_description,
            nit=nit,
            users=users,
            resolucionId=resolucionId,
        )

        # Prompt: sistema + TODA la conversación (incluye ToolMessages)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message_content),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        # Cadena con LLM habilitado para tools
        chain = prompt | llm_with_tools

        # Asegurar que los mensajes sean BaseMessage. Si vienen como str, los convertimos a HumanMessage
        msgs_in = []
        for m in state["messages"]:
            if isinstance(m, str):
                msgs_in.append(HumanMessage(content=m))
            else:
                msgs_in.append(m)

        # Invocar el modelo con el historial completo (incluye tool outputs)
        response = chain.invoke({"messages": msgs_in})

        return {"messages": [response]}

    graph_builder.add_node("call_model", call_model)
    
    tool_node = ToolNode(tools)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_conditional_edges("call_model", tools_condition)
    graph_builder.add_edge("tools", "call_model")
    graph_builder.add_edge(START, "call_model")

    return graph_builder.compile()

graph = build_graph()
