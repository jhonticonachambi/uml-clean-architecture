from app.domain.entities.diagram import Diagrama, TipoDiagrama
from app.domain.repositories.diagram_repository import DiagramRepository
from datetime import datetime
from typing import List

class CrearDiagramaUseCase:
    def __init__(self, diagram_repository: DiagramRepository):
        self.diagram_repository = diagram_repository

    async def ejecutar(
        self,
        nombre: str,
        proyecto_id: str,
        creado_por: str,
        tipo_diagrama: str,
        contenido_original: str,
        lenguaje_original: str,
        contenido_plantuml: str = None,  # Agregar este parámetro
        errores: List[str] = None
    ) -> Diagrama:
        """
        Crea y guarda un nuevo diagrama en el repositorio.

        Args:
            nombre: Nombre del diagrama.
            proyecto_id: ID del proyecto al que pertenece el diagrama.
            creado_por: ID del usuario que crea el diagrama.
            tipo_diagrama: Tipo de diagrama (e.g., "class", "sequence").
            contenido_original: Código fuente original del diagrama.
            lenguaje_original: Lenguaje del código fuente.
            errores: Lista de errores encontrados (opcional).

        Returns:
            Diagrama: El diagrama creado y guardado.
        """
        diagrama = Diagrama(
            nombre=nombre,
            proyecto_id=proyecto_id,
            creado_por=creado_por,
            tipo_diagrama=TipoDiagrama(tipo_diagrama),  # Conversión al enumerador
            estado="borrador",
            contenido_original=contenido_original,
            lenguaje_original=lenguaje_original,
            contenido_plantuml=contenido_plantuml,
            errores=errores or [],
            fecha_creacion=datetime.now(),
            fecha_actualizacion=datetime.now()
        )

        # Guardar el diagrama en el repositorio
        db_diagram = await self.diagram_repository.save(diagrama)
        diagrama.id = db_diagram.id  # Asignar el ID generado al objeto Diagrama

        return diagrama
