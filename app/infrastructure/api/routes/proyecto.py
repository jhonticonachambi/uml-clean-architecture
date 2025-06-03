from fastapi import APIRouter, HTTPException, Depends, Query
from app.application.services.project_service import ProjectService
from app.application.use_cases.project.crear_proyecto import CrearProyectoUseCase
from app.application.use_cases.project.obtener_proyectos import ObtenerProyectosUseCase
from app.application.use_cases.project.obtener_proyecto_por_id import ObtenerProyectoPorIdUseCase, ObtenerProyectoPorIdRequest
from app.application.use_cases.project.get_my_owned_projects import GetMyOwnedProjectsUseCase
from app.application.use_cases.project.get_accessible_projects import GetAccessibleProjectsUseCase
from app.application.use_cases.project.get_project_members import GetProjectMembersUseCase
from app.domain.entities.base import RolProyecto
from app.infrastructure.dependencies import get_project_service, get_user_repository, get_project_repository, get_member_repository, get_current_user
from pydantic import BaseModel
from app.application.use_cases.project.add_project_member import AgregarMiembroUseCase
from app.domain.entities.base import RolProyecto
from datetime import datetime
from typing import List
from app.domain.entities.user import User
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.member_repository import MemberRepository
from uuid import UUID
import logging


router = APIRouter(prefix="/proyectos", tags=["Proyectos"])

class CrearProyectoRequest(BaseModel):
    nombre: str
    user_id: str

# Modelo Pydantic para la solicitud
class AgregarMiembroRequest(BaseModel):
    usuario_id: str
    rol: str  # Debe ser uno de los valores definidos en RolProyecto

# Modelo Pydantic para la respuesta
class MiembroResponse(BaseModel):
    usuario_id: str
    proyecto_id: str
    rol: str
    fecha_union: datetime

# Modelo Pydantic para la respuesta del proyecto completo
class ProyectoResponse(BaseModel):
    id: str
    nombre: str
    user_id: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    uuid_publico: str

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

@router.get("/my-owned", summary="Obtiene proyectos donde soy propietario")
async def get_my_owned_projects(
    user_id: str,
    project_repository: ProjectRepository = Depends(get_project_repository)
):
    """
    Endpoint para obtener los proyectos donde el usuario especificado es el propietario.
    """
    logging.debug(f"[DEBUG] Valor recibido para user_id en el endpoint: {user_id}")
    try:
        # Validar que el user_id es un UUID válido
        user_uuid = UUID(user_id)
        logging.debug(f"[DEBUG] UUID convertido para user_id en el endpoint: {user_uuid}")
    except ValueError:
        logging.error(f"[ERROR] El user_id proporcionado no es un UUID válido: {user_id}")
        raise HTTPException(status_code=400, detail="El user_id proporcionado no es un UUID válido.")

    use_case = GetMyOwnedProjectsUseCase(project_repository)
    proyectos = await use_case.execute(str(user_uuid))
    logging.debug(f"[DEBUG] Proyectos obtenidos en el endpoint: {proyectos}")
    return {"proyectos": proyectos, "total": len(proyectos)}

@router.get("/accessible", summary="Obtiene todos los proyectos donde tengo acceso")
async def get_accessible_projects(
    user_id: str = Query(..., description="ID del usuario"),
    project_repository: ProjectRepository = Depends(get_project_repository)
):
    """
    Endpoint para obtener todos los proyectos a los que el usuario tiene acceso:
    - Como propietario (user_id en tabla proyectos)
    - Como miembro (usuario_id en tabla miembros_proyecto)
    """
    try:
        use_case = GetAccessibleProjectsUseCase(project_repository)
        result = await use_case.execute(user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
@router.post("/{proyecto_id}/miembros", summary="Agrega un miembro al proyecto")
async def agregar_miembro(
    proyecto_id: str, 
    request: AgregarMiembroRequest, 
    current_user_id: str = "usuario_actual",  # Aquí deberías usar tu sistema de autenticación
    project_service: ProjectService = Depends(get_project_service),
    user_repository = Depends(get_user_repository)  # Necesitas agregar esta dependencia
):
    """
    Endpoint para agregar un miembro a un proyecto existente.
    
    - **proyecto_id**: ID del proyecto al que se agregará el miembro
    - **usuario_id**: ID del usuario que será añadido como miembro
    - **rol**: Rol que tendrá el usuario ('propietario', 'editor', 'visualizador')
    
    Retorna los datos del nuevo miembro agregado.
    """
    print(f"[INFO] Iniciando agregar miembro a proyecto {proyecto_id}")
    
    use_case = AgregarMiembroUseCase(project_service.project_repo, user_repository)
    
    try:
        # Llamar al caso de uso
        miembro = await use_case.execute(
            proyecto_id=proyecto_id,
            usuario_id=request.usuario_id,
            rol=request.rol,
            usuario_solicitante_id=current_user_id
        )
        
        print(f"[INFO] Miembro agregado exitosamente: {miembro}")
        
        # Convertir la entidad a un modelo de respuesta
        response = MiembroResponse(
            usuario_id=miembro.usuario_id,
            proyecto_id=miembro.proyecto_id,
            rol=miembro.rol.value,
            fecha_union=miembro.fecha_union
        )
        
        return response
        
    except ValueError as e:
        print(f"[ERROR] Error de validación: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        print(f"[ERROR] Error de permisos: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/{proyecto_id}", summary="Obtiene los detalles de un proyecto por su ID")
async def obtener_proyecto_por_id(
    proyecto_id: str, 
    project_service: ProjectService = Depends(get_project_service)
):
    """
    Endpoint para obtener los detalles de un proyecto específico.
    
    - **proyecto_id**: ID del proyecto a obtener
    
    Retorna los detalles del proyecto solicitado.
    """
    print(f"[INFO] Obteniendo detalles del proyecto {proyecto_id}")
    
    use_case = ObtenerProyectoPorIdUseCase(project_service)
    
    try:
        print(f"[DEBUG] Iniciando caso de uso ObtenerProyectoPorIdUseCase con ID: {proyecto_id}")
        proyecto = await use_case.ejecutar(proyecto_id)
        print(f"[DEBUG] Resultado del caso de uso: {proyecto}")

        if not proyecto:
            print(f"[WARN] Proyecto con ID {proyecto_id} no encontrado")
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        print(f"[INFO] Proyecto obtenido exitosamente: {proyecto}")

        response = ProyectoResponse(
            id=proyecto.id,
            nombre=proyecto.nombre,
            user_id=proyecto.user_id,
            fecha_creacion=proyecto.fecha_creacion,
            fecha_actualizacion=proyecto.fecha_actualizacion,
            uuid_publico=proyecto.uuid_publico
        )

        print(f"[DEBUG] Respuesta generada: {response}")
        return response

    except ValueError as e:
        print(f"[ERROR] Error de validación: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/{proyecto_id}/miembros", summary="Obtiene los miembros de un proyecto")
async def get_project_members(
    proyecto_id: str,
    project_repository: ProjectRepository = Depends(get_project_repository)
):
    """
    Endpoint para obtener todos los miembros de un proyecto específico.
    
    - **proyecto_id**: ID del proyecto del cual obtener los miembros
    
    Retorna la lista de miembros del proyecto con información del usuario y permisos.
    """
    try:
        use_case = GetProjectMembersUseCase(project_repository)
        result = await use_case.execute(proyecto_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
