# app/domain/repositories/project_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from app.domain.entities.project import Proyecto

class ProjectRepository(ABC):
    @abstractmethod
    def save(self, project: Proyecto) -> None: ...

    @abstractmethod
    def get_by_id(self, project_id: str) -> Optional[Proyecto]: ...

    @abstractmethod
    def list_by_user(self, user_id: str) -> List[Proyecto]: ...
    
    @abstractmethod
    def list_all(self) -> List[Proyecto]: ...

    @abstractmethod
    def update(self, project: Proyecto) -> None: ...

    @abstractmethod
    async def get_projects_by_owner(self, user_id: str) -> List[Proyecto]: ...
    
    @abstractmethod
    async def get_projects_by_membership(self, user_id: str) -> List[Proyecto]: ...

    @abstractmethod
    async def get_accessible_projects(self, user_id: str) -> List[Dict]:
        """
        Obtiene todos los proyectos donde el usuario tiene acceso:
        - Como propietario (user_id en tabla proyectos)
        - Como miembro (usuario_id en tabla miembros_proyecto)
        """
        pass

    @abstractmethod
    async def get_project_members(self, proyecto_id: str) -> List[Dict]:
        """
        Obtiene todos los miembros de un proyecto específico.
        
        Args:
            proyecto_id: ID del proyecto
            
        Returns:
            List[Dict]: Lista de miembros con información del usuario y rol
        """
        pass