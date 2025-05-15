# from datetime import datetime
# from typing import Optional
# from app.domain.repositories.user_repository import UserRepository
# from app.domain.entities.usuario import Usuario
# from app.domain.services.password_service import PasswordService

# # DTO (Data Transfer Object) para el request
# class RegistrarUsuarioRequest:
#     def __init__(self, email: str, nombre: str, password: str):
#         self.email = email
#         self.nombre = nombre
#         self.password = password

# class RegistrarUsuarioUseCase:
#     def __init__(
#         self,
#         user_repository: UserRepository,
#         password_service: 'PasswordService'  # Interfaz abstracta para hashing
#     ):
#         self.user_repo = user_repository
#         self.password_service = password_service

#     def execute(self, request: RegistrarUsuarioRequest) -> Usuario:
#         # Validar que el email no exista
#         if self.user_repo.get_by_email(request.email):
#             raise ValueError("El email ya está registrado")

#         # Hashear la contraseña
#         password_hash = self.password_service.hash_password(request.password)

#         # Crear la entidad Usuario
#         usuario = Usuario(
#             email=request.email,
#             nombre=request.nombre,
#             password_hash=password_hash
#         )

#         # Guardar en el repositorio
#         return self.user_repo.create(usuario)





from datetime import datetime
from typing import Optional
from app.domain.repositories.user_repository import UserRepository
from app.domain.entities.usuario import Usuario
from app.domain.services.password_service import PasswordService

class RegistrarUsuarioRequest:
    def __init__(self, email: str, nombre: str, password: str):
        self.email = email
        self.nombre = nombre
        self.password = password

class RegistrarUsuarioUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_service: 'PasswordService'
    ):
        self.user_repo = user_repository
        self.password_service = password_service

    # ¡Agrega async aquí!
    async def execute(self, request: RegistrarUsuarioRequest) -> Usuario:
        # Usa await para llamadas asíncronas
        existing_user = await self.user_repo.get_by_email(request.email)
        
        # Verifica explícitamente si es None
        if existing_user is not None:
            raise ValueError("El email ya está registrado")

        password_hash = self.password_service.hash_password(request.password)
        
        usuario = Usuario(
            email=request.email,
            nombre=request.nombre,
            password_hash=password_hash
        )
        
        # Await para crear el usuario
        return await self.user_repo.create(usuario)