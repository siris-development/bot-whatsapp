import requests
from utils.constants import Constants
from langchain_core.tools import tool
from app.schemas.especialidad import Especialidad
from pydantic import ValidationError

@tool
def get_especialidades(nit: int) -> list:
    """Obtiene la lista de especialidades para un NIT específico usando el MCP server."""
    try:
        # Usar el endpoint directo del MCP server
        resp = requests.get(url=f"{Constants.base_url}/mcp-server/tools/getEspecialidades", params={"nit": nit})
        resp.raise_for_status()
        data = resp.json()
        
        # Validar y convertir cada especialidad usando Pydantic
        especialidades = []
        for item in data:
            try:
                especialidad = Especialidad(**item)
                especialidades.append(especialidad.model_dump())
            except ValidationError as e:
                # Return the raw item if validation fails
                especialidades.append(item)
        
        return especialidades
    except requests.RequestException as e:
        try:
            error_response = resp.json()
            if isinstance(error_response, dict) and "statusCode" in error_response and "message" in error_response:
                return error_response
        except Exception:
            pass
        return str(e)