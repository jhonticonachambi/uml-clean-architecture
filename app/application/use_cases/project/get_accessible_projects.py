from typing import List, Dict
from ....domain.repositories.project_repository import ProjectRepository

class GetAccessibleProjectsUseCase:
    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    async def execute(self, user_id: str) -> Dict:
        """
        Obtiene todos los proyectos donde el usuario tiene acceso:
        - Como propietario (user_id en tabla proyectos)
        - Como miembro (usuario_id en tabla miembros_proyecto)
        """
        if not user_id:
            raise ValueError("User ID es requerido")

        # Buscar en ambas tablas usando una sola consulta
        proyectos_accesibles = await self.project_repository.get_accessible_projects(user_id)
        
        return {
            "proyectos": proyectos_accesibles,
            "total": len(proyectos_accesibles)
        }
