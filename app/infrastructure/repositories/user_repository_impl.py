# app/infrastructure/repositories/user_repository_impl.py
from typing import Optional, List
from datetime import datetime
from app.domain.entities.usuario import Usuario
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.models import UserModel  
# from app.infrastructure.database.session import SessionLocal

from app.infrastructure.database.session import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

class UserRepositoryImpl(UserRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, usuario: Usuario) -> Usuario:
        db_user = UserModel(
            id=usuario.id,
            email=usuario.email,
            nombre=usuario.nombre,
            password_hash=usuario.password_hash
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return usuario

    async def get_by_id(self, user_id: str) -> Optional[Usuario]:
        result = await self.db.execute(select(UserModel).filter_by(id=user_id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return Usuario(
            id=db_user.id,
            email=db_user.email,
            nombre=db_user.nombre,
            password_hash=db_user.password_hash
        )

    async def get_by_email(self, email: str) -> Optional[Usuario]:
        result = await self.db.execute(select(UserModel).filter_by(email=email))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return Usuario(
            id=db_user.id,
            email=db_user.email,
            nombre=db_user.nombre,
            password_hash=db_user.password_hash,
            activo=db_user.activo
        )

    async def update_last_access(self, user_id: str, access_time: datetime) -> None:
        result = await self.db.execute(select(UserModel).filter_by(id=user_id))
        db_user = result.scalar_one_or_none()
        if db_user:
            db_user.ultimo_acceso = access_time
            await self.db.commit()

    async def obtener_usuario_por_id(self, user_id: str) -> Optional[Usuario]:
        """Busca un usuario por su ID."""
        result = await self.db.execute(select(UserModel).filter_by(id=user_id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return Usuario(
            id=db_user.id,
            email=db_user.email,
            nombre=db_user.nombre,
            password_hash=db_user.password_hash
        )


# class UserRepositoryImpl(UserRepository):
#     def __init__(self, db = None):
#         self.db = db or SessionLocal()

#     def create(self, usuario: Usuario) -> Usuario:
#         db_user = UserModel(
#             id=usuario.id,
#             email=usuario.email,
#             nombre=usuario.nombre,
#             password_hash=usuario.password_hash
#         )
#         self.db.add(db_user)
#         self.db.commit()
#         self.db.refresh(db_user)
#         return usuario

#     def get_by_id(self, user_id: str) -> Optional[Usuario]:
#         db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
#         if not db_user:
#             return None
#         return Usuario(
#             id=db_user.id,
#             email=db_user.email,
#             nombre=db_user.nombre,
#             password_hash=db_user.password_hash
#         )

#     def get_by_email(self, email: str) -> Optional[Usuario]:
#         db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
#         if not db_user:
#             return None
#         return Usuario(
#             id=db_user.id,
#             email=db_user.email,
#             nombre=db_user.nombre,
#             password_hash=db_user.password_hash,
#             activo=db_user.activo
#         )

#     def update_last_access(self, user_id: str, access_time: datetime) -> None:
#         self.db.query(UserModel).filter(UserModel.id == user_id).update(
#             {"ultimo_acceso": access_time}
#         )
#         self.db.commit()