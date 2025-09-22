"""MCP Client implementation for Cronhis Citas MCP Server integration with LangGraph.

This module provides a proper MCP client that follows the documentation specifications
for integrating with the Cronhis Citas MCP Server via HTTP.
"""

import json
from typing import Any, Dict, List, Optional
import httpx
from langchain_core.tools import BaseTool, ToolException
from mcp.types import Tool as MCPTool, CallToolResult, TextContent

class CronhisMCPClient:
    """MCP client for Cronhis Citas MCP Server following the documentation specifications."""
    
    def __init__(self, base_url: str, nit: str, timeout: float = 30.0):
        """Initialize the Cronhis MCP client.
        
        Args:
            base_url: Base URL of the MCP server
            nit: NIT parameter required for all requests
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.nit = nit
        self.timeout = timeout
        self._session_id = None
        
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP session.
        
        Returns:
            Server capabilities and info
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}?nit={self.nit}",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Origin": "https://tu-dominio.com",  # Optional as per docs
                    "Mcp-Session-Id": f"session-{self.nit}"  # For session management
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise Exception(f"MCP initialization failed: {result['error']}")
                
            return result.get("result", {})
    
    async def list_tools(self) -> List[MCPTool]:
        """List all available tools from the MCP server.
        
        Returns:
            List of MCP tools
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}?nit={self.nit}",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Mcp-Session-Id": f"session-{self.nit}"
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise Exception(f"Failed to list tools: {result['error']}")
                
            tools_data = result.get("result", {}).get("tools", [])
            return [self._parse_tool(tool_data) for tool_data in tools_data]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}?nit={self.nit}",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Mcp-Session-Id": f"session-{self.nit}"
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                error_msg = result["error"].get("message", "Unknown error")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {error_msg}")],
                    isError=True
                )
                
            # Parse the result according to documentation
            result_data = result.get("result", {})
            content = result_data.get("content", [])
            
            if content and isinstance(content, list) and len(content) > 0:
                # Extract text content as per documentation
                content_text = content[0].get("text", json.dumps(content, indent=2, ensure_ascii=False))
            else:
                # Fallback to JSON representation
                content_text = json.dumps(result_data, indent=2, ensure_ascii=False)
                
            return CallToolResult(
                content=[TextContent(type="text", text=content_text)],
                isError=False
            )
    
    def _parse_tool(self, tool_data: Dict[str, Any]) -> MCPTool:
        """Parse tool data into MCPTool object.
        
        Args:
            tool_data: Raw tool data from server
            
        Returns:
            MCPTool object
        """
        return MCPTool(
            name=tool_data["name"],
            description=tool_data["description"],
            inputSchema=tool_data["inputSchema"]
        )


