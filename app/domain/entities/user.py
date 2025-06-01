# domain/entities/user.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class User:
    email: str
    nombre: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fecha_registro: datetime = field(default_factory=datetime.now)
    ultimo_acceso: Optional[datetime] = None
    avatar_url: Optional[str] = None
    password_hash: Optional[str] = None
    activo: bool = True

    def __post_init__(self):
        self.validar()

    def validar(self):
        if not self.email or "@" not in self.email:
            raise ValueError("Email inválido")
        if not self.nombre or len(self.nombre.strip()) < 2:
            raise ValueError("Nombre debe tener al menos 2 caracteres")

    def registrar_acceso(self, ahora: Optional[datetime] = None):
        self.ultimo_acceso = ahora or datetime.now()

    def cambiar_password(self, hash_password: str):
        self.password_hash = hash_password

    def activate(self):
        self.activo = True

    def deactivate(self):
        self.activo = False