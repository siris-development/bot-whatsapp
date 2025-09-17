import asyncio
import json
from langchain_core.tools import tool
from app.custom_mcp_client import CustomMCPClient
from utils.constants import Constants

mcp_client = CustomMCPClient(f"{Constants.base_url}/{Constants.mcp_base_url}")

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
            print(f"✅ Created tool: {tool_name}")
        
        return langgraph_tools
        
    except Exception as e:
        print(f"Error creating MCP tools: {e}")
        return []