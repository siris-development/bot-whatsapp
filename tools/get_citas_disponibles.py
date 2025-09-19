import requests
from utils.constants import Constants
from langchain_core.tools import tool
from app.schemas.cita_disponible import CitaDisponible
from pydantic import ValidationError

@tool
def get_citas_disponibles(nit: int, idSede: int, idEspecialidad: int, fecha: str) -> list:
    """Obtiene las citas disponibles para un NIT, sede, especialidad y fecha específicos usando el MCP server."""
    try:
        # Usar el endpoint directo del MCP server con POST
        headers = {"Content-Type": "application/json"}
        post_data = {
            "idSede": idSede,
            "idEspecialidad": idEspecialidad,
            "fecha": fecha
        }
        
        resp = requests.post(
            url=f"{Constants.base_url}/mcp-server/tools/getCitasDisponibles",
            headers=headers,
            params={"nit": nit},
            json=post_data
        )
        resp.raise_for_status()
        data = resp.json()
        
        # Validar y convertir cada cita disponible usando Pydantic
        citas = []
        for item in data:
            try:
                cita = CitaDisponible(**item)
                citas.append(cita.model_dump())
            except ValidationError as e:
                # Return the raw item if validation fails
                citas.append(item)
        
        return citas
    except requests.RequestException as e:
        try:
            error_response = resp.json()
            if isinstance(error_response, dict) and "statusCode" in error_response and "message" in error_response:
                return error_response
        except Exception:
            pass
        return str(e)
