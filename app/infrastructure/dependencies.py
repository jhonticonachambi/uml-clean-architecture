# app/infrastructure/dependencies.py

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.services.password_service_impl import PasswordServiceImpl
from app.infrastructure.services.auth_service_impl import AuthServiceImpl
from app.application.use_cases.user.create_user import RegistrarUsuarioUseCase
from app.application.use_cases.auth.login import LoginUsuarioUseCase
from app.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
from app.domain.repositories.project_repository import ProjectRepository
from app.application.services.project_service import ProjectService
from app.infrastructure.repositories.diagram_repository_impl import DiagramRepositoryImpl
from app.domain.repositories.diagram_repository import DiagramRepository
from app.infrastructure.repositories.version_diagrama_repository_impl import VersionDiagramaRepositoryImpl
from app.domain.repositories.version_diagrama_repository import VersionDiagramaRepository
from app.domain.repositories.member_repository import MemberRepository
from app.infrastructure.repositories.member_repository_impl import MemberRepositoryImpl
from app.domain.entities.user import User

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

async def get_diagram_repository(
    db: AsyncSession = Depends(get_db)
) -> DiagramRepository:
    return DiagramRepositoryImpl(db)

async def get_version_diagrama_repository(
    db: AsyncSession = Depends(get_db)
) -> VersionDiagramaRepository:
    """Retorna una instancia del repositorio de versiones de diagramas."""
    return VersionDiagramaRepositoryImpl(db)

async def get_project_repository(
    db: AsyncSession = Depends(get_db)
) -> ProjectRepositoryImpl:
    return ProjectRepositoryImpl(db)

async def get_member_repository(
    db: AsyncSession = Depends(get_db)
) -> MemberRepository:
    return MemberRepositoryImpl(db)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    user_repo: UserRepositoryImpl = Depends(get_user_repository)
) -> User:
    """
    Obtiene el usuario actual desde el token JWT
    """
    auth_service = AuthServiceImpl()
    user_id = auth_service.verify_token(credentials.credentials)
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return user

async def get_project_service(
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
    diagram_repo: DiagramRepository = Depends(get_diagram_repository)
) -> ProjectService:
    project_repo = ProjectRepositoryImpl(db)
    return ProjectService(project_repo, user_repo, diagram_repo)
