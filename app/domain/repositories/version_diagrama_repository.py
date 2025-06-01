# app/domain/repositories/version_diagrama_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.version_diagrama import VersionDiagrama

class VersionDiagramaRepository(ABC):
    """Repositorio abstracto para gestionar las versiones de diagramas."""
    
    @abstractmethod
    async def save(self, version: VersionDiagrama) -> None:
        """Guarda una nueva versión de diagrama."""
        ...

    @abstractmethod
    async def get_by_id(self, version_id: str) -> Optional[VersionDiagrama]:
        """Obtiene una versión específica por su ID."""
        ...

    @abstractmethod
    async def list_by_diagrama(self, diagrama_id: str) -> List[VersionDiagrama]:
        """Obtiene todas las versiones de un diagrama específico."""
        ...
    
    @abstractmethod
    async def get_by_diagrama_and_version(self, diagrama_id: str, numero_version: int) -> Optional[VersionDiagrama]:
        """Obtiene una versión específica de un diagrama por número de versión."""
        ...
    
    @abstractmethod
    async def get_latest_version(self, diagrama_id: str) -> Optional[VersionDiagrama]:
        """Obtiene la versión más reciente de un diagrama."""
        ...
    
    @abstractmethod
    async def update(self, version: VersionDiagrama) -> None:
        """Actualiza una versión existente."""
        ...
    
    @abstractmethod
    async def delete(self, version_id: str) -> None:
        """Elimina una versión específica."""
        ...
