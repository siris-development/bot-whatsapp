import requests
from utils.constants import Constants
from langchain_core.tools import tool
from app.schemas.especialidad import Especialidad

@tool
def get_especialidades(nit: int) -> list:
    """Obtiene la lista de especialidades para un NIT específico."""
    try:
        resp = requests.get(url=f"{Constants.base_url}/cronhis/especialidades", params={"nit": nit})
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