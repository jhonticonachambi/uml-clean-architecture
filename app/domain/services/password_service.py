# app/domain/services/password_service.py
from typing import Protocol

class PasswordService(Protocol):
    """Interfaz para el servicio de manejo de contraseñas."""

    def hash_password(self, password: str) -> str:
        """Convierte una contraseña en su versión hasheada."""
        ...

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica si una contraseña coincide con su hash."""
        ...