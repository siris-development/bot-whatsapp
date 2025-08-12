import requests
from langchain.tools import tool
from utils.constants import Constants
from app.models.especialidad_model import Especialidad

@tool
def get_especialidades(nit: int):
    """
    Obtiene la lista de especialidades para un NIT específico.

    Realiza una solicitud GET al endpoint `/especialidades` y devuelve una lista de objetos `Especialidad`.

    Args:
        nit (int): Número de identificación tributaria de la entidad.

    Returns:
        list[Especialidad]: Lista de especialidades obtenidas. Lista vacía si ocurre un error.
    """
    params = {"nit": nit}

    try:
        resp = requests.get(url=f"{Constants.base_url}/especialidades", params=params)
        resp.raise_for_status()
        data = resp.json()
        especialidades = [Especialidad(**item) for item in data]
        return especialidades
    except requests.RequestException as e:
        print(f"Error en GET {Constants.base_url}: {e}")
        return []

