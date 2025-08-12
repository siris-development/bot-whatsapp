import requests
from langchain.tools import tool
from utils.constants import Constants
from app.models.sede_model import Sede

@tool
def get_sedes(nit: int):
    """
    Obtiene la lista de sedes para un NIT específico.

    Realiza una solicitud GET al endpoint `/sedes` y devuelve una lista de objetos `Sede`.

    Args:
        nit (int): Número de identificación tributaria de la entidad.

    Returns:
        list[Sede]: Lista de sedes obtenidas. Lista vacía si ocurre un error.
    """
    params = {"nit": nit}

    try:
        resp = requests.get(url=f"{Constants.base_url}/sedes", params=params)
        resp.raise_for_status()
        data = resp.json()
        sedes = [Sede(**item) for item in data]
        return sedes
    except requests.RequestException as e:
        print(f"Error en GET {Constants.base_url}: {e}")
        return []