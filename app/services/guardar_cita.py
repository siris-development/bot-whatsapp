import requests
from langchain_core.tools import tool
from utils.constants import Constants

@tool
def guardar_cita(nit: int, idUsuario: int, idSede: int, idProfesional: int, idEspecialidad: int, fecha: str, hora: str, idResolucion: int) -> dict:
    """Guarda una cita médica en el sistema."""
    headers = {"Content-Type": "application/json"}
    post_data = {
        "idUsuario": idUsuario,
        "idSede": idSede,
        "idProfesional": idProfesional,
        "idEspecialidad": idEspecialidad,
        "fecha": fecha,
        "hora": hora,
        "idResolucion": idResolucion
    }
    try:
        resp = requests.post(
            url=f"{Constants.base_url}/cronhis/guardar-cita",
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
