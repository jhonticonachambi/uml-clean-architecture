# app/domain/entities/version_diagrama.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Union

@dataclass
class VersionDiagrama:
    """Entidad que representa una versión específica de un diagrama."""
    diagrama_id: Union[int, str]  # ID del diagrama padre
    numero_version: int
    contenido_original: str
    creado_por: str
    notas_version: str = ""  # Descripción de los cambios en esta versión
    id: Optional[Union[int, str]] = None
    contenido_plantuml: Optional[str] = None
    lenguaje_original: Optional[str] = None
    errores: List[str] = field(default_factory=list)
    estado: str = field(default="borrador")  # borrador, validado, con_errores
    fecha_creacion: datetime = field(default_factory=datetime.now)
    fecha_actualizacion: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        self.validar()

    def validar(self):
        if not self.diagrama_id:
            raise ValueError("VersionDiagrama debe tener un diagrama_id válido")
        if not self.contenido_original:
            raise ValueError("VersionDiagrama debe tener contenido_original")
        if self.numero_version < 1:
            raise ValueError("El número de versión debe ser mayor a 0")
        if not self.creado_por:
            raise ValueError("VersionDiagrama debe tener un creador")

    def marcar_como_validado(self, plantuml: str) -> None:
        """Marca la versión como validada con el contenido PlantUML generado."""
        if not plantuml:
            raise ValueError("Contenido PlantUML no puede estar vacío")
        self.contenido_plantuml = plantuml
        self.estado = "validado"
        self.errores = []
        self.actualizar_fecha()

    def agregar_error(self, error: str) -> None:
        """Agrega un error a la versión y cambia el estado."""
        if not error:
            return
        self.estado = "con_errores"
        self.errores.append(error)
        self.actualizar_fecha()

    def actualizar_fecha(self):
        """Actualiza la fecha de última modificación."""
        self.fecha_actualizacion = datetime.now()
    
    def actualizar_contenido(self, nuevo_contenido: str, notas: str = "") -> None:
        """Actualiza el contenido de la versión."""
        if not nuevo_contenido:
            raise ValueError("El nuevo contenido no puede estar vacío")
        
        self.contenido_original = nuevo_contenido
        if notas:
            self.notas_version = notas
        self.estado = "borrador"  # Reset estado al modificar contenido
        self.actualizar_fecha()