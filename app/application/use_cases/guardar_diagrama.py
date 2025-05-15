# app/application/use_cases/guardar_diagrama.py
from app.domain.entities.diagrama import Diagrama
from app.domain.repositories.diagrama_repository import DiagramaRepository

class GuardarDiagramaUseCase:
    def __init__(self, repository: DiagramaRepository):
        self.repository = repository

    def ejecutar(self, diagrama: Diagrama):
        if not diagrama.puede_persistirse():
            raise ValueError("El diagrama no está en un estado válido para ser guardado.")

        self.repository.guardar(diagrama)
        return {
            "success": True,
            "message": f"Diagrama '{diagrama.nombre}' guardado exitosamente."
        }
