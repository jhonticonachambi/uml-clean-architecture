from app.domain.repositories.project_repository import ProjectRepository
from app.domain.entities.proyecto import Proyecto
from typing import Optional, List
from sqlalchemy.future import select
from app.infrastructure.database.models import ProyectoModel
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import logging

class ProjectRepositoryImpl(ProjectRepository):
    def __init__(self, db):
        self.db = db

    def guardar_proyecto(self, proyecto: Proyecto) -> None:
        """Guarda un proyecto en la base de datos."""
        # Aquí se debe implementar la lógica para guardar el proyecto en la base de datos.
        # Por ejemplo, convertir el objeto `Proyecto` a un modelo de base de datos y guardarlo.
        print(f"[DEBUG] Guardando proyecto: {proyecto}")
        # Simulación de guardado (reemplazar con lógica real)
        pass

    async def save(self, project: Proyecto) -> None:
        """Guarda un proyecto en la base de datos."""
        try:
            # Convertir los UUID de cadenas a objetos UUID
            import uuid
            proyecto_id = uuid.UUID(project.id) if isinstance(project.id, str) else project.id
            user_id = uuid.UUID(project.user_id) if isinstance(project.user_id, str) else project.user_id
            uuid_publico = uuid.UUID(project.uuid_publico) if isinstance(project.uuid_publico, str) else project.uuid_publico
            
            proyecto_model = ProyectoModel(
                id=proyecto_id,
                nombre=project.nombre,
                user_id=user_id,
                fecha_creacion=project.fecha_creacion,
                fecha_actualizacion=project.fecha_actualizacion,
                uuid_publico=uuid_publico
            )
            self.db.add(proyecto_model)
            await self.db.commit()
            await self.db.refresh(proyecto_model)
        except IntegrityError as e:
            logging.error(f"Error de integridad al guardar el proyecto: {str(e)}")
            await self.db.rollback()
            raise ValueError(f"Error de integridad: {str(e)}")
        except SQLAlchemyError as e:
            logging.error(f"Error al guardar el proyecto: {str(e)}")
            await self.db.rollback()
            raise ValueError(f"Error al guardar el proyecto: {str(e)}")

    async def get_by_id(self, project_id: str) -> Optional[Proyecto]:
        """Obtiene un proyecto por su ID."""
        query = await self.db.execute(select(ProyectoModel).filter_by(id=project_id))
        proyecto_model = query.scalar_one_or_none()
        if not proyecto_model:
            return None
        return Proyecto(
            id=proyecto_model.id,
            nombre=proyecto_model.nombre,
            user_id=proyecto_model.user_id,
            fecha_creacion=proyecto_model.fecha_creacion,
            fecha_actualizacion=proyecto_model.fecha_actualizacion
        )    
    async def list_by_user(self, user_id: str) -> List[Proyecto]:
        """Obtiene todos los proyectos de un usuario específico."""
        try:
            query = await self.db.execute(select(ProyectoModel).filter_by(user_id=user_id))
            proyecto_models = query.scalars().all()
            return [Proyecto(
                id=modelo.id,
                nombre=modelo.nombre,
                user_id=modelo.user_id,
                fecha_creacion=modelo.fecha_creacion,
                fecha_actualizacion=modelo.fecha_actualizacion,
                uuid_publico=modelo.uuid_publico
            ) for modelo in proyecto_models]
        except SQLAlchemyError as e:
            logging.error(f"Error al listar proyectos por usuario: {str(e)}")
            raise ValueError(f"Error al listar proyectos: {str(e)}")
            
    async def list_all(self) -> List[Proyecto]:
        """Obtiene todos los proyectos."""
        try:
            query = await self.db.execute(select(ProyectoModel))
            proyecto_models = query.scalars().all()
            return [Proyecto(
                id=modelo.id,
                nombre=modelo.nombre,
                user_id=modelo.user_id,
                fecha_creacion=modelo.fecha_creacion,
                fecha_actualizacion=modelo.fecha_actualizacion,
                uuid_publico=modelo.uuid_publico
            ) for modelo in proyecto_models]
        except SQLAlchemyError as e:
            logging.error(f"Error al listar todos los proyectos: {str(e)}")
            raise ValueError(f"Error al listar todos los proyectos: {str(e)}")
