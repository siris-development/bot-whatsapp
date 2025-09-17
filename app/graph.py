from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.ollama_provider import OllamaProvider
from app.state import State
from app.schemas.user import User
from utils.constants import system_prompt_agent, system_prompt_llm_user_selection
from typing import Literal
from app.redis_client import get_redis_history, clear_redis_history
from langchain_core.runnables import RunnableWithMessageHistory

from tools.get_sedes import get_sedes
from tools.get_citas_disponibles import get_citas_disponibles
from tools.get_especialidades import get_especialidades
from tools.guardar_cita import guardar_cita
from tools.despedida import despedida

tools = [
    get_sedes,
    get_citas_disponibles,
    get_especialidades,
    guardar_cita,
    despedida
]

# LLM-powered user selection node
def llm_user_selection(state: State) -> Command[Literal["user_approved", "user_rejected"]]:
    """LLM-powered user selection that intelligently processes user input"""
    users = state.get("users", [])
    users = [User(**user) for user in users]
    if not users:
        return Command(goto="user_rejected", update={"decision": "rejected"})
    
    # Create user selection prompt
    user_list = "\n".join([f"{i+1}. {user.nombreCompleto}" for i, user in enumerate(users)])
    
    # Check if we have a user selection from Command resume
    user_selection = state.get("user_selection")
    
    if not user_selection:
        user_selection = interrupt({
            "message": f"Por favor selecciona un usuario escribiendo el número, nombre, o cualquier información que te ayude a identificarlo:\n{user_list}",
        })
    else:
        # Extract the actual value if it's wrapped in a dict
        if isinstance(user_selection, dict) and "user_selection" in user_selection:
            user_selection = user_selection["user_selection"]

    # Use LLM to process the user selection
    model_provider = state.get("modelProvider")
    
    if model_provider == "openai":
        provider = OpenAIProvider()
    elif model_provider == "anthropic":
        provider = AnthropicProvider()
    else:
        provider = OllamaProvider()
    
    # Create prompt for LLM to analyze user selection
    selection_prompt = system_prompt_llm_user_selection(user_list, user_selection)

    try:
        # Get LLM response using LangChain model
        model = provider.get_langchain_model()
        llm_response = model.invoke(selection_prompt)
        response_content = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
        print(f"LLM Response: {response_content}")
        
        # Process LLM response
        if response_content.strip().isdigit():
            selected_index = int(response_content.strip()) - 1
            if 0 <= selected_index < len(users):
                selected_user = users[selected_index]
                print(f"✅ Usuario seleccionado por LLM: {selected_user.nombreCompleto}")
                
                if selected_user.puedeAgendar == "SI":
                    return Command(goto="user_approved", update={
                        "decision": "approved",
                        "selectedUser": selected_user.model_dump(),
                        "userSelection": user_selection,
                        "messages": [AIMessage(content=f"Usuario {selected_user.nombreCompleto} seleccionado por LLM y puede agendar citas.")]
                    })
                else:
                    return Command(goto="user_rejected", update={
                        "decision": "rejected",
                        "selectedUser": selected_user.model_dump(),
                        "userSelection": user_selection,
                        "messages": [AIMessage(content=f"Usuario {selected_user.nombreCompleto} seleccionado por LLM pero no puede agendar citas.")]
                    })
        
        # If LLM couldn't determine the user
        return Command(goto="user_rejected", update={
            "decision": "rejected",
            "userSelection": user_selection,
            "messages": [AIMessage(content=f"No pude identificar claramente qué usuario seleccionaste con '{user_selection}'. Por favor intenta de nuevo con información más específica.")]
        })
        
    except Exception as e:
        print(f"Error en procesamiento LLM: {e}")
        return Command(goto="user_rejected", update={
            "decision": "rejected",
            "userSelection": user_selection,
            "messages": [AIMessage(content="Hubo un error procesando tu selección. Por favor intenta de nuevo.")]
        })

# Next steps after approval
def approved_node(state: State) -> State:
    """Process approved user - can schedule appointments"""
    selected_user = state.get("selectedUser")
    if selected_user:
        user = User(**selected_user)
        return {
            "messages": [AIMessage(content=user.msgStatus)]
        }
    else:
        print("✅ Approved path taken (no specific user)")
        return state

