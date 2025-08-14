from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class User(BaseModel):
    identificacion: Optional[str]
    nombre1: str
    nombre2: Optional[str]
    apellido1: str
    apellido2: Optional[str]
    tipoDoc: Optional[str]
    phone_number: str
    isActive: bool
    fecha_inicio:  Optional[datetime]
    description: str = Field(
        None,
        description="Descripción adicional del campo isActive"
    )