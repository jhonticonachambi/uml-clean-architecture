# app/domain/entities/proyecto.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import uuid  # Importación faltante
from .base import RolProyecto
from .diagram import Diagrama  # Importar la clase Diagrama

@dataclass
class MiembroProyecto:
    usuario_id: str
    proyecto_id: str
    rol: RolProyecto
    fecha_union: datetime = field(default_factory=datetime.now)
    
    def puede_editar(self) -> bool:
        return self.rol in RolProyecto.roles_edicion()
    
    def puede_eliminar(self) -> bool:
        """Solo el propietario puede eliminar un proyecto"""
        return self.rol == RolProyecto.PROPIETARIO

@dataclass
class Proyecto:
    nombre: str
    user_id: str  # Cambiado de propietario_id a user_id
    id: str = field(default_factory=lambda: str(uuid.uuid4()))  # Agregar ID único como cadena
    fecha_creacion: datetime = field(default_factory=datetime.now)
    fecha_actualizacion: datetime = field(default_factory=datetime.now)
    uuid_publico: str = field(default_factory=lambda: str(uuid.uuid4()))  # UUID como cadena
    # descripcion: str = ""  # Restaurar descripción

    def __post_init__(self):
        self.validar()
        # El propietario se añade automáticamente como miembro
        # self.agregar_miembro(self.user_id, RolProyecto.PROPIETARIO)
    
    def validar(self):
        if not self.nombre or len(self.nombre.strip()) < 3:
            raise ValueError("Nombre de proyecto inválido")
    
    def es_propietario(self, usuario_id: str) -> bool:
        return self.user_id == usuario_id

    def actualizar_fecha(self):
        self.fecha_actualizacion = datetime.now()

    @staticmethod
    def from_orm(orm_model):
        return Proyecto(
            nombre=orm_model.nombre,
            user_id=str(orm_model.user_id),
            id=str(orm_model.id),
            fecha_creacion=orm_model.fecha_creacion,
            fecha_actualizacion=orm_model.fecha_actualizacion,
            uuid_publico=str(orm_model.uuid_publico)
        )