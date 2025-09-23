import asyncio
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.ollama_provider import OllamaProvider
from app.state import State
from app.schemas.user import User
from utils.constants import system_prompt_llm_user_selection, system_prompt_agent
from typing import Literal
from app.mcp_client import create_cronhis_tools

# LLM-powered user selection node
def llm_user_selection(state: State) -> Command[Literal["user_approved", "user_rejected"]]:
    """LLM-powered user selection that intelligently processes user input"""
    users = state.get("users", [])
    users = [User(**user) for user in users]
    user_list = "\n".join([f"{i+1}. {user.nombreCompleto}" for i, user in enumerate(users)])
    
    user_selection = state.get("userSelection")
    
    if not user_selection:
        user_selection = interrupt({
            "message": f"Por favor selecciona un usuario escribiendo el número, nombre, o cualquier información que te ayude a identificarlo:\n{user_list}",
        })

    model_provider = state.get("modelProvider")
    
    if model_provider == "openai":
        provider = OpenAIProvider()
    elif model_provider == "anthropic":
        provider = AnthropicProvider()
    else:
        provider = OllamaProvider()
    
    selection_prompt = system_prompt_llm_user_selection(user_list, user_selection)

    try:
        model = provider.get_langchain_model()
        llm_response = model.invoke(selection_prompt)
        response_content = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
        
        if response_content.strip().isdigit():
            selected_index = int(response_content.strip()) - 1
            if 0 <= selected_index < len(users):
                selected_user = users[selected_index]
                
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
        
        return Command(goto="user_rejected", update={
            "decision": "rejected",
            "userSelection": user_selection,
            "messages": [AIMessage(content=f"No pude identificar claramente qué usuario seleccionaste con '{user_selection}'. Por favor intenta de nuevo con información más específica.")]
        })
        
    except Exception as e:
        return Command(goto="user_rejected", update={
            "decision": "rejected",
            "userSelection": user_selection,
            "messages": [AIMessage(content="Hubo un error procesando tu selección. Por favor intenta de nuevo.")]
        })

def approved_node(state: State) -> State:
    """Process approved user - can schedule appointments"""
    selected_user = state.get("selectedUser")
    if selected_user:
        user = User(**selected_user)
        return {
            "messages": [AIMessage(content=user.msgStatus)]
        }
    else:
        return state

def retry_selection_node(state: State) -> State:
    """Handle retry of user selection with updated retry count"""
    retry_count = state.get("retry_count", 0) + 1
    users = state.get("users", [])
    users = [User(**user) for user in users]
    user_list = "\n".join([f"{i+1}. {user.nombreCompleto}" for i, user in enumerate(users)])
    
    return {
        "retry_count": retry_count,
        "messages": [AIMessage(content=f"Intento {retry_count} de 3. Por favor selecciona un usuario escribiendo el número, nombre, o cualquier información que te ayude a identificarlo:\n{user_list}")]
    }

def rejected_node(state: State) -> State:
    """Process rejected user - cannot schedule appointments"""
    selected_user = state.get("selectedUser")
    user_selection = state.get("userSelection", "")
    
    if selected_user:
        user = User(**selected_user)
        return {
            "messages": [AIMessage(content=f"{user.msgStatus}\n\nSi necesitas ayuda para seleccionar un usuario válido, por favor contacta con soporte.")]
        }
    else:
        return {
            "messages": [AIMessage(content=f"No pude identificar un usuario válido con la información '{user_selection}' después de varios intentos. Por favor contacta con soporte para obtener ayuda.")]
        }

def determine_entry_point(state: State) -> str:
    """Determine the entry point based on whether user is already selected"""
    selected_user = state.get("selectedUser")
    if selected_user:
        return "agent_node"
    else:
        return "llm_user_selection"

