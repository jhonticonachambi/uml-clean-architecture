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
    LECTOR = "lector"
    COLABORADOR = "colaborador"
    ADMINISTRADOR = "administrador"
    PROPIETARIO = "propietario"
    
    @classmethod
    def roles_edicion(cls):
        return [cls.ADMINISTRADOR, cls.COLABORADOR, cls.PROPIETARIO]

@dataclass
class Entidad:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fecha_creacion: datetime = field(default_factory=datetime.now)
    fecha_actualizacion: datetime = field(default_factory=datetime.now)
