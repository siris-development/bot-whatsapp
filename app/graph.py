from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from app.config import tools, llm_with_tools
from app.redis_client import get_redis_history

from app.state import State
from utils.constants import system_prompt_agent

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

def build_graph() -> StateGraph:
    graph_builder = StateGraph(State)

    def call_model(state: State):        
        tools_description = [tool.name for tool in tools]

        # Crear el mensaje de sistema explícito
        system_message_content = system_prompt_agent(tools_description=tools_description)
        
        # Create a prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message_content),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

        # Create the conversational chain
        chain = prompt | llm_with_tools

        # Create a runnable with message history
        chain_with_history = RunnableWithMessageHistory(
            chain, get_redis_history, input_messages_key="input", history_messages_key="history"
        )

        last_message = state["messages"][-1].content if len(state["messages"]) > 0 else state["messages"][0].content

        response = chain_with_history.invoke({"input": last_message}, 
                                             config={"configurable": {"session_id": state["sessionId"]}})
        return {"messages": [response]}

    graph_builder.add_node("call_model", call_model)
    
    tool_node = ToolNode(tools)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_conditional_edges("call_model", tools_condition)
    graph_builder.add_edge("tools", "call_model")
    graph_builder.add_edge(START, "call_model")

    return graph_builder.compile()

graph = build_graph()