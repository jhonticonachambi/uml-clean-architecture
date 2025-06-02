# infrastructure/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from app.application.use_cases.user.create_user import RegistrarUsuarioUseCase, RegistrarUsuarioRequest
from app.application.use_cases.user.get_current_user import GetCurrentUserUseCase, GetCurrentUserRequest
from app.infrastructure.dependencies import (
    get_registrar_usuario_use_case,
    get_user_repository
)
from app.domain.services.auth_service import AuthService
from app.infrastructure.services.auth_service_impl import AuthServiceImpl
from typing import Optional

router = APIRouter(tags=["Usuarios"])

# ✅ Mejor práctica: usar Pydantic model
class RegistrarUsuarioBody(BaseModel):
    email: str
    nombre: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    nombre: str
    activo: bool

# ✅ Función auxiliar para obtener usuario desde token
def get_current_user_id(authorization: Optional[str] = Header(None, alias="Authorization")) -> str:
    """
    Extrae el ID del usuario del token de autorización
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Token de autorización requerido")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de token inválido. Use: Bearer <token>")
    
    token = authorization.split(" ")[1]
    auth_service = AuthServiceImpl()
    user_id = auth_service.verify_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
    return user_id

@router.post("/register")
async def registrar_usuario(
    body: RegistrarUsuarioBody,
    use_case: RegistrarUsuarioUseCase = Depends(get_registrar_usuario_use_case)
):
    try:
        usuario = await use_case.execute(
            RegistrarUsuarioRequest(body.email, body.nombre, body.password)
        )
        return {
            "id": str(usuario.id),  # ✅ Convertir UUID a string para JSON
            "email": usuario.email,
            "nombre": usuario.nombre
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: str = Depends(get_current_user_id),
    user_repo = Depends(get_user_repository)
):
    """
    Obtiene la información del usuario autenticado
    """
    try:
        use_case = GetCurrentUserUseCase(user_repo)
        usuario = await use_case.execute(GetCurrentUserRequest(current_user_id))
        
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return UserResponse(
            id=str(usuario.id),
            email=usuario.email,
            nombre=usuario.nombre,
            activo=usuario.activo
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/buscar", response_model=UserResponse, summary="Buscar usuario por email")
async def buscar_usuario_por_email(
    email: str = Query(..., description="Email del usuario a buscar"),
    user_repo = Depends(get_user_repository)
):
    """
    Busca un usuario por su email.
    
    - **email**: Email del usuario a buscar
    
    Útil para verificar si un usuario existe antes de invitarlo a un proyecto.
    """
    try:
        usuario = await user_repo.get_by_email(email)
        
        if not usuario:
            raise HTTPException(
                status_code=404, 
                detail=f"No se encontró usuario con email: {email}"
            )
        
        if not usuario.activo:
            raise HTTPException(
                status_code=400,
                detail="El usuario está inactivo"
            )
        
        return UserResponse(
            id=str(usuario.id),
            email=usuario.email,
            nombre=usuario.nombre,
            activo=usuario.activo
        )
    except HTTPException:
        # Re-raise HTTPExceptions to preserve status codes
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")