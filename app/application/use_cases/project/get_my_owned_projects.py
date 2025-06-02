from typing import List
from ....domain.repositories.project_repository import ProjectRepository
from ....domain.entities.project import Proyecto

class GetMyOwnedProjectsUseCase:
    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    async def execute(self, user_id: str) -> List[Proyecto]:
        if not user_id:
            raise ValueError("User ID es requerido")
        return await self.project_repository.get_projects_by_owner(user_id)
