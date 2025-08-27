import requests
from langchain.tools import tool
from utils.constants import Constants
from app.schemas.guardar_cita import GuardarCita

@tool
def guardar_cita(nit: int, guardarCita: GuardarCita):
    """
    Guarda una cita médica en el sistema para un NIT, sede, especialidad y fecha determinados.

    Args:
        nit (int): Número de identificación tributaria de la entidad.
        guardarCita (GuardarCita): Objeto con la información necesaria para guardar la cita.
    """
    headers = { "Content-Type": "application/json"}
    params = {
        "nit": nit,
    }
    post_data = {
        "idUsuario": guardarCita.idUsuario,
        "idSede": guardarCita.idSede,
        "idProfesional": guardarCita.idProfesional,
        "idEspecialidad": guardarCita.idEspecialidad,
        "fecha": guardarCita.fecha,
        "hora": guardarCita.hora,
        "resolucionId": guardarCita.resolucionId
    }

    try:
        resp = requests.post(
            url=f"{Constants.base_url}/cronhis/guardar-cita",
            headers=headers,
            params=params,
            json=post_data,
        )
        resp.raise_for_status()
        print(resp.json())
    except requests.RequestException as e:
        try:
            error_response = resp.json()
            if isinstance(error_response, dict) and "statusCode" in error_response and "message" in error_response:
                return error_response
        except Exception:
            pass
        return str(e)
    