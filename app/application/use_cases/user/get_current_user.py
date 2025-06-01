# app/application/use_cases/user/get_current_user.py
from typing import Optional
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository

class GetCurrentUserRequest:
    def __init__(self, user_id: str):
        self.user_id = user_id

class GetCurrentUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def execute(self, request: GetCurrentUserRequest) -> Optional[User]:
        """
        Obtiene la información del usuario actual por su ID
        """
        return await self.user_repo.get_by_id(request.user_id)
