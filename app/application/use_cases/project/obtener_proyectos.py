# app/use_cases/proyecto/obtener_proyectos.py
from typing import List
from app.domain.entities.project import Proyecto
from app.application.services.project_service import ProjectService

class ObtenerProyectosUseCase:
    """
    Caso de uso para obtener todos los proyectos.
    """
    def __init__(self, project_service: ProjectService):
        self.project_service = project_service
    async def ejecutar(self) -> List[Proyecto]:
            """
            Obtiene todos los proyectos en el sistema.
            
            Returns:
                List[Proyecto]: Lista de todos los proyectos.
            """
            try:
                # Llama al método del servicio
                return await self.project_service.obtener_todos_proyectos()
            except Exception as e:
                # Registra y propaga el error
                print(f"Error al obtener proyectos: {e}")
                raise
