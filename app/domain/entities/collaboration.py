# app/domain/entities/collaboration.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid  # Importación necesaria añadida
from .base import Entidad, RolProyecto

@dataclass
class InvitacionProyecto(Entidad):
    proyecto_id: str
    email_invitado: str
    rol_asignado: RolProyecto
    token: str = field(default_factory=lambda: str(uuid.uuid4()))
    fecha_invitacion: datetime = field(default_factory=datetime.now)
    fecha_aceptacion: Optional[datetime] = None
    estado: str = "pendiente"  # 'pendiente', 'aceptada', 'rechazada'
    
    def aceptar(self) -> None:
        if self.estado != "pendiente":
            raise ValueError("Invitación ya fue procesada")
        self.estado = "aceptada"
        self.fecha_aceptacion = datetime.now()
    
    def es_valida(self) -> bool:
        return self.estado == "pendiente" and bool(self.token)