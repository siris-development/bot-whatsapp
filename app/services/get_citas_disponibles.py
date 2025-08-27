import requests
from langchain.tools import tool
from utils.constants import Constants
from app.schemas.cita_disponible import CitaDisponible

@tool
def get_citas_disponibles(nit: int, idSede: int, idEspecialidad: int, fecha:str) -> list[CitaDisponible]:
    """
    Obtiene las citas disponibles para un NIT, sede, especialidad y fecha específicos.

    Args:
        nit (int): Número de identificación tributaria de la entidad.
        idSede (int): Identificador de la sede.
        idEspecialidad (int): Identificador de la especialidad.
        fecha (str): Fecha de búsqueda en formato 'YYYY-MM-DD'.
    """
    params = {
        "nit": nit, 
        "idSede": idSede,
        "idEspecialidad": idEspecialidad,
        "fecha": fecha,
    }

    try:
        resp = requests.get(url=f"{Constants.base_url}/cronhis/citas-disponibles", params=params)
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