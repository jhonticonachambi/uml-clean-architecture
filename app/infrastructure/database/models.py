# # # app/infrastructure/database/models.py
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, ARRAY, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from .base import Base

def generate_uuid():
    return uuid.uuid4()

class UserModel(Base):
    __tablename__ = "users"

    # id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=generate_uuid)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True)
    nombre = Column(String(100))
    password_hash = Column(String(255))
    activo = Column(Boolean, default=True)
    fecha_registro = Column(DateTime, server_default=func.now())
    ultimo_acceso = Column(DateTime, nullable=True)
    
    # Relaciones
    proyectos = relationship("ProyectoModel", back_populates="propietario", foreign_keys="ProyectoModel.user_id")
    proyectos_miembro = relationship("MiembroProyectoModel", back_populates="usuario")
    diagramas = relationship("DiagramModel", back_populates="creador")

class ProyectoModel(Base):
    __tablename__ = "proyectos"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=generate_uuid)
    nombre = Column(String(255), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, onupdate=func.now())
    uuid_publico = Column(UUID(as_uuid=True), unique=True, nullable=False, default=generate_uuid)
    
    # Relaciones
    propietario = relationship("UserModel", back_populates="proyectos", foreign_keys=[user_id])
    miembros = relationship("MiembroProyectoModel", back_populates="proyecto")
    diagramas = relationship("DiagramModel", back_populates="proyecto")

class MiembroProyectoModel(Base):
    __tablename__ = "miembros_proyecto"
    
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), primary_key=True)
    rol = Column(String(20), nullable=False)
    fecha_union = Column(DateTime, server_default=func.now())
    
    # Relaciones
    usuario = relationship("UserModel", back_populates="proyectos_miembro")
    proyecto = relationship("ProyectoModel", back_populates="miembros")

class DiagramModel(Base):
    __tablename__ = "diagramas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=False)
    creado_por = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tipo_diagrama = Column(String(50), nullable=False)
    estado = Column(String(50), default="borrador")
    contenido_plantuml = Column(Text, nullable=True)
    contenido_original = Column(Text, nullable=True)
    lenguaje_original = Column(String(50), nullable=True)    
    errores = Column(ARRAY(String), default=[])
    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, onupdate=func.now())
    
    # Campos de versionado
    version_actual = Column(Integer, default=1, nullable=False)
    total_versiones = Column(Integer, default=1, nullable=False)
      # Relaciones
    proyecto = relationship("ProyectoModel", back_populates="diagramas")
    creador = relationship("UserModel", back_populates="diagramas")
    versiones = relationship("VersionDiagramaModel", back_populates="diagrama", cascade="all, delete-orphan")

class VersionDiagramaModel(Base):
    __tablename__ = "versiones_diagramas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagrama_id = Column(Integer, ForeignKey("diagramas.id"), nullable=False)
    numero_version = Column(Integer, nullable=False)
    contenido_original = Column(Text, nullable=False)
    notas_version = Column(Text, nullable=True)
    creado_por = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now())
    
    # Relaciones
    diagrama = relationship("DiagramModel", back_populates="versiones")
    creador = relationship("UserModel")
      # Constraint de unicidad para diagrama_id + numero_version
    __table_args__ = (
        UniqueConstraint('diagrama_id', 'numero_version', name='uq_diagrama_version'),
    )