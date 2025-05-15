# app/domain/services/auth_service.py
from typing import Optional, Protocol

class AuthService(Protocol):
    def generate_token(self, user_id: str) -> str:
        """Genera un token JWT."""
        ...

    def verify_token(self, token: str) -> Optional[str]:
        """Verifica un token. Retorna user_id si es válido, o None."""
        ...

    def refresh_token(self, token: str) -> Optional[str]:
        """Opcional: Refresca un token expirado."""
        ...