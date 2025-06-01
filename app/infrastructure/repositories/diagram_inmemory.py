# infrastructure/repositories/diagram_inmemory.py
from app.domain.repositories import DiagramaRepository
from app.domain.entities.diagram import Diagrama
from typing import Optional, List

class DiagramaInMemoryRepository(DiagramaRepository):
    def __init__(self):
        self.db = {}

    def guardar(self, diagrama: Diagrama):
        self.db[diagrama.id] = diagrama

    def obtener_por_id(self, diagrama_id: str) -> Optional[Diagrama]:
        return self.db.get(diagrama_id)

    def obtener_por_proyecto(self, proyecto_id: str) -> List[Diagrama]:
        return [d for d in self.db.values() if d.proyecto_id == proyecto_id]
