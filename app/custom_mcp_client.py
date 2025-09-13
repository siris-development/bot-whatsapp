from dotenv import load_dotenv
from typing import List, Dict, Any
import aiohttp

load_dotenv()

class CustomMCPClient:
    """Cliente MCP personalizado que evita el problema de timeout"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session_id = 1
    
    async def _make_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Realiza una petición HTTP al servidor MCP"""
        payload = {
            "jsonrpc": "2.0",
            "id": self.session_id,
            "method": method,
            "params": params or {}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10),
                ssl=False  # Disable SSL verification for development
            ) as response:
                self.session_id += 1
                
                if response.status in [200, 201]:
                    return await response.json()
                else:
                    text = await response.text()
                    raise Exception(f"Error HTTP {response.status}: {text}")
    
    async def get_tools_info(self) -> List[Dict[str, Any]]:
        """Obtiene información de las herramientas disponibles"""
        result = await self._make_request("tools/list")
        return result.get("result", {}).get("tools", [])
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Llama a una herramienta específica"""
        result = await self._make_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        return result.get("result", {})
