# app/domain/repositories/project_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.proyecto import Proyecto

class ProjectRepository(ABC):
    @abstractmethod
    def save(self, project: Proyecto) -> None: ...

    @abstractmethod
    def get_by_id(self, project_id: str) -> Optional[Proyecto]: ...

    @abstractmethod
    def list_by_user(self, user_id: str) -> List[Proyecto]: ...
    
    @abstractmethod
    def list_all(self) -> List[Proyecto]: ...