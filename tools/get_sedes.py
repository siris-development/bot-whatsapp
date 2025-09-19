import requests
from utils.constants import Constants
from langchain_core.tools import tool
from app.schemas.sede import Sede
from pydantic import ValidationError

@tool
def get_sedes(nit: int) -> list:
    """Obtiene la lista de sedes para un NIT específico usando el MCP server."""
    try:
        # Usar el endpoint directo del MCP server
        resp = requests.get(url=f"{Constants.base_url}/mcp-server/tools/getSedes", params={"nit": nit})
        resp.raise_for_status()
        data = resp.json()
        
        # Validar y convertir cada sede usando Pydantic
        sedes = []
        for item in data:
            try:
                sede = Sede(**item)
                sedes.append(sede.model_dump())
            except ValidationError as e:
                # Return the raw item if validation fails
                sedes.append(item)
        
        return sedes
    except requests.RequestException as e:
        try:
            error_response = resp.json()
            if isinstance(error_response, dict) and "statusCode" in error_response and "message" in error_response:
                return error_response
        except Exception:
            pass
        return str(e)
