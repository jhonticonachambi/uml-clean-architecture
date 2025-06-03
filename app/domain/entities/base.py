# app/domain/entities/base.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional, List, Dict, Set
import uuid

class EstadoDiagrama(str, Enum):
    BORRADOR = "borrador"
    VALIDADO = "validado"
    PERSISTIDO = "persistido"
    CON_ERRORES = "con_errores"
    
    @classmethod
    def estados_persistibles(cls):
        return [cls.VALIDADO, cls.PERSISTIDO]

class RolProyecto(str, Enum):
    PROPIETARIO = "propietario"
    EDITOR = "editor"
    VISUALIZADOR = "visualizador"
    
    @classmethod
    def roles_edicion(cls):
        """Devuelve los roles que pueden editar un proyecto"""
        return [cls.PROPIETARIO, cls.EDITOR]
    
    @classmethod
    def puede_agregar_miembros(cls, rol):
        """Verifica si un rol puede agregar miembros"""
        return rol == cls.PROPIETARIO

@dataclass
class Entidad:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fecha_creacion: datetime = field(default_factory=datetime.now)
    fecha_actualizacion: datetime = field(default_factory=datetime.now)
