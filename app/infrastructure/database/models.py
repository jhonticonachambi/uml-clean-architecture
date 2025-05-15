# # app/infrastructure/database/models.py
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, UUID
from sqlalchemy.sql import func  # Para funciones SQL nativas
from .base import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    nombre = Column(String(100))
    password_hash = Column(String(255))
    activo = Column(Boolean, default=True)
    fecha_registro = Column(DateTime, server_default=func.now())  # Mejor práctica para async
    ultimo_acceso = Column(DateTime, nullable=True)

class DiagramaModel(Base):
    __tablename__ = "diagramas"

    id = Column(String(36), primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    proyecto_id = Column(String(36), nullable=False)
    creado_por = Column(String(36), nullable=False)
    estado = Column(String(50), default="borrador")
    contenido_plantuml = Column(Text, nullable=True)
    contenido_original = Column(Text, nullable=True)
    lenguaje_original = Column(String(50), nullable=True)
    errores = Column(Text, nullable=True)  # Almacenar errores como JSON o texto
    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, onupdate=func.now())

class ProyectoModel(Base):
    __tablename__ = "proyectos"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # Relación con el usuario
    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, onupdate=func.now())
    uuid_publico = Column(UUID(as_uuid=True), unique=True, nullable=False)

    # Relación con miembros y diagramas (si es necesario)
    # miembros = relationship("MiembroProyectoModel", back_populates="proyecto")
    # diagramas = relationship("DiagramaModel", back_populates="proyecto")