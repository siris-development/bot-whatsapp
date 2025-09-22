# Guía de Integración MCP Server con LangGraph Python

## Información del Servidor MCP

**Servidor:** Cronhis Citas MCP Server  
**Versión:** 1.0.0  
**Protocolo:** MCP 2024-11-05  
**Transporte:** streamable_http  

## URLs de Conexión

```python
# Producción
MCP_SERVER_URL = "https://gateway.siriscloud.com.co/api/mcp-server"

# Desarrollo local
MCP_SERVER_URL_LOCAL = "http://localhost:3000/api/mcp-server"
```

## Instalación de Dependencias

```bash
pip install mcp langgraph langchain httpx aiohttp
```

## Configuración Básica del Cliente MCP

```python
import asyncio
import httpx
from typing import Dict, Any, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import StdioServerParameters

class CronhisMCPClient:
    def __init__(self, base_url: str, nit: str):
        self.base_url = base_url
        self.nit = nit
        self.session = None
        
    async def initialize(self):
        """Inicializa la conexión con el servidor MCP"""
        async with httpx.AsyncClient() as client:
            # Inicializar el servidor MCP
            response = await client.post(
                f"{self.base_url}?nit={self.nit}",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {}
                }
            )
            return response.json()
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de herramientas disponibles"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}?nit={self.nit}",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
            )
            result = response.json()
            return result.get("result", {}).get("tools", [])
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una herramienta específica"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}?nit={self.nit}",
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
            )
            return response.json()
```

## Integración con LangGraph

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from typing import TypedDict, Annotated, Sequence
import operator

# Estado del grafo
class AgentState(TypedDict):
    messages: Annotated[Sequence[HumanMessage | AIMessage], operator.add]
    nit: str

# Herramientas MCP como funciones de LangChain
class CronhisTools:
    def __init__(self, mcp_client: CronhisMCPClient):
        self.mcp_client = mcp_client
    
    @tool
    async def get_sedes(self) -> str:
        """Obtiene todas las sedes activas disponibles en el sistema"""
        result = await self.mcp_client.call_tool("getSedes", {})
        content = result.get("result", {}).get("content", [])
        if content:
            return content[0].get("text", "")
        return "No se pudieron obtener las sedes"
    
    @tool
    async def get_especialidades(self) -> str:
        """Obtiene todas las especialidades médicas disponibles"""
        result = await self.mcp_client.call_tool("getEspecialidades", {})
        content = result.get("result", {}).get("content", [])
        if content:
            return content[0].get("text", "")
        return "No se pudieron obtener las especialidades"
    
    @tool
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
        content = result.get("result", {}).get("content", [])
        if content:
            return content[0].get("text", "")
        return "No se pudieron obtener las citas disponibles"
    
    @tool
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
        content = result.get("result", {}).get("content", [])
        if content:
            return content[0].get("text", "")
        return "No se pudo guardar la cita"
    
    @tool
    async def consultar_citas(self, num_doc_usr: str) -> str:
        """
        Consulta las citas de un usuario
        
        Args:
            num_doc_usr: Número de documento del usuario
        """
        result = await self.mcp_client.call_tool("consultarCitas", {
            "numDocUsr": num_doc_usr
        })
        content = result.get("result", {}).get("content", [])
        if content:
            return content[0].get("text", "")
        return "No se pudieron consultar las citas"
    
    @tool
    async def cancelar_cita(self, id_cita: int) -> str:
        """
        Cancela una cita médica
        
        Args:
            id_cita: ID de la cita a cancelar
        """
        result = await self.mcp_client.call_tool("cancelarCita", {
            "idCita": id_cita
        })
        content = result.get("result", {}).get("content", [])
        if content:
            return content[0].get("text", "")
        return "No se pudo cancelar la cita"

