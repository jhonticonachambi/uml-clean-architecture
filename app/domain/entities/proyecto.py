# app/domain/entities/proyecto.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import uuid  # Importación faltante
from .base import RolProyecto
from .diagrama import Diagrama  # Importar la clase Diagrama

@dataclass
class MiembroProyecto:
    usuario_id: str
    proyecto_id: str
    rol: RolProyecto
    fecha_union: datetime = field(default_factory=datetime.now)  # Campo con valor predeterminado al final
    
    def puede_editar(self) -> bool:
        return self.rol in RolProyecto.roles_edicion()

@dataclass
class Proyecto:
    nombre: str
    user_id: str  # Cambiado de propietario_id a user_id
    id: str = field(default_factory=lambda: str(uuid.uuid4()))  # Agregar ID único como cadena
    miembros: List[MiembroProyecto] = field(default_factory=list)
    fecha_creacion: datetime = field(default_factory=datetime.now)
    fecha_actualizacion: datetime = field(default_factory=datetime.now)
    uuid_publico: str = field(default_factory=lambda: str(uuid.uuid4()))  # UUID como cadena
    diagramas: List[Diagrama] = field(default_factory=list)  # Nueva lista para diagramas
    
    def __post_init__(self):
        self.validar()
        # El propietario se añade automáticamente como miembro
        self.agregar_miembro(self.user_id, RolProyecto.PROPIETARIO)
    
    def validar(self):
        if not self.nombre or len(self.nombre.strip()) < 3:
            raise ValueError("Nombre de proyecto inválido")
    
    def agregar_miembro(self, usuario_id: str, rol: RolProyecto) -> MiembroProyecto:
        if any(m.usuario_id == usuario_id for m in self.miembros):
            raise ValueError("Usuario ya es miembro")
        
        nuevo_miembro = MiembroProyecto(
            usuario_id=usuario_id,
            proyecto_id=self.id,
            rol=rol
        )
        self.miembros.append(nuevo_miembro)
        self.actualizar_fecha()
        return nuevo_miembro
    
    def agregar_diagrama(self, diagrama: Diagrama):
        """Agrega un diagrama al proyecto."""
        if diagrama in self.diagramas:
            raise ValueError("El diagrama ya está vinculado a este proyecto")
        self.diagramas.append(diagrama)
        self.actualizar_fecha()

    def eliminar_diagrama(self, diagrama: Diagrama):
        """Elimina un diagrama del proyecto."""
        if diagrama not in self.diagramas:
            raise ValueError("El diagrama no está vinculado a este proyecto")
        self.diagramas.remove(diagrama)
        self.actualizar_fecha()

    def actualizar_fecha(self):
        self.fecha_actualizacion = datetime.now()