# app/infrastructure/repositories/diagram_repository_impl.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
import uuid  # Importar módulo uuid
from app.domain.entities.diagram import Diagrama
from app.domain.repositories.diagram_repository import DiagramRepository
from app.infrastructure.database.models import DiagramModel

class DiagramRepositoryImpl(DiagramRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, diagram: Diagrama) -> DiagramModel:
        # Convertir strings a UUID para proyecto_id y creado_por
        try:
            proyecto_id = uuid.UUID(diagram.proyecto_id) if isinstance(diagram.proyecto_id, str) else diagram.proyecto_id
        except ValueError:
            # Si no es un UUID válido, crear uno
            proyecto_id = uuid.uuid4()
            
        try:
            creado_por = uuid.UUID(diagram.creado_por) if isinstance(diagram.creado_por, str) else diagram.creado_por
        except ValueError:
            # Si no es un UUID válido, crear uno
            creado_por = uuid.uuid4()
        
        # Si el id es None, omitirlo para que la base de datos lo genere automáticamente
        diagram_data = {
            "nombre": diagram.nombre,
            "proyecto_id": proyecto_id,  # UUID convertido
            "creado_por": creado_por,    # UUID convertido
            "tipo_diagrama": diagram.tipo_diagrama.value,
            "estado": diagram.estado,
            "contenido_plantuml": diagram.contenido_plantuml,
            "contenido_original": diagram.contenido_original,
            "lenguaje_original": diagram.lenguaje_original,
            "errores": diagram.errores,
            "fecha_creacion": diagram.fecha_creacion,
            "fecha_actualizacion": diagram.fecha_actualizacion
        }
        
        # Crear nuevo modelo de diagrama
        db_diagram = DiagramModel(**diagram_data)
        
        # Guardar en la base de datos
        self.db.add(db_diagram)
        await self.db.commit()
        await self.db.refresh(db_diagram)
        
        # Asignar ID generado al objeto de dominio
        diagram.id = db_diagram.id
        
        return db_diagram

    async def get_by_id(self, diagram_id: str) -> Optional[Diagrama]:
        try:
            # Convertir diagram_id a entero si es una cadena
            diagram_id = int(diagram_id)
        except ValueError:
            raise ValueError("El ID del diagrama debe ser un entero válido")

        # Implementación para obtener un diagrama por su ID
        result = await self.db.execute(select(DiagramModel).filter_by(id=diagram_id))
        db_diagram = result.scalar_one_or_none()

        if not db_diagram:
            return None

        return self._map_to_entity(db_diagram)

    async def list_by_project(self, project_id: str) -> List[Diagrama]:
        # Convertir project_id a UUID si es un string
        try:
            project_uuid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
        except ValueError:
            # Si no es un UUID válido, devolver lista vacía
            return []
            
        # Implementación para listar diagramas por proyecto
        result = await self.db.execute(select(DiagramModel).filter_by(proyecto_id=project_uuid))
        db_diagrams = result.scalars().all()
        
        return [self._map_to_entity(db_diagram) for db_diagram in db_diagrams]
    
    async def list_all(self) -> List[Diagrama]:
        # Obtener todos los diagramas de la base de datos
        result = await self.db.execute(select(DiagramModel))
        db_diagrams = result.scalars().all()

        # Mapear los resultados a entidades de dominio
        return [self._map_to_entity(db_diagram) for db_diagram in db_diagrams]
        
    async def update(self, diagram: Diagrama) -> DiagramModel:
        # Convertir diagram_id a entero si es una cadena
        try:
            diagram_id = int(diagram.id)
        except (ValueError, TypeError):
            raise ValueError("El ID del diagrama debe ser un entero válido")

        # Buscar el diagrama existente
        result = await self.db.execute(select(DiagramModel).filter_by(id=diagram_id))
        db_diagram = result.scalar_one_or_none()
        
        if not db_diagram:
            raise ValueError(f"Diagrama con ID {diagram_id} no encontrado")

        # Convertir strings a UUID para proyecto_id y creado_por si es necesario
        try:
            proyecto_id = uuid.UUID(diagram.proyecto_id) if isinstance(diagram.proyecto_id, str) else diagram.proyecto_id
        except ValueError:
            proyecto_id = db_diagram.proyecto_id  # Mantener el valor existente
            
        try:
            creado_por = uuid.UUID(diagram.creado_por) if isinstance(diagram.creado_por, str) else diagram.creado_por
        except ValueError:
            creado_por = db_diagram.creado_por  # Mantener el valor existente        # Actualizar los campos del diagrama
        db_diagram.nombre = diagram.nombre
        db_diagram.proyecto_id = proyecto_id
        db_diagram.creado_por = creado_por
        db_diagram.tipo_diagrama = diagram.tipo_diagrama.value
        db_diagram.estado = diagram.estado
        db_diagram.contenido_plantuml = diagram.contenido_plantuml
        db_diagram.contenido_original = diagram.contenido_original
        db_diagram.lenguaje_original = diagram.lenguaje_original
        db_diagram.errores = diagram.errores
        db_diagram.fecha_actualizacion = diagram.fecha_actualizacion
        
        # Actualizar campos de versionado
        if hasattr(db_diagram, 'version_actual'):
            db_diagram.version_actual = diagram.version_actual
        if hasattr(db_diagram, 'total_versiones'):
            db_diagram.total_versiones = diagram.total_versiones

        # Guardar los cambios en la base de datos
        await self.db.commit()
        await self.db.refresh(db_diagram)        # Actualizar el objeto de dominio con cualquier cambio de la base de datos
        diagram.fecha_actualizacion = db_diagram.fecha_actualizacion

        return db_diagram

    def _map_to_entity(self, db_diagram: DiagramModel) -> Diagrama:
        # Mapear desde el modelo de base de datos a la entidad de dominio
        from app.domain.entities.diagram import TipoDiagrama
        
        return Diagrama(
            id=db_diagram.id,
            nombre=db_diagram.nombre,
            proyecto_id=str(db_diagram.proyecto_id),  # Convertir UUID a string
            creado_por=str(db_diagram.creado_por),    # Convertir UUID a string
            tipo_diagrama=TipoDiagrama(db_diagram.tipo_diagrama),
            estado=db_diagram.estado,
            contenido_plantuml=db_diagram.contenido_plantuml,
            contenido_original=db_diagram.contenido_original,
            lenguaje_original=db_diagram.lenguaje_original,
            errores=db_diagram.errores,
            fecha_creacion=db_diagram.fecha_creacion,
            fecha_actualizacion=db_diagram.fecha_actualizacion,            version_actual=getattr(db_diagram, 'version_actual', 1),
            total_versiones=getattr(db_diagram, 'total_versiones', 1)
        )