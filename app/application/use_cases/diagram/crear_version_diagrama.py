# app/application/use_cases/diagram/crear_version_diagrama.py
from typing import Optional
from app.domain.entities.version_diagrama import VersionDiagrama
from app.domain.entities.diagram import Diagrama
from app.domain.repositories.version_diagrama_repository import VersionDiagramaRepository
from app.domain.repositories.diagram_repository import DiagramRepository

class CrearVersionDiagramaUseCase:
    """Caso de uso para crear una nueva versión de un diagrama."""
    
    def __init__(
        self, 
        version_repository: VersionDiagramaRepository,
        diagram_repository: DiagramRepository
    ):
        self.version_repository = version_repository
        self.diagram_repository = diagram_repository
    
    async def ejecutar(
        self,
        diagrama_id: str,
        contenido_original: str,
        creado_por: str,
        notas_version: str = "",
        lenguaje_original: Optional[str] = None,
        contenido_plantuml: Optional[str] = None
    ) -> VersionDiagrama:
        """
        Crea una nueva versión de un diagrama existente.
        
        Args:
            diagrama_id: ID del diagrama padre
            contenido_original: Contenido de código de la nueva versión
            creado_por: ID del usuario que crea la versión
            notas_version: Descripción de los cambios
            lenguaje_original: Lenguaje del código fuente
            contenido_plantuml: Contenido PlantUML opcional
            
        Returns:
            VersionDiagrama: La nueva versión creada
            
        Raises:
            ValueError: Si el diagrama no existe o los datos son inválidos
        """
        # 1. Verificar que el diagrama existe
        diagrama = await self.diagram_repository.get_by_id(diagrama_id)
        if not diagrama:
            raise ValueError(f"No se encontró el diagrama con ID: {diagrama_id}")
        
        # 2. Incrementar el contador de versiones y obtener el nuevo número
        numero_version = diagrama.incrementar_version()
        
        # 3. Crear la nueva versión
        nueva_version = VersionDiagrama(
            diagrama_id=diagrama_id,
            numero_version=numero_version,
            contenido_original=contenido_original,
            creado_por=creado_por,
            notas_version=notas_version,
            lenguaje_original=lenguaje_original or diagrama.lenguaje_original,
            contenido_plantuml=contenido_plantuml
        )
        
        # 4. Guardar la nueva versión
        await self.version_repository.save(nueva_version)
        
        # 5. Actualizar el diagrama padre con el nuevo contador de versiones
        await self.diagram_repository.update(diagrama)
        
        return nueva_version