# Alternative path after rejection
def rejected_node(state: State) -> State:
    """Process rejected user - cannot schedule appointments"""
    selected_user = state.get("selectedUser")
    if selected_user:
        user = User(**selected_user)
        return {
            "messages": [AIMessage(content=user.msgStatus)]
        }
    else:
        print("❌ Rejected path taken (no specific user)")
        return state

def determine_entry_point(state: State) -> str:
    """Determine the entry point based on whether user is already selected"""
    selected_user = state.get("selectedUser")
    if selected_user:
        print(f"✅ User already selected: {selected_user.get('nombreCompleto', 'Unknown')}")
        return "agent_node"
    else:
        print("🔄 No user selected, starting with user selection")
        return "llm_user_selection"

def invoke_graph(graph_params: dict):
    """Invoke the graph with checkpoint memory"""
    try:
        # Create initial state from parameters
        state = State.create_from_params(graph_params)
        
        # Run the graph with checkpoint memory
        thread = {"configurable": {"thread_id": state["sessionId"]}}
        
        result = graph.invoke(state, config=thread)
        
        return {"messages": [result["messages"][-1]]}
            
    except Exception as e:
        print(f"Error invoking graph: {e}")
        error_message = AIMessage(content="Lo siento, tuve un problema técnico. Por favor, intenta de nuevo.")
        return {"messages": [error_message]}

def agent_node(state: State):
    """Agent node that processes messages and maintains state"""
    print(f"Agent processing state: {state}")
    
    # Get the appropriate provider
    model_provider = state.get("modelProvider")
    if model_provider == "openai":
        provider = OpenAIProvider()
    elif model_provider == "anthropic":
        provider = AnthropicProvider()
    else:  # Default to ollama
        provider = OllamaProvider()

    # Get the last message
    messages = state.get("messages", [])
    if not messages:
        error_message = AIMessage(content="No se encontró ningún mensaje para procesar.")
        return {"messages": [error_message]}

    # Get the LangChain model
    llm = provider.get_langchain_model()
    
    # Create system prompt with state context and user data
    system_message_content = system_prompt_agent()
    
    # Create a prompt template with explicit history handling
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message_content),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )

    # Bind tools to the model
    llm_with_tools = llm.bind_tools(tools)
    
    # Create the conversational chain
    chain = prompt | llm_with_tools
    
    print(f"✅ Processing with tools ({len(tools)} tools available)")
    
    # Create a runnable with message history
    chain_with_history = RunnableWithMessageHistory(
        chain, 
        get_redis_history, 
        input_messages_key="input", 
        history_messages_key="history"
    )
    try:
        # Obtener el último mensaje de manera segura
        if len(state["messages"]) > 0:
            last_message = state["messages"][-1].content
        else:
            # Si no hay mensajes, usar un mensaje por defecto
            last_message = "Hola, ¿en qué puedo ayudarte?"
       
        print(f"Last message: {last_message}")

        response = chain_with_history.invoke(
            {"input": last_message}, 
            config={"configurable": {"session_id": state["sessionId"]}}
        )

        print(f"Model response: {response}")
        print(f"Has tool_calls: {hasattr(response, 'tool_calls') and response.tool_calls}")
        return {"messages": [response]}
        
    except Exception as e:
        print(f"ERROR invoking model: {e}")
        error_message = AIMessage(content="Lo siento, tuve un problema técnico. Por favor, intenta de nuevo.")
        clear_redis_history(state["sessionId"])
        return {"messages": [error_message]}

# Build the graph
builder = StateGraph(State)
builder.add_node("llm_user_selection", llm_user_selection)
builder.add_node("user_approved", approved_node)
builder.add_node("user_rejected", rejected_node)
builder.add_node("agent_node", agent_node)

# Use conditional entry point
builder.add_conditional_edges(
    "__start__",
    determine_entry_point,
    {
        "llm_user_selection": "llm_user_selection",
        "agent_node": "agent_node"
    }
)

builder.add_edge("user_approved", "agent_node")
builder.add_edge("agent_node", END)  # End after processing one message
builder.add_edge("user_rejected", "llm_user_selection")

graph = builder.compile()