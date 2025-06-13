# app/infrastructure/api/routes/version_diagrama.py
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List, Optional
from pydantic import BaseModel
from app.application.use_cases.diagram.crear_version_diagrama import CrearVersionDiagramaUseCase
from app.application.use_cases.diagram.obtener_versiones_diagrama import ObtenerVersionesDiagramaUseCase
from app.domain.repositories.version_diagrama_repository import VersionDiagramaRepository
from app.domain.repositories.diagram_repository import DiagramRepository
from app.infrastructure.dependencies import get_version_diagrama_repository, get_diagram_repository

router = APIRouter(prefix="/diagramas", tags=["versiones-diagramas"])

class CrearVersionRequest(BaseModel):
    contenido_original: str
    notas_version: str = ""
    lenguaje_original: Optional[str] = None
    contenido_plantuml: Optional[str] = None
    creado_por: str

class VersionDiagramaResponse(BaseModel):
    id: str
    diagrama_id: str
    numero_version: int
    contenido_original: str
    contenido_plantuml: Optional[str]
    lenguaje_original: Optional[str]
    notas_version: str
    estado: str
    errores: List[str]
    creado_por: str
    fecha_creacion: str
    fecha_actualizacion: str

class ProximaVersionInfoResponse(BaseModel):
    diagrama_id: str
    version_actual: int
    total_versiones: int
    proxima_version: int
    contenido_actual: Optional[str]
    lenguaje_actual: Optional[str]

async def get_crear_version_use_case(
    version_repo: VersionDiagramaRepository = Depends(get_version_diagrama_repository),
    diagram_repo: DiagramRepository = Depends(get_diagram_repository)
) -> CrearVersionDiagramaUseCase:
    return CrearVersionDiagramaUseCase(version_repo, diagram_repo)

async def get_obtener_versiones_use_case(
    version_repo: VersionDiagramaRepository = Depends(get_version_diagrama_repository),
    diagram_repo: DiagramRepository = Depends(get_diagram_repository)
) -> ObtenerVersionesDiagramaUseCase:
    return ObtenerVersionesDiagramaUseCase(version_repo, diagram_repo)

@router.post("/{diagrama_id}/versiones", summary="Crea una nueva versión de un diagrama")
async def crear_nueva_version(
    diagrama_id: str,
    request: CrearVersionRequest = Body(...),
    crear_version_use_case: CrearVersionDiagramaUseCase = Depends(get_crear_version_use_case),
):
    """Crea una nueva versión de un diagrama existente."""
    try:
        version = await crear_version_use_case.ejecutar(
            diagrama_id=diagrama_id,
            contenido_original=request.contenido_original,
            creado_por=request.creado_por,
            notas_version=request.notas_version,
            lenguaje_original=request.lenguaje_original,
            contenido_plantuml=request.contenido_plantuml
        )
        
        return VersionDiagramaResponse(
            id=str(version.id),
            diagrama_id=str(version.diagrama_id),
            numero_version=version.numero_version,
            contenido_original=version.contenido_original,
            contenido_plantuml=version.contenido_plantuml,
            lenguaje_original=version.lenguaje_original,
            notas_version=version.notas_version,
            estado=version.estado,
            errores=version.errores,
            creado_por=version.creado_por,
            fecha_creacion=version.fecha_creacion.isoformat(),
            fecha_actualizacion=version.fecha_actualizacion.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear la versión: {str(e)}")

@router.get("/{diagrama_id}/versiones", summary="Obtiene todas las versiones de un diagrama")
async def obtener_versiones(
    diagrama_id: str,
    obtener_versiones_use_case: ObtenerVersionesDiagramaUseCase = Depends(get_obtener_versiones_use_case),
):
    """Obtiene todas las versiones de un diagrama específico."""
    try:
        versiones = await obtener_versiones_use_case.obtener_todas_las_versiones(diagrama_id)
        
        return [
            VersionDiagramaResponse(
                id=str(version.id),
                diagrama_id=str(version.diagrama_id),
                numero_version=version.numero_version,
                contenido_original=version.contenido_original,
                contenido_plantuml=version.contenido_plantuml,
                lenguaje_original=version.lenguaje_original,
                notas_version=version.notas_version,
                estado=version.estado,
                errores=version.errores,
                creado_por=version.creado_por,
                fecha_creacion=version.fecha_creacion.isoformat(),
                fecha_actualizacion=version.fecha_actualizacion.isoformat()
            )
            for version in versiones
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener versiones: {str(e)}")

@router.get("/{diagrama_id}/versiones/{numero_version}", summary="Obtiene una versión específica")
async def obtener_version_especifica(
    diagrama_id: str,
    numero_version: int,
    obtener_versiones_use_case: ObtenerVersionesDiagramaUseCase = Depends(get_obtener_versiones_use_case),
):
    """Obtiene una versión específica de un diagrama."""
    try:
        version = await obtener_versiones_use_case.obtener_version_especifica(diagrama_id, numero_version)
        
        if not version:
            raise HTTPException(status_code=404, detail=f"Versión {numero_version} no encontrada")
        
        return VersionDiagramaResponse(
            id=str(version.id),
            diagrama_id=str(version.diagrama_id),
            numero_version=version.numero_version,
            contenido_original=version.contenido_original,
            contenido_plantuml=version.contenido_plantuml,
            lenguaje_original=version.lenguaje_original,
            notas_version=version.notas_version,
            estado=version.estado,
            errores=version.errores,
            creado_por=version.creado_por,
            fecha_creacion=version.fecha_creacion.isoformat(),
            fecha_actualizacion=version.fecha_actualizacion.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener la versión: {str(e)}")

@router.get("/{diagrama_id}/proxima-version", summary="Obtiene información de la próxima versión")
async def obtener_info_proxima_version(
    diagrama_id: str,
    obtener_versiones_use_case: ObtenerVersionesDiagramaUseCase = Depends(get_obtener_versiones_use_case),
):
    """Obtiene información sobre la próxima versión a crear. Útil para el modal de edición."""
    try:
        info = await obtener_versiones_use_case.obtener_proxima_version_info(diagrama_id)
        
        return ProximaVersionInfoResponse(
            diagrama_id=info["diagrama_id"],
            version_actual=info["version_actual"],
            total_versiones=info["total_versiones"],
            proxima_version=info["proxima_version"],
            contenido_actual=info["contenido_actual"],
            lenguaje_actual=info["lenguaje_actual"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener información: {str(e)}")
