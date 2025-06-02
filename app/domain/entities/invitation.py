from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid
from .base import RolProyecto

@dataclass
class InvitacionProyecto:
    proyecto_id: str
    email_invitado: str
    rol_asignado: RolProyecto
    invitado_por: str
    token: str = field(default_factory=lambda: str(uuid.uuid4()))
    fecha_invitacion: datetime = field(default_factory=datetime.now)
    fecha_aceptacion: Optional[datetime] = None
    estado: str = "pendiente"

    def aceptar(self) -> None:
        if self.estado != "pendiente":
            raise ValueError("Invitación ya fue procesada")
        self.estado = "aceptada"
        self.fecha_aceptacion = datetime.now()

    def rechazar(self) -> None:
        if self.estado != "pendiente":
            raise ValueError("Invitación ya fue procesada")
        self.estado = "rechazada"

    def es_valida(self) -> bool:
        return self.estado == "pendiente" and bool(self.token)