class CronhisTools:
    """Wrapper class for Cronhis MCP tools as LangChain tools."""
    
    def __init__(self, mcp_client: CronhisMCPClient):
        """Initialize with MCP client."""
        self.mcp_client = mcp_client
    
    async def get_sedes(self) -> str:
        """Obtiene todas las sedes activas disponibles en el sistema"""
        result = await self.mcp_client.call_tool("getSedes", {})
        if result.isError:
            raise ToolException(result.content[0].text)
        return result.content[0].text
    
    async def get_especialidades(self) -> str:
        """Obtiene todas las especialidades médicas disponibles"""
        result = await self.mcp_client.call_tool("getEspecialidades", {})
        if result.isError:
            raise ToolException(result.content[0].text)
        return result.content[0].text
    
    async def get_citas_disponibles(self, id_sede: int, id_especialidad: int, fecha: str) -> str:
        """
        Obtiene las citas disponibles para una sede, especialidad y fecha específica
        
        Args:
            id_sede: ID de la sede
            id_especialidad: ID de la especialidad
            fecha: Fecha en formato YYYY-MM-DD
        """
        result = await self.mcp_client.call_tool("getCitasDisponibles", {
            "idSede": id_sede,
            "idEspecialidad": id_especialidad,
            "fecha": fecha
        })
        if result.isError:
            raise ToolException(result.content[0].text)
        return result.content[0].text
    
    async def guardar_cita(self, id_usuario: int, id_sede: int, id_profesional: int, 
                          id_especialidad: int, fecha: str, hora: str, id_resolucion: int) -> str:
        """
        Guarda una nueva cita médica
        
        Args:
            id_usuario: ID del usuario
            id_sede: ID de la sede
            id_profesional: ID del profesional
            id_especialidad: ID de la especialidad
            fecha: Fecha en formato YYYY-MM-DD
            hora: Hora en formato HH:MM
            id_resolucion: ID de la resolución
        """
        result = await self.mcp_client.call_tool("guardarCita", {
            "idUsuario": id_usuario,
            "idSede": id_sede,
            "idProfesional": id_profesional,
            "idEspecialidad": id_especialidad,
            "fecha": fecha,
            "hora": hora,
            "idResolucion": id_resolucion
        })
        if result.isError:
            raise ToolException(result.content[0].text)
        return result.content[0].text
    
    async def consultar_citas(self, num_doc_usr: str) -> str:
        """
        Consulta las citas de un usuario
        
        Args:
            num_doc_usr: Número de documento del usuario
        """
        result = await self.mcp_client.call_tool("consultarCitas", {
            "numDocUsr": num_doc_usr
        })
        if result.isError:
            raise ToolException(result.content[0].text)
        return result.content[0].text
    
    async def cancelar_cita(self, id_cita: int) -> str:
        """
        Cancela una cita médica
        
        Args:
            id_cita: ID de la cita a cancelar
        """
        result = await self.mcp_client.call_tool("cancelarCita", {
            "idCita": id_cita
        })
        if result.isError:
            raise ToolException(result.content[0].text)
        return result.content[0].text
    
    async def confirmar_cita(self, id_cita: int) -> str:
        """
        Confirma una cita médica
        
        Args:
            id_cita: ID de la cita a confirmar
        """
        result = await self.mcp_client.call_tool("confirmarCita", {
            "idCita": id_cita
        })
        if result.isError:
            raise ToolException(result.content[0].text)
        return result.content[0].text
    
    async def consultar_citas_confirmar(self, num_doc_usr: str) -> str:
        """
        Consulta citas pendientes de confirmar
        
        Args:
            num_doc_usr: Número de documento del usuario
        """
        result = await self.mcp_client.call_tool("consultarCitasConfirmar", {
            "numDocUsr": num_doc_usr
        })
        if result.isError:
            raise ToolException(result.content[0].text)
        return result.content[0].text
    
    async def consultar_citas_cancelar(self, num_doc_usr: str) -> str:
        """
        Consulta citas que se pueden cancelar
        
        Args:
            num_doc_usr: Número de documento del usuario
        """
        result = await self.mcp_client.call_tool("consultarCitasCancelar", {
            "numDocUsr": num_doc_usr
        })
        if result.isError:
            raise ToolException(result.content[0].text)
        return result.content[0].text
    
    async def get_contactos(self) -> str:
        """Obtiene contactos de la IPS"""
        result = await self.mcp_client.call_tool("getContactos", {})
        if result.isError:
            raise ToolException(result.content[0].text)
        return result.content[0].text


