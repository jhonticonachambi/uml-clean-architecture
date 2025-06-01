# app/domain/repositories/diagram_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.diagram import Diagrama

class DiagramRepository(ABC):
    @abstractmethod
    def save(self, diagram: Diagrama) -> None: ...

    @abstractmethod
    def get_by_id(self, diagram_id: str) -> Optional[Diagrama]: ...

    @abstractmethod
    def list_by_project(self, project_id: str) -> List[Diagrama]: ...

    @abstractmethod
    def update(self, diagram: Diagrama) -> None: ...