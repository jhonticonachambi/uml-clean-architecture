from fastapi import APIRouter, HTTPException, Depends
from app.application.services.project_service import ProjectService
from app.use_cases.proyecto.crear_proyecto import CrearProyectoUseCase
from app.use_cases.proyecto.agregar_miembro import AgregarMiembroUseCase
from app.use_cases.proyecto.vincular_diagrama import VincularDiagramaUseCase
from app.use_cases.proyecto.desvincular_diagrama import DesvincularDiagramaUseCase
from app.use_cases.proyecto.obtener_proyectos import ObtenerProyectosUseCase
from app.domain.entities.base import RolProyecto
from app.infrastructure.dependencies import get_project_service
from pydantic import BaseModel

router = APIRouter(prefix="/proyectos", tags=["Proyectos"])

class CrearProyectoRequest(BaseModel):
    nombre: str
    user_id: str

@router.post("/crear")
async def crear_proyecto(request: CrearProyectoRequest, project_service: ProjectService = Depends(get_project_service)):
    print("[INFO] Iniciando creación de proyecto")  # Log inicial
    use_case = CrearProyectoUseCase(project_service)
    try:
        print(f"[INFO] Ejecutando caso de uso con nombre={request.nombre}, user_id={request.user_id}")  # Log de parámetros
        proyecto = await use_case.ejecutar(request.nombre, request.user_id)  # Cambiado a await
        print(f"[INFO] Proyecto creado exitosamente: {proyecto}")  # Log de éxito
        return {"mensaje": "Proyecto creado exitosamente", "proyecto": proyecto}
    except ValueError as e:
        print(f"[ERROR] Error de validación: {e}")  # Log de error de validación
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")  # Log de error inesperado
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/{proyecto_id}/miembros/agregar")
def agregar_miembro(proyecto_id: str, usuario_id: str, rol: RolProyecto, project_service: ProjectService = Depends(get_project_service)):
    use_case = AgregarMiembroUseCase(project_service)
    try:
        miembro = use_case.ejecutar(proyecto_id, usuario_id, rol)
        return {"mensaje": "Miembro agregado exitosamente", "miembro": miembro}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{proyecto_id}/diagramas/vincular")
def vincular_diagrama(proyecto_id: str, diagrama_id: str, project_service: ProjectService = Depends(get_project_service)):
    use_case = VincularDiagramaUseCase(project_service)
    try:
        use_case.ejecutar(proyecto_id, diagrama_id)
        return {"mensaje": "Diagrama vinculado exitosamente"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{proyecto_id}/diagramas/desvincular")
def desvincular_diagrama(proyecto_id: str, diagrama_id: str, project_service: ProjectService = Depends(get_project_service)):
    use_case = DesvincularDiagramaUseCase(project_service)
    try:
        use_case.ejecutar(proyecto_id, diagrama_id)
        return {"mensaje": "Diagrama desvinculado exitosamente"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", summary="Obtiene todos los proyectos")
async def obtener_proyectos(project_service: ProjectService = Depends(get_project_service)):
    """
    Endpoint para obtener todos los proyectos existentes
    """
    use_case = ObtenerProyectosUseCase(project_service)
    try:
        proyectos = await use_case.ejecutar()
        return {"proyectos": proyectos}
    except Exception as e:
        print(f"[ERROR] Error al obtener proyectos: {e}")  # Log de error inesperado
        raise HTTPException(status_code=500, detail=f"Error al obtener proyectos: {str(e)}")

@router.get("/health", summary="Verifica el estado del servidor")
async def health_check():
    return {"status": "ok"}
