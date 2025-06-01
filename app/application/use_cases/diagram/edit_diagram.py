# app/application/use_cases/diagram/edit_diagram.py
from app.domain.entities.diagram import Diagrama, TipoDiagrama
from app.domain.repositories.diagram_repository import DiagramRepository
from datetime import datetime
from typing import List, Optional

class EditarDiagramaUseCase:
    def __init__(self, diagram_repository: DiagramRepository):
        self.diagram_repository = diagram_repository

    async def ejecutar(
        self,
        diagrama_id: str,
        nombre: Optional[str] = None,
        tipo_diagrama: Optional[str] = None,
        contenido_original: Optional[str] = None,
        lenguaje_original: Optional[str] = None,
        contenido_plantuml: Optional[str] = None,
        errores: Optional[List[str]] = None,
        estado: Optional[str] = None
    ) -> Diagrama:
        """
        Edita un diagrama existente en el repositorio.

        Args:
            diagrama_id: ID del diagrama a editar.
            nombre: Nuevo nombre del diagrama (opcional).
            tipo_diagrama: Nuevo tipo de diagrama (opcional).
            contenido_original: Nuevo código fuente original (opcional).
            lenguaje_original: Nuevo lenguaje del código fuente (opcional).
            contenido_plantuml: Nuevo contenido PlantUML (opcional).
            errores: Nueva lista de errores (opcional).
            estado: Nuevo estado del diagrama (opcional).

        Returns:
            Diagrama: El diagrama editado y actualizado.
            
        Raises:
            ValueError: Si el diagrama no existe o los datos son inválidos.
        """
        # Obtener el diagrama existente
        diagrama_existente = await self.diagram_repository.get_by_id(diagrama_id)
        if not diagrama_existente:
            raise ValueError(f"Diagrama con ID {diagrama_id} no encontrado")

        # Actualizar solo los campos proporcionados
        if nombre is not None:
            diagrama_existente.nombre = nombre
            
        if tipo_diagrama is not None:
            try:
                diagrama_existente.tipo_diagrama = TipoDiagrama(tipo_diagrama)
            except ValueError:
                raise ValueError(f"Tipo de diagrama inválido: {tipo_diagrama}")
                
        if contenido_original is not None:
            diagrama_existente.contenido_original = contenido_original
            
        if lenguaje_original is not None:
            diagrama_existente.lenguaje_original = lenguaje_original
            
        if contenido_plantuml is not None:
            diagrama_existente.contenido_plantuml = contenido_plantuml
            
        if errores is not None:
            diagrama_existente.errores = errores
            
        if estado is not None:
            diagrama_existente.estado = estado

        # Actualizar la fecha de modificación
        diagrama_existente.actualizar_fecha()

        # Guardar los cambios en el repositorio
        await self.diagram_repository.update(diagrama_existente)

        return diagrama_existente
