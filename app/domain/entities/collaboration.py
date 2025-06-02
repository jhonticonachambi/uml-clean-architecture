# app/domain/entities/collaboration.py
from dataclasses import dataclass, field
from datetime import datetime
from .base import RolProyecto

@dataclass
class ColaboracionProyecto:
    proyecto_id: str
    usuario_id: str
    rol: RolProyecto
    activo: bool = True
    fecha_union: datetime = field(default_factory=datetime.now)

    def puede_editar(self) -> bool:
        return self.rol in RolProyecto.roles_edicion() and self.activo

    def puede_ver(self) -> bool:
        return self.activo

    def puede_administrar(self) -> bool:
        return self.rol == RolProyecto.PROPIETARIO and self.activo