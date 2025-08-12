import requests
from langchain.tools import tool
from utils.constants import Constants
from app.models.cita_disponible_model import CitaDisponible

@tool
def get_citas_disponibles(nit: int, idSede: int, idEspecialidad: int, fecha:str):
    """
    Obtiene las citas disponibles para un NIT, sede, especialidad y fecha específicos.

    Realiza una solicitud GET al endpoint `/citas-disponibles` y devuelve una lista de objetos `CitaDisponible`.

    Args:
        nit (int): Número de identificación tributaria de la entidad.
        idSede (int): Identificador de la sede.
        idEspecialidad (int): Identificador de la especialidad.
        fecha (str): Fecha de búsqueda en formato 'YYYY-MM-DD'.

    Returns:
        list[CitaDisponible]: Lista de citas disponibles. Lista vacía si ocurre un error.
    """
    params = {
        "nit": nit, 
        "idSede": idSede,
        "idEspecialidad": idEspecialidad,
        "fecha": fecha,
    }

    try:
        resp = requests.get(url=f"{Constants.base_url}/citas-disponibles", params=params)
        resp.raise_for_status()
        data = resp.json()
        citas = [CitaDisponible(**item) for item in data]
        return citas
    except requests.RequestException as e:
        print(f"Error en GET {Constants.base_url}: {e}")
        return []