from typing import List, Dict
from app.domain.repositories.project_repository import ProjectRepository
import logging

class GetProjectMembersUseCase:
    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    async def execute(self, proyecto_id: str) -> Dict:
        """
        Obtiene todos los miembros de un proyecto específico.
        
        Args:
            proyecto_id: ID del proyecto
            
        Returns:
            Dict: Lista de miembros con información detallada
            
        Raises:
            ValueError: Si el proyecto no existe
        """
        if not proyecto_id:
            raise ValueError("ID del proyecto es requerido")

        # Verificar que el proyecto existe
        proyecto = await self.project_repository.get_by_id(proyecto_id)
        if not proyecto:
            raise ValueError(f"El proyecto con ID {proyecto_id} no existe")

        # Obtener los miembros del proyecto
        miembros = await self.project_repository.get_project_members(proyecto_id)
        
        return {
            "proyecto_id": proyecto_id,
            "proyecto_nombre": proyecto.nombre,
            "miembros": miembros,
            "total_miembros": len(miembros)
        }
