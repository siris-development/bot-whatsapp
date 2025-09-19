import requests
from langchain_core.tools import tool
from utils.constants import Constants
from app.schemas.guardar_cita import GuardarCita
from pydantic import ValidationError

@tool
def guardar_cita(nit: int, idUsuario: int, idSede: int, idProfesional: int, idEspecialidad: int, fecha: str, hora: str, idResolucion: int) -> dict:
    """Guarda una cita médica en el sistema usando el MCP server."""
    try:
        # Validar los parámetros de entrada usando Pydantic
        cita_data = {
            "idUsuario": idUsuario,
            "idSede": idSede,
            "idProfesional": idProfesional,
            "idEspecialidad": idEspecialidad,
            "fecha": fecha,
            "hora": hora,
            "idResolucion": idResolucion
        }
        
        # Validar con el schema GuardarCita
        try:
            validated_cita = GuardarCita(**cita_data)
            post_data = validated_cita.model_dump()
        except ValidationError as e:
            return {"error": f"Invalid cita data: {str(e)}"}
        
        headers = {"Content-Type": "application/json"}
        
        # Usar el endpoint directo del MCP server
        resp = requests.post(
            url=f"{Constants.base_url}/mcp-server/tools/guardarCita",
            headers=headers,
            params={"nit": nit},
            json=post_data,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        try:
            error_response = resp.json()
            if isinstance(error_response, dict) and "statusCode" in error_response and "message" in error_response:
                return error_response
        except Exception:
            pass
        return str(e)
