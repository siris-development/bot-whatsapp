from pydantic import BaseModel

class User(BaseModel):
    idUsuario: int
    numDocUsr: str
    nombreCompleto: str
    msgStatus: str
    puedeAgendar: str