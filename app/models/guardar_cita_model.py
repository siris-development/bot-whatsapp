from datetime import datetime
from pydantic import BaseModel

class GuardarCita(BaseModel):
    idUsuario: int
    idSede: int
    idProfesional: int
    idEspecialidad: int
    fecha: datetime
    hora: str
    idResolucion: int