async def create_cronhis_tools(nit: str, base_url: str = "https://gateway.siriscloud.com.co/api/mcp-server") -> List[BaseTool]:
    """Create LangChain tools from Cronhis MCP server.
    
    Args:
        nit: NIT parameter for the MCP server
        base_url: Base URL of the MCP server
        
    Returns:
        List of LangChain tools
    """
    from langchain_core.tools import tool
    
    # Initialize MCP client
    mcp_client = CronhisMCPClient(base_url=base_url, nit=nit)
    
    # Initialize the client
    await mcp_client.initialize()
    
    # Create tools wrapper
    cronhis_tools = CronhisTools(mcp_client)
    
    # Create tools using the @tool decorator approach
    @tool
    async def get_sedes() -> str:
        """Obtiene todas las sedes activas disponibles en el sistema"""
        return await cronhis_tools.get_sedes()
    
    @tool
    async def get_especialidades() -> str:
        """Obtiene todas las especialidades médicas disponibles"""
        return await cronhis_tools.get_especialidades()
    
    @tool
    async def get_citas_disponibles(id_sede: int, id_especialidad: int, fecha: str) -> str:
        """
        Obtiene las citas disponibles para una sede, especialidad y fecha específica
        
        Args:
            id_sede: ID de la sede
            id_especialidad: ID de la especialidad
            fecha: Fecha en formato YYYY-MM-DD
        """
        return await cronhis_tools.get_citas_disponibles(id_sede, id_especialidad, fecha)
    
    @tool
    async def guardar_cita(id_usuario: int, id_sede: int, id_profesional: int, 
                          id_especialidad: int, fecha: str, hora: str, id_resolucion: int) -> str:
        """
        Guarda una nueva cita médica
        
        Args:
            id_usuario: ID del usuario
            id_sede: ID de la sede
            id_profesional: ID del profesional
            id_especialidad: ID de la especialidad
            fecha: Fecha en formato YYYY-MM-DD
            hora: Hora en formato HH:MM
            id_resolucion: ID de la resolución
        """
        return await cronhis_tools.guardar_cita(id_usuario, id_sede, id_profesional, 
                                               id_especialidad, fecha, hora, id_resolucion)
    
    @tool
    async def consultar_citas(num_doc_usr: str) -> str:
        """
        Consulta las citas de un usuario
        
        Args:
            num_doc_usr: Número de documento del usuario
        """
        return await cronhis_tools.consultar_citas(num_doc_usr)
    
    @tool
    async def cancelar_cita(id_cita: int) -> str:
        """
        Cancela una cita médica
        
        Args:
            id_cita: ID de la cita a cancelar
        """
        return await cronhis_tools.cancelar_cita(id_cita)
    
    @tool
    async def confirmar_cita(id_cita: int) -> str:
        """
        Confirma una cita médica
        
        Args:
            id_cita: ID de la cita a confirmar
        """
        return await cronhis_tools.confirmar_cita(id_cita)
    
    @tool
    async def consultar_citas_confirmar(num_doc_usr: str) -> str:
        """
        Consulta citas pendientes de confirmar
        
        Args:
            num_doc_usr: Número de documento del usuario
        """
        return await cronhis_tools.consultar_citas_confirmar(num_doc_usr)
    
    @tool
    async def consultar_citas_cancelar(num_doc_usr: str) -> str:
        """
        Consulta citas que se pueden cancelar
        
        Args:
            num_doc_usr: Número de documento del usuario
        """
        return await cronhis_tools.consultar_citas_cancelar(num_doc_usr)
    
    @tool
    async def get_contactos() -> str:
        """Obtiene contactos de la IPS"""
        return await cronhis_tools.get_contactos()
    
    # Return all tools
    return [
        get_sedes,
        get_especialidades,
        get_citas_disponibles,
        guardar_cita,
        consultar_citas,
        cancelar_cita,
        confirmar_cita,
        consultar_citas_confirmar,
        consultar_citas_cancelar,
        get_contactos
    ]

async def safe_call_tool(client: CronhisMCPClient, tool_name: str, arguments: dict) -> Optional[Dict[str, Any]]:
    """Safe tool call with error handling as per documentation.
    
    Args:
        client: MCP client instance
        tool_name: Name of the tool to call
        arguments: Tool arguments
        
    Returns:
        Tool result or None if error
    """
    try:
        result = await client.call_tool(tool_name, arguments)
        
        if result.isError:
            print(f"Error del servidor: {result.content[0].text}")
            return None
            
        return {"content": result.content[0].text}
        
    except Exception as e:
        print(f"Error en la llamada: {e}")
        return None
