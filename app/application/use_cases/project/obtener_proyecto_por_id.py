# app/application/use_cases/project/obtener_proyecto_por_id.py
from typing import Optional
from app.domain.entities.project import Proyecto
from app.application.services.project_service import ProjectService

class ObtenerProyectoPorIdRequest:
    def __init__(self, proyecto_id: str):
        self.proyecto_id = proyecto_id

class ObtenerProyectoPorIdUseCase:
    """
    Caso de uso para obtener un proyecto específico por su ID.
    """
    def __init__(self, project_service: ProjectService):
        self.project_service = project_service
    async def ejecutar(self, proyecto_id: str) -> Optional[Proyecto]:
        """
        Obtiene un proyecto específico por su ID.
        
        Args:
            proyecto_id: ID del proyecto a obtener
            
        Returns:
            Optional[Proyecto]: El proyecto si existe, None si no existe.
            
        Raises:
            ValueError: Si el proyecto no existe
        """
        try:
            proyecto = await self.project_service.obtener_proyecto_por_id(proyecto_id)
            return proyecto
        except ValueError as e:
            # Re-lanzar ValueError para que el endpoint maneje el 404
            raise e
        except Exception as e:
            # Registra y propaga otros errores
            print(f"Error al obtener proyecto por ID {proyecto_id}: {e}")
            raise
