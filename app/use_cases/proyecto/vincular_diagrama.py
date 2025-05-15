from app.application.services.project_service import ProjectService

class VincularDiagramaUseCase:
    def __init__(self, project_service: ProjectService):
        self.project_service = project_service

    def ejecutar(self, proyecto_id: str, diagrama_id: str):
        """Ejecuta el caso de uso para vincular un diagrama a un proyecto."""
        self.project_service.vincular_diagrama(proyecto_id, diagrama_id)
