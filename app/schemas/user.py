from pydantic import BaseModel

class StatusValid(BaseModel):
    isActive: bool
    message: str

class User(BaseModel):
    idUsuario: int
    nombreCompleto: str
    statusValid: StatusValid