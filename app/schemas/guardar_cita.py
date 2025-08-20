from pydantic import BaseModel, field_validator
import re

class GuardarCita(BaseModel):
    idUsuario: int
    idSede: int
    idProfesional: int
    idEspecialidad: int
    fecha: str
    hora: str
    idResolucion: int

    @field_validator('hora')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        # opcional: normaliza a MAYÚSCULAS y quita espacios
        v_norm = v.strip().upper()
        # 12h con AM/PM, horas 1–12 con/ sin cero inicial
        pattern = r'^(0?[1-9]|1[0-2]):[0-5][0-9](AM|PM)$'
        if not re.fullmatch(pattern, v_norm):
            raise ValueError('El formato debe ser HH:MMAM o HH:MMPM, ej: 11:00AM')
        return v_norm  # o `return v` si quieres preservar el original
