#application/use_cases/auth/login.py
from datetime import datetime
from typing import Optional, Dict, Any
from app.domain.repositories.user_repository import UserRepository
from app.domain.entities.user import User
from app.domain.services.password_service import PasswordService
from app.domain.services.auth_service import AuthService

class LoginUsuarioRequest:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = str(password)

class LoginUsuarioUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_service: PasswordService,
        auth_service: AuthService    ):
        self.user_repo = user_repository
        self.password_service = password_service
        self.auth_service = auth_service

    async def execute(self, request: LoginUsuarioRequest) -> Optional[Dict[str, Any]]:
        usuario = await self.user_repo.get_by_email(request.email)  # ✅ await

        if not usuario:
            return None

        if not self.password_service.verify_password(
            request.password, usuario.password_hash
        ):
            return None

        await self.user_repo.update_last_access(usuario.id, datetime.now())  # ✅ await
        token = self.auth_service.generate_token(usuario.id)
        
        return {
            "access_token": token,
            "user": {
                "id": str(usuario.id),
                "email": usuario.email,
                "nombre": usuario.nombre
            }
        }
