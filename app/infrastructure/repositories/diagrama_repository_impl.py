# app/infrastructure/repositories/diagrama_repository_impl.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.domain.entities.diagrama import Diagrama
from app.domain.repositories.diagrama_repository import DiagramaRepository
from app.infrastructure.database.models import DiagramaModel
import json

class DiagramaRepositoryImpl(DiagramaRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def guardar(self, diagrama: Diagrama):
        diagrama_model = DiagramaModel(
            id=diagrama.id,
            nombre=diagrama.nombre,
            proyecto_id=diagrama.proyecto_id,
            creado_por=diagrama.creado_por,
            estado=diagrama.estado,
            contenido_plantuml=diagrama.contenido_plantuml,
            contenido_original=diagrama.contenido_original,
            lenguaje_original=diagrama.lenguaje_original,
            errores=json.dumps(diagrama.errores),
            fecha_creacion=diagrama.fecha_creacion,
            fecha_actualizacion=diagrama.fecha_actualizacion
        )
        self.db_session.add(diagrama_model)
        await self.db_session.commit()

    async def obtener_por_id(self, diagrama_id: str) -> Diagrama:
        diagrama_model = await self.db_session.get(DiagramaModel, diagrama_id)
        if not diagrama_model:
            return None
        return Diagrama(
            nombre=diagrama_model.nombre,
            proyecto_id=diagrama_model.proyecto_id,
            creado_por=diagrama_model.creado_por,
            estado=diagrama_model.estado,
            contenido_plantuml=diagrama_model.contenido_plantuml,
            contenido_original=diagrama_model.contenido_original,
            lenguaje_original=diagrama_model.lenguaje_original,
            errores=json.loads(diagrama_model.errores),
            fecha_creacion=diagrama_model.fecha_creacion,
            fecha_actualizacion=diagrama_model.fecha_actualizacion
        )

    async def obtener_por_proyecto(self, proyecto_id: str):
        query = await self.db_session.execute(
            select(DiagramaModel).where(DiagramaModel.proyecto_id == proyecto_id)
        )
        diagramas_model = query.scalars().all()
        return [
            Diagrama(
                nombre=diagrama.nombre,
                proyecto_id=diagrama.proyecto_id,
                creado_por=diagrama.creado_por,
                estado=diagrama.estado,
                contenido_plantuml=diagrama.contenido_plantuml,
                contenido_original=diagrama.contenido_original,
                lenguaje_original=diagrama.lenguaje_original,
                errores=json.loads(diagrama.errores),
                fecha_creacion=diagrama.fecha_creacion,
                fecha_actualizacion=diagrama.fecha_actualizacion
            )
            for diagrama in diagramas_model
        ]
