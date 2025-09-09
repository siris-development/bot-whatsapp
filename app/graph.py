# graph.py - Solución para el problema de timeout MCP
import asyncio
import json
import os
import requests
from contextlib import asynccontextmanager
from typing import List, Dict, Any
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class CustomMCPClient:
    """Cliente MCP personalizado que evita el problema de timeout"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session_id = 1
    
    def _make_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Realiza una petición HTTP al servidor MCP"""
        payload = {
            "jsonrpc": "2.0",
            "id": self.session_id,
            "method": method,
            "params": params or {}
        }
        
        response = requests.post(
            self.base_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        self.session_id += 1
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Error HTTP {response.status_code}: {response.text}")
    
    def get_tools_info(self) -> List[Dict[str, Any]]:
        """Obtiene información de las herramientas disponibles"""
        result = self._make_request("tools/list")
        return result.get("result", {}).get("tools", [])
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Llama a una herramienta específica"""
        result = self._make_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        return result.get("result", {})

# Cliente MCP global
mcp_client = CustomMCPClient("https://national-clam-ghastly.ngrok-free.app/api/mcp-server?nit=900410267")

# Definir herramientas dinámicamente basadas en el servidor MCP
@tool
def get_sedes() -> str:
    """Obtiene todas las sedes activas disponibles en el sistema"""
    try:
        result = mcp_client.call_tool("getSedes", {})
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error al obtener sedes: {str(e)}"

@tool
def get_especialidades() -> str:
    """Obtiene todas las especialidades médicas disponibles en el sistema"""
    try:
        result = mcp_client.call_tool("getEspecialidades", {})
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error al obtener especialidades: {str(e)}"

@tool
def get_citas_disponibles(id_sede: int, id_especialidad: int, fecha: str) -> str:
    """
    Obtiene las citas disponibles para una sede, especialidad y fecha específica
    
    Args:
        id_sede: ID de la sede
        id_especialidad: ID de la especialidad
        fecha: Fecha en formato YYYY-MM-DD
    """
    try:
        result = mcp_client.call_tool("getCitasDisponibles", {
            "idSede": id_sede,
            "idEspecialidad": id_especialidad,
            "fecha": fecha
        })
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error al obtener citas disponibles: {str(e)}"

@tool
def guardar_cita(id_usuario: int, id_sede: int, id_profesional: int, 
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
    try:
        result = mcp_client.call_tool("guardarCita", {
            "idUsuario": id_usuario,
            "idSede": id_sede,
            "idProfesional": id_profesional,
            "idEspecialidad": id_especialidad,
            "fecha": fecha,
            "hora": hora,
            "idResolucion": id_resolucion
        })
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error al guardar cita: {str(e)}"

@tool
def consultar_citas(num_doc_usr: str) -> str:
    """
    Consulta las citas de un usuario
    
    Args:
        num_doc_usr: Número de documento del usuario
    """
    try:
        result = mcp_client.call_tool("consultarCitas", {
            "numDocUsr": num_doc_usr
        })
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error al consultar citas: {str(e)}"

@tool
def cancelar_cita(id_cita: int) -> str:
    """
    Cancela una cita médica
    
    Args:
        id_cita: ID de la cita a cancelar
    """
    try:
        result = mcp_client.call_tool("cancelarCita", {
            "idCita": id_cita
        })
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error al cancelar cita: {str(e)}"

@tool
def get_contactos() -> str:
    """Obtiene los contactos de la IPS"""
    try:
        result = mcp_client.call_tool("getContactos", {})
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error al obtener contactos: {str(e)}"

@tool
def get_users_by_phone(message_id: str, msg_init: str, display_phone_number: str) -> str:
    """
    Obtiene usuarios por número de teléfono
    
    Args:
        message_id: ID del mensaje
        msg_init: Mensaje inicial
        display_phone_number: Número de teléfono a mostrar
    """
    try:
        result = mcp_client.call_tool("getUsersByPhone", {
            "messageId": message_id,
            "msgInit": msg_init,
            "displayPhoneNumber": display_phone_number
        })
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error al obtener usuarios por teléfono: {str(e)}"

# Lista de todas las herramientas disponibles
AVAILABLE_TOOLS = [
    get_sedes,
    get_especialidades, 
    get_citas_disponibles,
    guardar_cita,
    consultar_citas,
    cancelar_cita,
    get_contactos,
    get_users_by_phone
]

async def make_graph():
    """Crea el agente con las herramientas MCP personalizadas"""
    try:
        print("Conectando al servidor MCP...")
        
        # Verificar conectividad del servidor
        tools_info = mcp_client.get_tools_info()
        print(f"Herramientas obtenidas: {len(tools_info)}")
        
        for i, tool_info in enumerate(tools_info, 1):
            print(f"  {i}. {tool_info['name']}: {tool_info['description'][:50]}...")
        
        # Crear el agente con las herramientas personalizadas
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        agent = create_react_agent(llm, AVAILABLE_TOOLS)
        
        print("Agente creado exitosamente")
        return agent
        
    except Exception as e:
        print(f"Error al crear el agente: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

async def main():
    """Función principal para probar el agente"""
    agent = await make_graph()
    if agent:
        print("Ejecutando consulta...")
        
        try:
            response = await agent.ainvoke({
                "messages": [("user", "Consulta sedes")]
            })
            
            print("\n📋 Respuesta del agente:")
            if "messages" in response:
                for msg in response["messages"]:
                    if hasattr(msg, 'content'):
                        print(msg.content)
            else:
                print(response)
                
        except Exception as e:
            print(f"Error al ejecutar consulta: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
    else:
        print("No se pudo crear el agente")

if __name__ == "__main__":
    asyncio.run(main())
