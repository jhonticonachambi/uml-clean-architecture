from app.application.services.project_service import ProjectService
from app.domain.entities.proyecto import MiembroProyecto
from app.domain.entities.base import RolProyecto

class AgregarMiembroUseCase:
    def __init__(self, project_service: ProjectService):
        self.project_service = project_service

    def ejecutar(self, proyecto_id: str, usuario_id: str, rol: RolProyecto) -> MiembroProyecto:
        """Ejecuta el caso de uso para agregar un miembro a un proyecto."""
        return self.project_service.agregar_miembro(proyecto_id, usuario_id, rol)
