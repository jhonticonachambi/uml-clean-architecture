# app/infrastructure/services/password_service_impl.py
from passlib.context import CryptContext
from app.domain.services.password_service import PasswordService

class PasswordServiceImpl(PasswordService):
    def __init__(self):
        self.crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self.crypt_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.crypt_context.verify(plain_password, hashed_password)