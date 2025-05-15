from app.domain.entities.diagrama import Diagrama
from app.domain.repositories.diagrama_repository import DiagramaRepository

class DiagramService:
    def __init__(self, diagrama_repository: DiagramaRepository):
        self.diagrama_repository = diagrama_repository

    async def guardar_diagrama(self, diagrama: Diagrama):
        """Guarda un diagrama en el repositorio."""
        if not diagrama.puede_persistirse():
            raise ValueError("El diagrama no está en un estado válido para ser guardado.")
        await self.diagrama_repository.guardar(diagrama)
