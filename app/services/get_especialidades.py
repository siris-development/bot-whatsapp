import requests
from langchain.tools import tool
from utils.constants import Constants
from app.models.especialidad_model import Especialidad

@tool
def get_especialidades(nit: int) -> list[Especialidad]:
    """
    Obtiene la lista de especialidades para un NIT específico.

    Args:
        nit (int): Número de identificación tributaria de la entidad.
    """
    params = {"nit": nit}

    try:
        resp = requests.get(url=f"{Constants.base_url}/especialidades", params=params)
        resp.raise_for_status()
        data = resp.json()
        especialidades = [Especialidad(**item).model_dump() for item in data]
        return especialidades
    except requests.RequestException as e:
        try:
            error_response = resp.json()
            if isinstance(error_response, dict) and "statusCode" in error_response and "message" in error_response:
                return error_response
        except Exception:
            pass
        return str(e)