# Configuración del grafo de LangGraph
def create_cronhis_agent(nit: str):
    # Inicializar cliente MCP
    mcp_client = CronhisMCPClient(
        base_url="https://gateway.siriscloud.com.co/api/mcp-server",
        nit=nit
    )
    
    # Crear herramientas
    cronhis_tools = CronhisTools(mcp_client)
    tools = [
        cronhis_tools.get_sedes,
        cronhis_tools.get_especialidades,
        cronhis_tools.get_citas_disponibles,
        cronhis_tools.guardar_cita,
        cronhis_tools.consultar_citas,
        cronhis_tools.cancelar_cita
    ]
    
    # Nodo de herramientas
    tool_node = ToolNode(tools)
    
    # Función de enrutamiento
    def should_continue(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        return END
    
    # Función del agente (aquí integrarías tu LLM)
    async def call_model(state: AgentState):
        # Aquí deberías integrar tu modelo de lenguaje
        # Por ejemplo, con OpenAI, Anthropic, etc.
        messages = state["messages"]
        # response = await your_llm.ainvoke(messages)
        return {"messages": []}  # Placeholder
    
    # Crear el grafo
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()
```

## Ejemplo de Uso Completo

```python
async def main():
    # Configuración
    NIT = "123456789"  # Reemplaza con el NIT real
    
    # Crear cliente MCP
    client = CronhisMCPClient(
        base_url="https://gateway.siriscloud.com.co/api/mcp-server",
        nit=NIT
    )
    
    # Inicializar conexión
    init_result = await client.initialize()
    print("Inicialización:", init_result)
    
    # Listar herramientas disponibles
    tools = await client.list_tools()
    print("Herramientas disponibles:")
    for tool in tools:
        print(f"- {tool['name']}: {tool['description']}")
    
    # Ejemplo: Obtener sedes
    sedes_result = await client.call_tool("getSedes", {})
    print("Sedes:", sedes_result)
    
    # Ejemplo: Obtener especialidades
    especialidades_result = await client.call_tool("getEspecialidades", {})
    print("Especialidades:", especialidades_result)
    
    # Ejemplo: Buscar citas disponibles
    citas_result = await client.call_tool("getCitasDisponibles", {
        "idSede": 1,
        "idEspecialidad": 2,
        "fecha": "2024-12-01"
    })
    print("Citas disponibles:", citas_result)

# Ejecutar el ejemplo
if __name__ == "__main__":
    asyncio.run(main())
```

## Server-Sent Events (SSE) para Monitoreo

```python
import aiohttp
import asyncio

async def monitor_mcp_server(nit: str):
    """Monitorea el servidor MCP via SSE"""
    url = f"https://gateway.siriscloud.com.co/api/mcp-server/sse?nit={nit}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            async for line in response.content:
                if line:
                    print(f"SSE Event: {line.decode()}")

# Usar en un task separado
# asyncio.create_task(monitor_mcp_server("123456789"))
```

## Herramientas Disponibles

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| `getSedes` | Obtiene todas las sedes activas | Ninguno |
| `getEspecialidades` | Obtiene especialidades médicas | Ninguno |
| `getCitasDisponibles` | Busca citas disponibles | `idSede`, `idEspecialidad`, `fecha` |
| `guardarCita` | Guarda una nueva cita | `idUsuario`, `idSede`, `idProfesional`, `idEspecialidad`, `fecha`, `hora`, `idResolucion` |
| `consultarCitas` | Consulta citas de un usuario | `numDocUsr` |
| `cancelarCita` | Cancela una cita médica | `idCita` |
| `confirmarCita` | Confirma una cita médica | `idCita` |
| `consultarCitasConfirmar` | Citas pendientes de confirmar | `numDocUsr` |
| `consultarCitasCancelar` | Citas que se pueden cancelar | `numDocUsr` |
| `getContactos` | Obtiene contactos de la IPS | Ninguno |

## Manejo de Errores

```python
async def safe_call_tool(client: CronhisMCPClient, tool_name: str, arguments: dict):
    """Llamada segura a herramientas con manejo de errores"""
    try:
        result = await client.call_tool(tool_name, arguments)
        
        if "error" in result:
            print(f"Error del servidor: {result['error']}")
            return None
            
        return result.get("result", {})
        
    except Exception as e:
        print(f"Error en la llamada: {e}")
        return None
```

## Configuración de Seguridad

```python
# Headers recomendados para las solicitudes
HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://tu-dominio.com",  # Opcional
    "Mcp-Session-Id": "unique-session-id"  # Para gestión de sesiones
}
```

## Notas Importantes

1. **NIT Obligatorio**: Todas las llamadas requieren el parámetro `nit` como query parameter
2. **Formato de Fechas**: Usar formato `YYYY-MM-DD`
3. **Formato de Horas**: Usar formato `HH:MM`
4. **JSON-RPC 2.0**: Todas las respuestas siguen este estándar
5. **SSE Disponible**: Para monitoreo en tiempo real en `/sse`

## Soporte y Documentación

- **Endpoint de información**: `GET /api/mcp-server/info`
- **Documentación completa**: Disponible en el repositorio del proyecto
- **Protocolo MCP**: [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

*Generado para el servidor Cronhis Citas MCP v1.0.0*
