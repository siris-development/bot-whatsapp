from pydantic import BaseModel

class Sede(BaseModel):
    idSede: int
    nomSede: str