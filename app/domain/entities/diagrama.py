# app/domain/entities/diagrama.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class Diagrama:
    nombre: str
    proyecto_id: str
    creado_por: str  # user_id
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

    def puede_persistirse(self) -> bool:
        return self.estado in ["validado", "persistido"] and bool(self.contenido_plantuml)

    def actualizar_fecha(self):
        self.fecha_actualizacion = datetime.now()