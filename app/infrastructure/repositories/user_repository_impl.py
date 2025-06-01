# app/infrastructure/repositories/user_repository_impl.py
from typing import Optional, List
from datetime import datetime
import uuid
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.models import UserModel
from app.infrastructure.database.session import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text

class UserRepositoryImpl(UserRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, usuario: User) -> User:
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

    async def get_by_id(self, user_id: str) -> Optional[User]:
        try:
            # Usar consulta SQL directa con cast explícito para evitar problemas de tipo
            query = text("SELECT * FROM users WHERE id = :user_id")
            result = await self.db.execute(query, {"user_id": user_id})
            db_user = result.fetchone()
            
            if not db_user:
                return None
                
            return User(
                id=str(db_user.id),
                email=db_user.email,
                nombre=db_user.nombre,
                password_hash=db_user.password_hash,
                activo=db_user.activo
            )
        except Exception as e:
            print(f"Error en get_by_id: {e}")
            return None

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(UserModel).filter_by(email=email))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return User(
            id=str(db_user.id),
            email=db_user.email,
            nombre=db_user.nombre,
            password_hash=db_user.password_hash,
            activo=db_user.activo
        )

    async def update_last_access(self, user_id: str, access_time: datetime) -> None:
        try:
            # Usar consulta SQL directa con cast explícito para evitar problemas de tipo
            query = text("UPDATE users SET ultimo_acceso = :access_time WHERE id = :user_id")
            await self.db.execute(query, {"user_id": user_id, "access_time": access_time})
            await self.db.commit()
        except Exception as e:
            print(f"Error en update_last_access: {e}")
            pass

    async def obtener_usuario_por_id(self, user_id: str) -> Optional[User]:
        """Busca un usuario por su ID."""
        try:
            # Usar consulta SQL directa con cast explícito para evitar problemas de tipo
            query = text("SELECT * FROM users WHERE id = :user_id")
            result = await self.db.execute(query, {"user_id": user_id})
            db_user = result.fetchone()
            
            if not db_user:
                return None
                
            return User(
                id=str(db_user.id),
                email=db_user.email,
                nombre=db_user.nombre,
                password_hash=db_user.password_hash,
                activo=db_user.activo if hasattr(db_user, 'activo') else True
            )
        except Exception as e:
            print(f"Error en obtener_usuario_por_id: {e}")
            return None