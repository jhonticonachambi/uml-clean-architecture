# app/api/routes/diagram.py
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List, Optional
from pydantic import BaseModel
from app.application.use_cases.diagram.generate_diagram import GenerarDiagramaDesdeCodigoUseCase
from app.application.use_cases.diagram.create_diagram import CrearDiagramaUseCase
from app.application.use_cases.diagram.edit_diagram import EditarDiagramaUseCase
from app.application.use_cases.diagram.list_diagrams_by_project import ListDiagramsByProjectUseCase
from app.domain.entities.diagram import Diagrama, TipoDiagrama
from app.domain.repositories.diagram_repository import DiagramRepository
from app.infrastructure.dependencies import get_diagram_repository

router = APIRouter(prefix="/diagramas", tags=["diagramas"])  # Cambiado a /api/diagramas

class DiagramaRequest(BaseModel):
    codigo: str
    lenguaje: str = "csharp"
    diagramas: List[str] = ["clases"]  # Cambiado a "clases" para coincidir con el Enum
    proyecto_id: str  # Agregado para incluir el ID del proyecto

class CrearDiagramaRequest(BaseModel):
    nombre: str
    proyecto_id: str
    creado_por: str
    tipo_diagrama: str
    contenido_original: str
    lenguaje_original: str
    contenido_plantuml: str 
    errores: List[str] = None

class EditarDiagramaRequest(BaseModel):
    nombre: Optional[str] = None
    tipo_diagrama: Optional[str] = None
    contenido_original: Optional[str] = None
    lenguaje_original: Optional[str] = None
    contenido_plantuml: Optional[str] = None
    errores: Optional[List[str]] = None
    estado: Optional[str] = None

