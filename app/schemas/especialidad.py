from pydantic import BaseModel

class Especialidad(BaseModel):
    idEspecialidad: int
    descripcionEspecialidad: str
