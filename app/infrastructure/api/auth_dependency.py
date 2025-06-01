# app/infrastructure/api/auth_dependency.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.infrastructure.services.auth_service_impl import AuthServiceImpl

# Configurar el esquema de seguridad
security = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency para obtener el ID del usuario desde el token JWT
    """
    print(f"[DEBUG] Token recibido: {credentials.credentials[:20]}...")
    
    auth_service = AuthServiceImpl()
    user_id = auth_service.verify_token(credentials.credentials)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    print(f"[DEBUG] User ID extraído: {user_id}")
    return user_id