@router.post("/generar", summary="Genera diagramas UML desde código fuente")
async def generar_diagrama(
    request: DiagramaRequest = Body(...),  # Solo Body, no Query params
):
    try:
        # Instancia del caso de uso
        use_case = GenerarDiagramaDesdeCodigoUseCase()

        # Ejecutar el caso de uso
        resultados = use_case.ejecutar(
            codigo_fuente=request.codigo,
            lenguaje=request.lenguaje,
            diagramas_solicitados=request.diagramas,
            proyecto_id=request.proyecto_id
        )

        # Convertir los resultados en un formato adecuado para la respuesta
        data = [
            {
                "nombre": diagrama.nombre,
                "tipo_diagrama": diagrama.tipo_diagrama.value,  # Convertir Enum a string
                "estado": diagrama.estado,
                "contenido_plantuml": diagrama.contenido_plantuml,
                "errores": diagrama.errores,
                "fecha_creacion": diagrama.fecha_creacion,
                "fecha_actualizacion": diagrama.fecha_actualizacion
            }
            for diagrama in resultados
        ]

        return {
            "success": True,
            "data": data,
            "meta": {
                "lenguaje": request.lenguaje,
                "diagramas_generados": [diagrama.nombre for diagrama in resultados]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def get_crear_diagrama_use_case(
    diagram_repository: DiagramRepository = Depends(get_diagram_repository)
) -> CrearDiagramaUseCase:
    return CrearDiagramaUseCase(diagram_repository)

async def get_list_diagrams_by_project_use_case(
    diagram_repository: DiagramRepository = Depends(get_diagram_repository)
) -> ListDiagramsByProjectUseCase:
    return ListDiagramsByProjectUseCase(diagram_repository)

@router.post("/crear", summary="Crea un nuevo diagrama UML")
async def crear_diagrama(
    request: CrearDiagramaRequest = Body(...),
    crear_diagrama_use_case: CrearDiagramaUseCase = Depends(get_crear_diagrama_use_case),
):
    try:
        diagrama = await crear_diagrama_use_case.ejecutar(
            nombre=request.nombre,
            proyecto_id=request.proyecto_id,
            creado_por=request.creado_por,
            tipo_diagrama=request.tipo_diagrama,
            contenido_original=request.contenido_original,
            contenido_plantuml=request.contenido_plantuml,  # Agregar esta línea
            lenguaje_original=request.lenguaje_original,
            errores=request.errores,
        )
        return {
            "id": str(diagrama.id),  # Convertir a string para asegurar serialización JSON
            "nombre": diagrama.nombre,
            "tipo_diagrama": diagrama.tipo_diagrama.value,  # Usamos .value para obtener el string
            "fecha_creacion": diagrama.fecha_creacion
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", summary="Obtiene todos los diagramas")
async def obtener_todos_los_diagramas(
    diagram_repository: DiagramRepository = Depends(get_diagram_repository)
):
    """Endpoint para obtener todos los diagramas disponibles."""
    try:
        diagramas = await diagram_repository.list_all()
        return [
            {
                "id": str(diagrama.id),
                "nombre": diagrama.nombre,
                "tipo_diagrama": diagrama.tipo_diagrama.value,
                "fecha_creacion": diagrama.fecha_creacion,
                "fecha_actualizacion": diagrama.fecha_actualizacion
            }
            for diagrama in diagramas
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener diagramas: {str(e)}")

@router.get("/proyecto/{project_id}", summary="Obtiene todos los diagramas de un proyecto")
async def obtener_diagramas_por_proyecto(
    project_id: str,
    list_diagrams_use_case: ListDiagramsByProjectUseCase = Depends(get_list_diagrams_by_project_use_case)
):
    """Endpoint para obtener todos los diagramas de un proyecto específico."""
    try:
        diagramas = await list_diagrams_use_case.ejecutar(project_id)
        
        return [
            {
                "id": str(diagrama.id),
                "nombre": diagrama.nombre,
                "proyecto_id": diagrama.proyecto_id,
                "creado_por": diagrama.creado_por,
                "tipo_diagrama": diagrama.tipo_diagrama.value,
                "estado": diagrama.estado,
                "contenido_plantuml": diagrama.contenido_plantuml,
                "contenido_original": diagrama.contenido_original,
                "lenguaje_original": diagrama.lenguaje_original,
                "errores": diagrama.errores,
                "version_actual": diagrama.version_actual,
                "total_versiones": diagrama.total_versiones,
                "fecha_creacion": diagrama.fecha_creacion,
                "fecha_actualizacion": diagrama.fecha_actualizacion
            }
            for diagrama in diagramas
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener diagramas del proyecto: {str(e)}")

@router.get("/{diagrama_id}", summary="Obtiene un diagrama por ID")
async def obtener_diagrama_por_id(
    diagrama_id: str,
    diagram_repository: DiagramRepository = Depends(get_diagram_repository)
):
    """Endpoint para obtener un diagrama específico por su ID."""
    try:
        diagrama = await diagram_repository.get_by_id(diagrama_id)
        if not diagrama:
            raise HTTPException(status_code=404, detail="Diagrama no encontrado")
        return {
            "id": str(diagrama.id),
            "nombre": diagrama.nombre,
            "tipo_diagrama": diagrama.tipo_diagrama.value,
            "contenido_plantuml": diagrama.contenido_plantuml,
            "contenido_original": diagrama.contenido_original,
            "lenguaje_original": diagrama.lenguaje_original,
            "estado": diagrama.estado,  
            "fecha_creacion": diagrama.fecha_creacion,
            "fecha_actualizacion": diagrama.fecha_actualizacion
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el diagrama: {str(e)}")

async def get_editar_diagrama_use_case(
    diagram_repository: DiagramRepository = Depends(get_diagram_repository)
) -> EditarDiagramaUseCase:
    return EditarDiagramaUseCase(diagram_repository)

@router.put("/{diagrama_id}", summary="Edita un diagrama existente")
async def editar_diagrama(
    diagrama_id: str,
    request: EditarDiagramaRequest = Body(...),
    editar_diagrama_use_case: EditarDiagramaUseCase = Depends(get_editar_diagrama_use_case),
):
    """Endpoint para editar un diagrama específico por su ID."""
    try:
        diagrama = await editar_diagrama_use_case.ejecutar(
            diagrama_id=diagrama_id,
            nombre=request.nombre,
            tipo_diagrama=request.tipo_diagrama,
            contenido_original=request.contenido_original,
            lenguaje_original=request.lenguaje_original,
            contenido_plantuml=request.contenido_plantuml,
            errores=request.errores,
            estado=request.estado
        )
        return {
            "id": str(diagrama.id),
            "nombre": diagrama.nombre,
            "tipo_diagrama": diagrama.tipo_diagrama.value,
            "contenido_plantuml": diagrama.contenido_plantuml,
            "contenido_original": diagrama.contenido_original,
            "lenguaje_original": diagrama.lenguaje_original,
            "estado": diagrama.estado,
            "errores": diagrama.errores,
            "fecha_creacion": diagrama.fecha_creacion,
            "fecha_actualizacion": diagrama.fecha_actualizacion
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al editar el diagrama: {str(e)}")