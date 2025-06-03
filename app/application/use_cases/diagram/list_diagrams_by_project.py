# app/application/use_cases/diagram/list_diagrams_by_project.py
from typing import List
from app.domain.entities.diagram import Diagrama
from app.domain.repositories.diagram_repository import DiagramRepository

class ListDiagramsByProjectUseCase:
    """Caso de uso para listar todos los diagramas de un proyecto específico."""
    
    def __init__(self, diagram_repository: DiagramRepository):
        self.diagram_repository = diagram_repository
    
    async def ejecutar(self, project_id: str) -> List[Diagrama]:
        """
        Lista todos los diagramas que pertenecen a un proyecto específico.
        
        Args:
            project_id: ID del proyecto del cual listar los diagramas
            
        Returns:
            List[Diagrama]: Lista de diagramas del proyecto
            
        Raises:
            ValueError: Si el project_id está vacío o es inválido
        """
        if not project_id:
            raise ValueError("El ID del proyecto es requerido")
        
        try:
            # Usar el método del repositorio que ya tienes implementado
            diagramas = await self.diagram_repository.list_by_project(project_id)
            return diagramas
            
        except Exception as e:
            # Log del error si es necesario
            print(f"Error al obtener diagramas del proyecto {project_id}: {e}")
            raise ValueError(f"Error al obtener diagramas del proyecto: {str(e)}")
