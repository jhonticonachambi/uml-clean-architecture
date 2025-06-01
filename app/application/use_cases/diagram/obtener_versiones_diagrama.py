# app/application/use_cases/diagram/obtener_versiones_diagrama.py
from typing import List, Optional
from app.domain.entities.version_diagrama import VersionDiagrama
from app.domain.repositories.version_diagrama_repository import VersionDiagramaRepository
from app.domain.repositories.diagram_repository import DiagramRepository

class ObtenerVersionesDiagramaUseCase:
    """Caso de uso para obtener versiones de un diagrama."""
    
    def __init__(
        self, 
        version_repository: VersionDiagramaRepository,
        diagram_repository: DiagramRepository
    ):
        self.version_repository = version_repository
        self.diagram_repository = diagram_repository
    
    async def obtener_todas_las_versiones(self, diagrama_id: str) -> List[VersionDiagrama]:
        """
        Obtiene todas las versiones de un diagrama ordenadas por número de versión.
        
        Args:
            diagrama_id: ID del diagrama
            
        Returns:
            List[VersionDiagrama]: Lista de versiones ordenadas
            
        Raises:
            ValueError: Si el diagrama no existe
        """
        # Verificar que el diagrama existe
        diagrama = await self.diagram_repository.get_by_id(diagrama_id)
        if not diagrama:
            raise ValueError(f"No se encontró el diagrama con ID: {diagrama_id}")
        
        # Obtener todas las versiones
        versiones = await self.version_repository.list_by_diagrama(diagrama_id)
        
        # Ordenar por número de versión
        return sorted(versiones, key=lambda v: v.numero_version)
    
    async def obtener_version_especifica(
        self, 
        diagrama_id: str, 
        numero_version: int
    ) -> Optional[VersionDiagrama]:
        """
        Obtiene una versión específica de un diagrama.
        
        Args:
            diagrama_id: ID del diagrama
            numero_version: Número de la versión a obtener
            
        Returns:
            VersionDiagrama: La versión solicitada o None si no existe
        """
        return await self.version_repository.get_by_diagrama_and_version(
            diagrama_id, numero_version
        )
    
    async def obtener_version_actual(self, diagrama_id: str) -> Optional[VersionDiagrama]:
        """
        Obtiene la versión actual (más reciente) de un diagrama.
        
        Args:
            diagrama_id: ID del diagrama
            
        Returns:
            VersionDiagrama: La versión actual o None si no existe
        """
        return await self.version_repository.get_latest_version(diagrama_id)
    
    async def obtener_proxima_version_info(self, diagrama_id: str) -> dict:
        """
        Obtiene información sobre la próxima versión a crear.
        
        Args:
            diagrama_id: ID del diagrama
            
        Returns:
            dict: Información de la próxima versión
        """
        diagrama = await self.diagram_repository.get_by_id(diagrama_id)
        if not diagrama:
            raise ValueError(f"No se encontró el diagrama con ID: {diagrama_id}")
        
        version_actual = await self.obtener_version_actual(diagrama_id)
        
        return {
            "diagrama_id": diagrama_id,
            "version_actual": diagrama.version_actual,
            "total_versiones": diagrama.total_versiones,
            "proxima_version": diagrama.obtener_proxima_version(),
            "contenido_actual": version_actual.contenido_original if version_actual else diagrama.contenido_original,
            "lenguaje_actual": version_actual.lenguaje_original if version_actual else diagrama.lenguaje_original
        }
