# app/infrastructure/dependencies.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.services.password_service_impl import PasswordServiceImpl
from app.infrastructure.services.auth_service_impl import AuthServiceImpl
from app.application.use_cases.usuario.registrar_usuario import RegistrarUsuarioUseCase
from app.application.use_cases.usuario.login_usuario import LoginUsuarioUseCase
from app.infrastructure.repositories.diagrama_repository_impl import DiagramaRepositoryImpl
from app.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
from app.domain.repositories.project_repository import ProjectRepository
from app.application.services.project_service import ProjectService

# ✅ Inyección de sesión async
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# ✅ Repo requiere db inyectado
async def get_user_repository(
    db: AsyncSession = Depends(get_db)
) -> UserRepositoryImpl:
    return UserRepositoryImpl(db)

def get_password_service() -> PasswordServiceImpl:
    return PasswordServiceImpl()

def get_auth_service() -> AuthServiceImpl:
    return AuthServiceImpl()

# ✅ UseCases usan repo correctamente
async def get_registrar_usuario_use_case(
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
    password_service: PasswordServiceImpl = Depends(get_password_service)
) -> RegistrarUsuarioUseCase:
    return RegistrarUsuarioUseCase(user_repo, password_service)

async def get_login_use_case(
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
    password_service: PasswordServiceImpl = Depends(get_password_service),
    auth_service: AuthServiceImpl = Depends(get_auth_service)
) -> LoginUsuarioUseCase:
    return LoginUsuarioUseCase(user_repo, password_service, auth_service)

async def get_diagrama_repository():
    async with AsyncSessionLocal() as db:
        yield DiagramaRepositoryImpl(db)

async def get_project_service(
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
    diagram_repo: DiagramaRepositoryImpl = Depends(get_diagrama_repository)
) -> ProjectService:
    project_repo = ProjectRepositoryImpl(db)
    return ProjectService(project_repo, user_repo, diagram_repo)
