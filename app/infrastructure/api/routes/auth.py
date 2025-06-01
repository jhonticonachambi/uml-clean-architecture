# infrastructure/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.application.use_cases.auth.login import LoginUsuarioUseCase, LoginUsuarioRequest
from app.application.use_cases.user.get_current_user import GetCurrentUserUseCase, GetCurrentUserRequest
from app.infrastructure.dependencies import (
    get_login_use_case,
    get_user_repository
)
from app.infrastructure.services.auth_service_impl import AuthServiceImpl

router = APIRouter(tags=["Autenticación"])

# ✅ Configurar seguridad Bearer
security = HTTPBearer()

class UserResponse(BaseModel):
    id: str
    email: str
    nombre: str
    activo: bool

class LoginResponse(BaseModel):
    access_token: str
    user: dict

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency para obtener el ID del usuario desde el token JWT
    """
    auth_service = AuthServiceImpl()
    user_id = auth_service.verify_token(credentials.credentials)
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user_id

# 🚀 Ruta para el login
@router.post("/login", response_model=LoginResponse)
async def login(
    email: str,
    password: str,
    use_case: LoginUsuarioUseCase = Depends(get_login_use_case)
):
    result = await use_case.execute(LoginUsuarioRequest(email, password))  # ✅ FIX
    if not result:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return result

@router.get("/users/me", response_model=UserResponse)
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
