# app/infrastructure/repositories/version_diagrama_repository_impl.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from typing import List, Optional
from app.domain.entities.version_diagrama import VersionDiagrama
from app.domain.repositories.version_diagrama_repository import VersionDiagramaRepository
from datetime import datetime
import uuid
import json

class VersionDiagramaRepositoryImpl(VersionDiagramaRepository):
    """Implementación del repositorio de versiones de diagramas usando PostgreSQL."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(self, version: VersionDiagrama) -> None:
        """Guarda una nueva versión de diagrama en la base de datos."""
        query = text("""
            INSERT INTO versiones_diagramas (
                diagrama_id, numero_version, contenido_original, contenido_plantuml,
                lenguaje_original, notas_version, estado, errores, creado_por,
                fecha_creacion, fecha_actualizacion
            ) VALUES (
                :diagrama_id, :numero_version, :contenido_original, :contenido_plantuml,
                :lenguaje_original, :notas_version, :estado, :errores, :creado_por,
                :fecha_creacion, :fecha_actualizacion
            ) RETURNING id
        """)
        
        result = await self.db.execute(query, {
            "diagrama_id": int(version.diagrama_id),
            "numero_version": version.numero_version,
            "contenido_original": version.contenido_original,
            "contenido_plantuml": version.contenido_plantuml,
            "lenguaje_original": version.lenguaje_original,
            "notas_version": version.notas_version,
            "estado": version.estado,
            "errores": json.dumps(version.errores),
            "creado_por": version.creado_por,
            "fecha_creacion": version.fecha_creacion,
            "fecha_actualizacion": version.fecha_actualizacion
        })
        
        # Obtener el ID generado
        version_id = result.fetchone()[0]
        version.id = version_id
        
        await self.db.commit()

    async def get_by_id(self, version_id: str) -> Optional[VersionDiagrama]:
        """Obtiene una versión específica por su ID."""
        query = text("""
            SELECT id, diagrama_id, numero_version, contenido_original, contenido_plantuml,
                   lenguaje_original, notas_version, estado, errores, creado_por,
                   fecha_creacion, fecha_actualizacion
            FROM versiones_diagramas 
            WHERE id = :version_id
        """)
        
        result = await self.db.execute(query, {"version_id": int(version_id)})
        row = result.fetchone()
        
        if not row:
            return None
            
        return self._row_to_version(row)

    async def list_by_diagrama(self, diagrama_id: str) -> List[VersionDiagrama]:
        """Obtiene todas las versiones de un diagrama específico."""
        query = text("""
            SELECT id, diagrama_id, numero_version, contenido_original, contenido_plantuml,
                   lenguaje_original, notas_version, estado, errores, creado_por,
                   fecha_creacion, fecha_actualizacion
            FROM versiones_diagramas 
            WHERE diagrama_id = :diagrama_id
            ORDER BY numero_version ASC
        """)
        
        result = await self.db.execute(query, {"diagrama_id": int(diagrama_id)})
        rows = result.fetchall()
        
        return [self._row_to_version(row) for row in rows]

    async def get_by_diagrama_and_version(self, diagrama_id: str, numero_version: int) -> Optional[VersionDiagrama]:
        """Obtiene una versión específica de un diagrama por número de versión."""
        query = text("""
            SELECT id, diagrama_id, numero_version, contenido_original, contenido_plantuml,
                   lenguaje_original, notas_version, estado, errores, creado_por,
                   fecha_creacion, fecha_actualizacion
            FROM versiones_diagramas 
            WHERE diagrama_id = :diagrama_id AND numero_version = :numero_version
        """)
        
        result = await self.db.execute(query, {
            "diagrama_id": int(diagrama_id),
            "numero_version": numero_version
        })
        row = result.fetchone()
        
        if not row:
            return None
            
        return self._row_to_version(row)

    async def get_latest_version(self, diagrama_id: str) -> Optional[VersionDiagrama]:
        """Obtiene la versión más reciente de un diagrama."""
        query = text("""
            SELECT id, diagrama_id, numero_version, contenido_original, contenido_plantuml,
                   lenguaje_original, notas_version, estado, errores, creado_por,
                   fecha_creacion, fecha_actualizacion
            FROM versiones_diagramas 
            WHERE diagrama_id = :diagrama_id
            ORDER BY numero_version DESC
            LIMIT 1
        """)
        
        result = await self.db.execute(query, {"diagrama_id": int(diagrama_id)})
        row = result.fetchone()
        
        if not row:
            return None
            
        return self._row_to_version(row)

    async def update(self, version: VersionDiagrama) -> None:
        """Actualiza una versión existente."""
        query = text("""
            UPDATE versiones_diagramas 
            SET contenido_original = :contenido_original,
                contenido_plantuml = :contenido_plantuml,
                lenguaje_original = :lenguaje_original,
                notas_version = :notas_version,
                estado = :estado,
                errores = :errores,
                fecha_actualizacion = :fecha_actualizacion
            WHERE id = :id
        """)
        
        await self.db.execute(query, {
            "id": int(version.id),
            "contenido_original": version.contenido_original,
            "contenido_plantuml": version.contenido_plantuml,
            "lenguaje_original": version.lenguaje_original,
            "notas_version": version.notas_version,
            "estado": version.estado,
            "errores": json.dumps(version.errores),
            "fecha_actualizacion": datetime.now()
        })
        
        await self.db.commit()

    async def delete(self, version_id: str) -> None:
        """Elimina una versión específica."""
        query = text("""
            DELETE FROM versiones_diagramas 
            WHERE id = :version_id
        """)
        
        await self.db.execute(query, {"version_id": int(version_id)})
        await self.db.commit()

    def _row_to_version(self, row) -> VersionDiagrama:
        """Convierte una fila de la base de datos a una entidad VersionDiagrama."""
        errores = json.loads(row[8]) if row[8] else []
        
        return VersionDiagrama(
            id=row[0],
            diagrama_id=row[1],
            numero_version=row[2],
            contenido_original=row[3],
            creado_por=row[9],
            contenido_plantuml=row[4],
            lenguaje_original=row[5],
            notas_version=row[6],
            estado=row[7],
            errores=errores,
            fecha_creacion=row[10],
            fecha_actualizacion=row[11]
        )
