from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.ollama_provider import OllamaProvider
from app.redis_client import get_redis_history
from app.validators.validate_user_permissions import validate_user_permissions
from utils.constants import system_prompt_agent
from tools.create_mcp_tools import create_mcp_tools

async def invoke_mcp_graph(graph_params: dict):
    """Invoke the MCP graph with the same interface as the original graph"""
    try:
        # Check user permissions first
        users = graph_params.get("users", [])
        has_permission, permission_message = validate_user_permissions(users)
        
        if not has_permission:
            error_message = AIMessage(content=f"❌ {permission_message} Por favor, contacta al administrador para obtener permisos de agendamiento.")
            return {"messages": [error_message]}
        
        print(f"✅ {permission_message}")
        
        model_provider = graph_params.get("modelProvider")
        agent = await make_graph(model_provider)
        
        if not agent:
            error_message = AIMessage(content="Lo siento, no puedo acceder a los servicios de IA en este momento. Por favor, intenta de nuevo más tarde.")
            return {"messages": [error_message]}
        
        # Extract the last message from the graph_params
        messages = graph_params.get("messages", [])
        if not messages:
            error_message = AIMessage(content="No se encontró ningún mensaje para procesar.")
            return {"messages": [error_message]}
        
        # Get the last message content
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            message_content = last_message.content
        else:
            message_content = str(last_message)
        
        # Process the message with the agent using RunnableWithMessageHistory
        response = await agent.ainvoke(
            {"input": message_content}, 
            config={"configurable": {"session_id": graph_params.get("sessionId")}}
        )
        
        return {"messages": [response]}
        
    except Exception as e:
        print(f"Error invoking MCP graph: {e}")
        error_message = AIMessage(content="Lo siento, tuve un problema técnico. Por favor, intenta de nuevo.")
        return {"messages": [error_message]}

async def make_graph(model_provider: str):
    """Crea el agente LangGraph con las herramientas MCP usando RunnableWithMessageHistory"""
    try:
        print(f"Creating MCP graph with provider: {model_provider}")
        
        # Get MCP tools as LangGraph tools
        mcp_tools = await create_mcp_tools()
        
        if not mcp_tools:
            print("❌ No MCP tools available")
            return None
        
        print(f"✅ Found {len(mcp_tools)} MCP tools")
        
        # Get the appropriate provider
        if model_provider == "openai":
            provider = OpenAIProvider()
        elif model_provider == "anthropic":
            provider = AnthropicProvider()
        else:  # Default to ollama
            provider = OllamaProvider()
        
        # Get the LangChain model
        llm = provider.get_langchain_model()
        
        # Create system prompt
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
        llm_with_tools = llm.bind_tools(mcp_tools)
        
        # Create the conversational chain
        chain = prompt | llm_with_tools
        
        # Create a runnable with message history
        chain_with_history = RunnableWithMessageHistory(
            chain, 
            get_redis_history, 
            input_messages_key="input", 
            history_messages_key="history"
        )
        
        print(f"✅ LangGraph agent created successfully with {len(mcp_tools)} tools")
        return chain_with_history
        
    except Exception as e:
        print(f"❌ Error creating MCP graph: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None