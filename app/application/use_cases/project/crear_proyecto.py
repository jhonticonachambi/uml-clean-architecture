from app.application.services.project_service import ProjectService
from app.domain.entities.project import Proyecto

class CrearProyectoUseCase:
    def __init__(self, project_service: ProjectService):
        self.project_service = project_service

    def ejecutar(self, nombre: str, user_id: str) -> Proyecto:
        """Ejecuta el caso de uso para crear un proyecto."""
        return self.project_service.crear_proyecto(nombre, user_id)
