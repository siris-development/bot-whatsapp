import requests
from utils.constants import Constants
from langchain_core.tools import tool
from app.schemas.sede import Sede

@tool
def get_sedes(nit: int) -> list:
    """Obtiene la lista de sedes para un NIT específico."""
    try:
        resp = requests.get(url=f"{Constants.base_url}/cronhis/sedes", params={"nit": nit})
        resp.raise_for_status()
        data = resp.json()
        sedes = [Sede(**item).model_dump() for item in data]
        return sedes
    except requests.RequestException as e:
        try:
            error_response = resp.json()
            if isinstance(error_response, dict) and "statusCode" in error_response and "message" in error_response:
                return error_response
        except Exception:
            pass
        return str(e)