async def invoke_graph(graph_params: dict, chat_history=None):
    """Invoke the graph with checkpoint memory and chat history"""
    try:
        messages = [HumanMessage(content=graph_params["input"])]
            
        # If we have chat history, prepend it to the messages
        if chat_history and hasattr(chat_history, 'messages'):
            # Get previous messages from Redis (excluding the current one we just added)
            previous_messages = chat_history.messages[:-1] if len(chat_history.messages) > 1 else []
            # Prepend previous messages to create conversation context
            messages = previous_messages + messages
        
        # Always set messages in graph_params
        graph_params["messages"] = messages
        
        # Create initial state from parameters
        state = State.create_from_params(graph_params)

        session_id = state["to"] + "_" + state["phoneNumberId"]
        
        # Run the graph with checkpoint memory and increased recursion limit
        thread = {"configurable": {"thread_id": session_id}, "recursion_limit": 10}
        
        result = await graph.ainvoke(state, config=thread)
        
        # Check if there's an interrupt (waiting for user input)
        if "__interrupt__" in result and result["__interrupt__"]:
            interrupt_data = result["__interrupt__"][0]
            interrupt_message = interrupt_data.value.get("message", "Esperando tu respuesta...")
            return {"messages": [AIMessage(content=interrupt_message)]}
        
        if result and "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            return {"messages": [last_message]}
        else:
            error_message = AIMessage(content="No se pudo procesar la solicitud. Por favor, intenta de nuevo.")
            return {"messages": [error_message]}
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_message = AIMessage(content=f"Lo siento, tuve un problema técnico: {str(e)}. Por favor, intenta de nuevo.")
        return {"messages": [error_message]}

async def load_mcp_tools_for_state(state: State) -> list:
    """Load MCP tools from the Cronhis MCP server using proper client"""
    nit = state.get("nit")
    
    if not nit:
        print("[ERROR] No NIT provided in state")
        return []
        
    try:
        # Use the proper Cronhis MCP client with timeout
        tools = await asyncio.wait_for(
            create_cronhis_tools(nit=nit),
            timeout=30.0  # 30 second timeout
        )
        return tools
    except asyncio.TimeoutError:
        print(f"[ERROR] Cronhis MCP tools loading timed out after 30 seconds")
        print(f"[DEBUG] Using empty tools list as fallback")
        return []
    except Exception as e:
        print(f"[ERROR] Failed to load Cronhis MCP tools: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"[DEBUG] Using empty tools list as fallback")
        return []

async def agent_node(state: State):
    """Agent node that processes messages and maintains state"""
    
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
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt_agent()),
            MessagesPlaceholder(variable_name="messages")
        ]
    )

    # Load MCP tools
    tools = await load_mcp_tools_for_state(state)
    
    # Bind tools to the model
    llm_with_tools = llm.bind_tools(tools)
    
    # Create the conversational chain
    chain = prompt | llm_with_tools
    
    try:
        # Use LangGraph's built-in message handling instead of RunnableWithMessageHistory
        # This ensures proper tool call/response flow
        response = await chain.ainvoke({"messages": messages})
        
        # Don't store tools in state (they're not serializable)
        return {"messages": [response]}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_message = AIMessage(content=f"Lo siento, tuve un problema técnico: {str(e)}. Por favor, intenta de nuevo.")
        return {"messages": [error_message]}

async def create_tools_node(state: State):
    """Create a dynamic tools node loading tools from MCP"""
    # Load tools dynamically from MCP
    tools = await load_mcp_tools_for_state(state)
    
    # Create ToolNode with the tools
    tool_node = ToolNode(tools)
    
    # Execute the tools
    result = await tool_node.ainvoke(state)
    return result

def route_after_user_selection(state: State) -> str:
    """Route after user selection based on decision"""
    decision = state.get("decision")
    retry_count = state.get("retry_count", 0)
    
    if decision == "approved":
        return "user_approved"
    elif retry_count < 2:  # Allow up to 2 retries
        return "retry_selection"
    else:
        return "user_rejected"

# Create checkpointer for state persistence
checkpointer = MemorySaver()

# Build the graph
builder = StateGraph(State)
builder.add_node("llm_user_selection", llm_user_selection)
builder.add_node("retry_selection", retry_selection_node)
builder.add_node("user_approved", approved_node)
builder.add_node("user_rejected", rejected_node)
builder.add_node("agent_node", agent_node)
builder.add_node("tools", create_tools_node)

# Use conditional entry point
builder.add_conditional_edges(
    "__start__",
    determine_entry_point,
    {
        "llm_user_selection": "llm_user_selection",
        "agent_node": "agent_node"
    }
)

builder.add_conditional_edges("llm_user_selection", route_after_user_selection, ["user_approved", "retry_selection", "user_rejected"])
builder.add_edge("retry_selection", "llm_user_selection")  # Go back to selection with retry count
builder.add_edge("user_approved", "agent_node")
builder.add_edge("user_rejected", END)  # End the conversation after max retries

builder.add_conditional_edges(
    "agent_node",
    tools_condition,
)
builder.add_edge("tools", "agent_node")

graph = builder.compile(checkpointer=checkpointer)