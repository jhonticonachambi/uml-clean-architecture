# app/infrastructure/database/session.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .base import Base
from dotenv import load_dotenv
import os

load_dotenv()

SQLALCHEMY_DATABASE_URL = (
    f"postgresql+{os.getenv('DB_DRIVER')}://"
    f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)


engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True,
    pool_size=5,         # Reducir el tamaño del pool
    max_overflow=10,      # Reducir el overflow máximo
    pool_timeout=60,     # Aumentar el tiempo de espera
    pool_pre_ping=True,  
    pool_recycle=1800,   # Reciclar conexiones cada 30 minutos
    # ✅ Configuración para manejar cambios de schema
    connect_args={
        "ssl": "require", 
        "timeout": 60.0, 
        "command_timeout": 60.0,
        "server_settings": {
            "application_name": "uml-clean-architecture",
            "jit": "off"  # ✅ Desactivar JIT para evitar problemas de caché
        }
    }
)


AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


