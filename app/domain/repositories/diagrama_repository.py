# app/domain/repositories/diagrama_repository.py
from abc import ABC, abstractmethod
from app.domain.entities.diagrama import Diagrama
from typing import Optional, List

class DiagramaRepository(ABC):
    @abstractmethod
    def guardar(self, diagrama: Diagrama):
        """Guarda un diagrama en el repositorio."""
        pass

    @abstractmethod
    def obtener_por_id(self, diagrama_id: str) -> Optional[Diagrama]:
        """Obtiene un diagrama por su ID."""
        pass

    @abstractmethod
    def obtener_por_proyecto(self, proyecto_id: str) -> List[Diagrama]:
        """Obtiene todos los diagramas asociados a un proyecto."""
        pass
