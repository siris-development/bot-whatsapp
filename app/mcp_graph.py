import asyncio
import json
import requests
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.ollama_provider import OllamaProvider
from app.custom_mcp_client import CustomMCPClient
from app.schemas.whatsapp_response import WhatsAppMessage, WhatsAppResponse
from utils.constants import Constants

# Cliente MCP global
mcp_client = CustomMCPClient("https://gateway.siriscloud.com.co/api/mcp-server?nit=900410267")

async def create_mcp_tools():
    """Create LangGraph tools from MCP server tools"""
    try:
        # Get tools from MCP server
        tools_info = await mcp_client.get_tools_info()
        print(f"Creating {len(tools_info)} LangGraph tools from MCP server")
        
        langgraph_tools = []
        
        for tool_info in tools_info:
            tool_name = tool_info['name']
            tool_description = tool_info['description']
            tool_schema = tool_info['inputSchema']
            
            # Create a LangGraph tool wrapper for each MCP tool
            def create_tool_wrapper(name, description, schema):
                @tool
                def mcp_tool_wrapper(**kwargs) -> str:
                    """Wrapper for MCP tool"""
                    try:
                        # Run the async call in a new event loop
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(mcp_client.call_tool(name, kwargs))
                        loop.close()
                        return json.dumps(result, ensure_ascii=False, indent=2)
                    except Exception as e:
                        return f"Error calling {name}: {str(e)}"
                
                # Set the tool name and description
                mcp_tool_wrapper.name = name
                mcp_tool_wrapper.description = description
                return mcp_tool_wrapper
            
            langgraph_tool = create_tool_wrapper(tool_name, tool_description, tool_schema)
            langgraph_tools.append(langgraph_tool)
            print(f"  ✓ Created tool: {tool_name}")
        
        return langgraph_tools
        
    except Exception as e:
        print(f"Error creating MCP tools: {e}")
        return []

def send_to_whatsapp(message_content: str, session_id: str, phone_number_id: str, to: str):
    """Send a message to WhatsApp"""
    try:
        print(f"Sending to WhatsApp: {message_content}")
        
        post_data = WhatsAppResponse(
            sessionId=session_id,
            phoneNumberId=phone_number_id,
            to=to,
            messages=[WhatsAppMessage(type="text", content=str(message_content))]
        )
        
        post_data_dict = post_data.model_dump()
        
        headers = {"Content-Type": "application/json"}
        resp = requests.post(
            url=f"{Constants.base_url}/whatsapp/send-message", 
            headers=headers, 
            json=post_data_dict
        )
        resp.raise_for_status()
        data = resp.json()

        print(f"WhatsApp API response: {data}")
        return True

    except requests.exceptions.ConnectionError as e:
        print(f"Error de conexión con WhatsApp API: {e}")
        return False
        
    except requests.exceptions.Timeout as e:
        print(f"Timeout en WhatsApp API: {e}")
        return False
        
    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP en WhatsApp API: {e}")
        return False
        
    except requests.RequestException as e:
        print(f"Error general en WhatsApp API: {e}")
        return False
        
    except Exception as e:
        print(f"Error inesperado: {e}")
        return False

def get_langchain_model(provider_type: str):
    """Get the appropriate LangChain model from provider"""
    if provider_type == "openai":
        provider = OpenAIProvider(model_name="gpt-4o")
        return provider.get_langchain_model()
    elif provider_type == "anthropic":
        provider = AnthropicProvider(model_name="claude-3-5-sonnet-20241022")
        return provider.get_langchain_model()
    elif provider_type == "ollama":
        provider = OllamaProvider(model_name="gpt-oss:20b")
        return provider.get_langchain_model()
    else:
        return None

async def process_message_and_send_to_whatsapp(
    user_message: str, 
    session_id: str, 
    phone_number_id: str, 
    to: str,
    provider_type: str
):
    """Process a user message with MCP tools and send response to WhatsApp"""
    try:
        # Create the agent
        agent = await make_graph(provider_type)
        if not agent:
            error_msg = "Lo siento, no puedo acceder a los servicios de IA en este momento. Por favor, intenta de nuevo más tarde."
            send_to_whatsapp(error_msg, session_id, phone_number_id, to)
            return False
        
        print(f"Processing message: {user_message}")
        
        # Process the message with the agent
        response = await agent.ainvoke({
            "messages": [HumanMessage(content=user_message)]
        })
        
        # Extract the final response
        if "messages" in response and response["messages"]:
            # Get the last message from the response
            last_message = response["messages"][-1]
            
            if hasattr(last_message, 'content') and last_message.content:
                message_content = last_message.content
            else:
                message_content = "Lo siento, no pude procesar tu solicitud. Por favor, intenta de nuevo."
        else:
            message_content = "Lo siento, no pude procesar tu solicitud. Por favor, intenta de nuevo."
        
        # Send the response to WhatsApp
        success = send_to_whatsapp(message_content, session_id, phone_number_id, to)
        
        if success:
            print("✅ Message sent to WhatsApp successfully")
        else:
            print("❌ Failed to send message to WhatsApp")
        
        return success
        
    except Exception as e:
        print(f"Error processing message: {e}")
        error_msg = "Lo siento, tuve un problema técnico. Por favor, intenta de nuevo."
        send_to_whatsapp(error_msg, session_id, phone_number_id, to)
        return False

async def invoke_mcp_graph(graph_params: dict):
    """Invoke the MCP graph with the same interface as the original graph"""
    try:
        provider_type = graph_params.get("provider_type", "ollama")
        agent = await make_graph(provider_type)
        
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
        
        # Process the message with the agent
        response = await agent.ainvoke({
            "messages": [HumanMessage(content=message_content)]
        })
        
        return response
        
    except Exception as e:
        print(f"Error invoking MCP graph: {e}")
        error_message = AIMessage(content="Lo siento, tuve un problema técnico. Por favor, intenta de nuevo.")
        return {"messages": [error_message]}

async def make_graph(provider_type: str = "ollama"):
    """Crea el agente LangGraph con las herramientas MCP"""
    try:
        
        # Get LangChain model directly from provider
        custom_llm_provider = get_langchain_model(provider_type)

        if custom_llm_provider is None:
            print("❌ No LangChain model available")
            return None
        
        # Get model name based on provider type
        if provider_type == "openai":
            model_name = "gpt-4o"
        elif provider_type == "anthropic":
            model_name = "claude-3-5-sonnet-20241022"
        elif provider_type == "ollama":
            model_name = "gpt-oss:20b"
        else:
            model_name = "gpt-4o"  # Default fallback
            
        print(f"Creating LangGraph agent with model: {model_name}")
        print(f"Using LangChain model: {custom_llm_provider.__class__.__name__}")
        
        # Get MCP tools as LangGraph tools
        mcp_tools = await create_mcp_tools()
        
        if not mcp_tools:
            print("❌ No MCP tools available")
            return None
        
        # Create the LangGraph agent
        print(f"Creating agent with {len(mcp_tools)} tools...")
        print(f"Tool names: {[tool.name for tool in mcp_tools]}")
        
        agent = create_react_agent(custom_llm_provider, mcp_tools)
        
        print(f"✅ LangGraph agent created successfully with {len(mcp_tools)} tools")
        return agent
        
    except Exception as e:
        print(f"Error creating LangGraph agent: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None