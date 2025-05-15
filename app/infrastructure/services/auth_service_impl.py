# app/infrastructure/services/auth_service_impl.py
from datetime import datetime, timedelta
import jwt
from app.domain.services.auth_service import AuthService
from app.core.config import settings  
from typing import Optional

class AuthServiceImpl(AuthService):
    def __init__(self):
        self.SECRET_KEY = settings.SECRET_KEY
        self.ALGORITHM = "HS256"
    
    def generate_token(self, user_id: str) -> str:
        expires = datetime.utcnow() + timedelta(hours=24)
        return jwt.encode(
            {"sub": user_id, "exp": expires},
            self.SECRET_KEY,
            algorithm=self.ALGORITHM
        )
    
    def verify_token(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload["sub"]
        except jwt.PyJWTError:
            return None