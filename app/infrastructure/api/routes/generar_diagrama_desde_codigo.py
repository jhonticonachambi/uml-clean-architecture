# app/api/routes/generar_diagrama_desde_codigo.py
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List
from pydantic import BaseModel
from app.application.use_cases.generar_codigo import GenerarDiagramaDesdeCodigoUseCase
from app.application.use_cases.guardar_diagrama import GuardarDiagramaUseCase
from app.infrastructure.dependencies import get_diagrama_repository, get_db
from app.domain.entities.diagrama import Diagrama
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/diagramas", tags=["diagramas"])  # Cambiado a /api/diagramas

class DiagramaRequest(BaseModel):
    codigo: str
    lenguaje: str = "csharp"
    diagramas: List[str] = ["class"]
    proyecto_id: str  # Agregado para incluir el ID del proyecto

@router.post("/generar", summary="Genera diagramas UML desde código fuente")
async def generar_diagrama(
    request: DiagramaRequest = Body(...),  # Solo Body, no Query params
):
    try:
        use_case = GenerarDiagramaDesdeCodigoUseCase()
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

@router.post("/guardar", summary="Guarda un diagrama generado")
async def guardar_diagrama(
    diagrama: DiagramaRequest = Body(...),
    repository=Depends(get_diagrama_repository)
):
    try:
        guardar_use_case = GuardarDiagramaUseCase(repository)
        diagrama_entidad = Diagrama(
            nombre=diagrama.codigo,  # Ajustar según los datos reales
            proyecto_id=diagrama.proyecto_id,  # Placeholder
            creado_por="usuario_demo",  # Placeholder
            contenido_plantuml=diagrama.codigo  # Placeholder
        )
        resultado = guardar_use_case.ejecutar(diagrama_entidad)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))