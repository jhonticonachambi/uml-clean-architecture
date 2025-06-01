# app/domain/entities/diagrama.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Union
from enum import Enum

class TipoDiagrama(Enum):
    """Enum para los tipos de diagramas UML."""
    CLASS = "class"
    SEQUENCE = "sequence"
    ACTIVITY = "activity"
    USE_CASE = "use_case"

@dataclass
class Diagrama:
    nombre: str
    proyecto_id: str
    creado_por: str  # user_id
    tipo_diagrama: TipoDiagrama = TipoDiagrama.CLASS  # Usamos el Enum para el tipo de diagrama
    id: Optional[Union[int, str]] = None  # Permitir None o entero/string para compatibilidad
    estado: str = field(default="borrador")
    contenido_plantuml: Optional[str] = None
    contenido_original: Optional[str] = None
    lenguaje_original: Optional[str] = None
    errores: List[str] = field(default_factory=list)
    fecha_creacion: datetime = field(default_factory=datetime.now)
    fecha_actualizacion: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.validar()

    def validar(self):
        if not self.nombre:
            raise ValueError("Diagrama debe tener nombre")
        if not self.proyecto_id:
            raise ValueError("Diagrama debe pertenecer a un proyecto")
        if not isinstance(self.tipo_diagrama, TipoDiagrama):
            raise ValueError("El tipo de diagrama debe ser un valor válido de TipoDiagrama")

    def marcar_como_validado(self, plantuml: str) -> None:
        if not plantuml:
            raise ValueError("Contenido PlantUML no puede estar vacío")
        self.contenido_plantuml = plantuml
        self.estado = "validado"
        self.errores = []
        self.actualizar_fecha()

    def agregar_error(self, error: str) -> None:
        if not error:
            return
        self.estado = "con_errores"
        self.errores.append(error)
        self.actualizar_fecha()

    def actualizar_fecha(self):
        self.fecha_actualizacion = datetime.now()