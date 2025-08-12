import requests
from langchain.tools import tool
from utils.constants import Constants
from app.models.guardar_cita_model import GuardarCita

@tool
def guardar_cita(nit: int, idSede: int, idEspecialidad: int, fecha:str, guardarCita: GuardarCita):
    """
    Guarda una cita médica en el sistema para un NIT, sede, especialidad y fecha determinados.

    Realiza una solicitud POST al endpoint `/guardar-cita` enviando los datos del modelo `GuardarCita`.

    Args:
        nit (int): Número de identificación tributaria de la entidad.
        idSede (int): Identificador de la sede.
        idEspecialidad (int): Identificador de la especialidad.
        fecha (str): Fecha de la cita en formato 'YYYY-MM-DD'.
        guardarCita (GuardarCita): Objeto con la información necesaria para guardar la cita.

    Returns:
        None: Imprime la respuesta del servidor o un mensaje de error en consola.
    """
    headers = { "Content-Type": "application/json"}
    params = {
        "nit": nit,
        "idSede": idSede,
        "idEspecialidad": idEspecialidad,
        "fecha": fecha
    }
    post_data = {
        "idUsuario": guardarCita.idUsuario,
        "idSede": guardarCita.idSede,
        "idProfesional": guardarCita.idProfesional,
        "idEspecialidad": guardarCita.idEspecialidad,
        "fecha": guardarCita.fecha,
        "hora": guardarCita.hora,
        "idResolucion": guardarCita.idResolucion
    }

    try:
        resp = requests.post(
            url=f"{Constants.base_url}/guardar-cita",
            headers=headers,
            params=params,
            json=post_data,
        )
        resp.raise_for_status()
        print(resp.json())
    except requests.RequestException as e:
        print(f"Error en POST: {e}")