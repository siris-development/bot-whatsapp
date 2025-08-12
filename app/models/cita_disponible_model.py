from pydantic import BaseModel

class CitaDisponible(BaseModel):
    idSede: int
    idProfesional: int
    idEspecialidad: int
    idDia: int
    profesional: str
    especialidad: str
    dia: str
    horaInicio: str
    horaFin: str
    turnosDisponibles: str