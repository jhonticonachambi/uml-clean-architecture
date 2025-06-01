from app.domain.entities.project import Proyecto, MiembroProyecto
from app.domain.entities.diagram import Diagrama
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.repositories.diagram_repository import DiagramRepository
from app.domain.entities.base import RolProyecto
from typing import List, Optional

class ProjectService:
    def __init__(self, project_repo: ProjectRepository, user_repo: UserRepository, diagram_repo: DiagramRepository = None):
        self.project_repo = project_repo
        self.user_repo = user_repo
        self.diagram_repo = diagram_repo

    async def crear_proyecto(self, nombre: str, user_id: str) -> Proyecto:  # Cambiado propietario_id a user_id
        """Crea un nuevo proyecto y lo guarda en el repositorio."""
        try:
            propietario = await self.user_repo.obtener_usuario_por_id(user_id)  # Cambiado propietario_id a user_id
            if not propietario:
                raise ValueError("El usuario no existe")

            proyecto = Proyecto(nombre=nombre, user_id=user_id)  # Cambiado propietario_id a user_id
            await self.project_repo.save(proyecto)  # Usar save en lugar de guardar_proyecto
            return proyecto
        except Exception as e:
            print(f"Error al crear el proyecto: {e}")  # Log del error
            raise

    def agregar_miembro(self, proyecto_id: str, usuario_id: str, rol: RolProyecto) -> MiembroProyecto:
        """Agrega un miembro a un proyecto existente."""
        proyecto = self.project_repo.obtener_proyecto_por_id(proyecto_id)
        if not proyecto:
            raise ValueError("El proyecto no existe")

        usuario = self.user_repo.obtener_usuario_por_id(usuario_id)
        if not usuario:
            raise ValueError("El usuario no existe")

        miembro = proyecto.agregar_miembro(usuario_id, rol)
        self.project_repo.guardar_proyecto(proyecto)
        return miembro

    def vincular_diagrama(self, proyecto_id: str, diagrama_id: str):
        """Vincula un diagrama a un proyecto."""
        proyecto = self.project_repo.obtener_proyecto_por_id(proyecto_id)
        if not proyecto:
            raise ValueError("El proyecto no existe")

        diagrama = self.diagram_repo.obtener_diagrama_por_id(diagrama_id)
        if not diagrama:
            raise ValueError("El diagrama no existe")

        proyecto.agregar_diagrama(diagrama)
        self.project_repo.guardar_proyecto(proyecto)

    def desvincular_diagrama(self, proyecto_id: str, diagrama_id: str):
        """Desvincula un diagrama de un proyecto."""
        proyecto = self.project_repo.obtener_proyecto_por_id(proyecto_id)
        if not proyecto:
            raise ValueError("El proyecto no existe")

        diagrama = self.diagram_repo.obtener_diagrama_por_id(diagrama_id)
        if not diagrama:
            raise ValueError("El diagrama no existe")

        proyecto.eliminar_diagrama(diagrama)
        self.project_repo.guardar_proyecto(proyecto)
         
    async def obtener_proyecto_por_id(self, proyecto_id: str) -> Proyecto:
        """Obtiene un proyecto por su ID."""
        proyecto = await self.project_repo.get_by_id(proyecto_id)
        if not proyecto:
            raise ValueError("El proyecto no existe")
        return proyecto
        
    async def obtener_todos_proyectos(self) -> List[Proyecto]:
        """Obtiene todos los proyectos."""
        try:
            return await self.project_repo.list_all()
        except Exception as e:
            print(f"Error al obtener todos los proyectos: {e}")
            raise
