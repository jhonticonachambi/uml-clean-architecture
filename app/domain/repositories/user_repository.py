# app/domain/repositories/user_repository.py

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.domain.entities.usuario import Usuario  

class UserRepository:
    """Interfaz abstracta para el repositorio de usuarios."""

    def create(self, usuario: Usuario) -> Usuario:
        """Guarda un nuevo usuario en la base de datos."""
        raise NotImplementedError()

    def get_by_id(self, user_id: str) -> Optional[Usuario]:
        """Obtiene un usuario por su ID. Retorna None si no existe."""
        raise NotImplementedError()

    def get_by_email(self, email: str) -> Optional[Usuario]:
        """Busca un usuario por email. Retorna None si no existe."""
        raise NotImplementedError()

    def update(self, usuario: Usuario) -> Usuario:
        """Actualiza los datos de un usuario existente."""
        raise NotImplementedError()

    def delete(self, user_id: str) -> bool:
        """Elimina un usuario. Retorna True si tuvo éxito."""
        raise NotImplementedError()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Usuario]:
        """Lista usuarios con paginación."""
        raise NotImplementedError()

    def update_last_access(self, user_id: str, access_time: datetime) -> None:
        """Actualiza la fecha de último acceso del usuario."""
        raise NotImplementedError()