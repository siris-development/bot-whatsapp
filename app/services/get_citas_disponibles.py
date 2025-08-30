import requests
from utils.constants import Constants
from langchain_core.tools import tool
from app.schemas.cita_disponible import CitaDisponible

@tool
def get_citas_disponibles(nit: int, idSede: int, idEspecialidad: int, fecha: str) -> list:
    """Obtiene las citas disponibles para un NIT, sede, especialidad y fecha específicos."""
    try:
        resp = requests.get(
            url=f"{Constants.base_url}/cronhis/citas-disponibles", 
            params={
                "nit": nit,
                "idSede": idSede,
                "idEspecialidad": idEspecialidad,
                "fecha": fecha
            }
        )
        resp.raise_for_status()
        data = resp.json()
        citas = [CitaDisponible(**item).model_dump() for item in data]
        return citas
    except requests.RequestException as e:
        try:
            error_response = resp.json()
            if isinstance(error_response, dict) and "statusCode" in error_response and "message" in error_response:
                return error_response
        except Exception:
            pass
        return str(e)
