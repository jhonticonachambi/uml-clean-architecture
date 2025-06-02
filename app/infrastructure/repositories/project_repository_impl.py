from app.domain.repositories.project_repository import ProjectRepository
from app.domain.entities.project import Proyecto, MiembroProyecto
from typing import Optional, List, Dict
from sqlalchemy.future import select
from app.infrastructure.database.models import ProyectoModel, MiembroProyectoModel
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.domain.entities.base import RolProyecto
from sqlalchemy import text
import logging
import uuid

class ProjectRepositoryImpl(ProjectRepository):
    def __init__(self, db):
        self.db = db

    def guardar_proyecto(self, proyecto: Proyecto) -> None:
        """Guarda un proyecto en la base de datos."""
        # Aquí se debe implementar la lógica para guardar el proyecto en la base de datos.
        # Por ejemplo, convertir el objeto `Proyecto` a un modelo de base de datos y guardarlo.
        print(f"[DEBUG] Guardando proyecto: {proyecto}")
        # Simulación de guardado (reemplazar con lógica real)
        pass

    async def save(self, project: Proyecto) -> None:
        """Guarda un proyecto en la base de datos."""
        try:
            # Convertir los UUID de cadenas a objetos UUID
            proyecto_id = uuid.UUID(project.id) if isinstance(project.id, str) else project.id
            user_id = uuid.UUID(project.user_id) if isinstance(project.user_id, str) else project.user_id
            uuid_publico = uuid.UUID(project.uuid_publico) if isinstance(project.uuid_publico, str) else project.uuid_publico
            
            proyecto_model = ProyectoModel(
                id=proyecto_id,
                nombre=project.nombre,
                user_id=user_id,
                fecha_creacion=project.fecha_creacion,
                fecha_actualizacion=project.fecha_actualizacion,
                uuid_publico=uuid_publico
            )
            self.db.add(proyecto_model)
            await self.db.commit()
            await self.db.refresh(proyecto_model)
        except IntegrityError as e:
            logging.error(f"Error de integridad al guardar el proyecto: {str(e)}")
            await self.db.rollback()
            raise ValueError(f"Error de integridad: {str(e)}")
        except SQLAlchemyError as e:
            logging.error(f"Error al guardar el proyecto: {str(e)}")
            await self.db.rollback()
            raise ValueError(f"Error al guardar el proyecto: {str(e)}")

    async def get_by_id(self, project_id: str) -> Optional[Proyecto]:
        """Obtiene un proyecto por su ID."""
        try:
            logging.info(f"[DEBUG] Ejecutando consulta para obtener proyecto con ID: {project_id}")
            query = text("SELECT * FROM proyectos WHERE id = :project_id")
            result = await self.db.execute(query, {"project_id": project_id})
            proyecto_model = result.fetchone()

            if not proyecto_model:
                logging.warning(f"[WARN] Proyecto con ID {project_id} no encontrado")
                return None

            logging.info(f"[DEBUG] Proyecto encontrado: {proyecto_model}")
            return Proyecto(
                id=str(proyecto_model.id),
                nombre=proyecto_model.nombre,
                user_id=str(proyecto_model.user_id),
                fecha_creacion=proyecto_model.fecha_creacion,
                fecha_actualizacion=proyecto_model.fecha_actualizacion,
                uuid_publico=str(proyecto_model.uuid_publico)
            )
        except Exception as e:
            logging.error(f"[ERROR] Error al obtener proyecto por ID: {str(e)}")
            return None

    async def list_by_user(self, user_id: str) -> List[Proyecto]:
        """Obtiene todos los proyectos de un usuario específico."""
        try:
            # Convertir el ID a un objeto UUID
            user_uuid = uuid.UUID(user_id)
            
            query = await self.db.execute(
                select(ProyectoModel).filter(ProyectoModel.user_id == user_uuid)
            )
            proyecto_models = query.scalars().all()
            return [Proyecto(
                id=str(modelo.id),
                nombre=modelo.nombre,
                user_id=str(modelo.user_id),
                fecha_creacion=modelo.fecha_creacion,
                fecha_actualizacion=modelo.fecha_actualizacion,
                uuid_publico=str(modelo.uuid_publico)
            ) for modelo in proyecto_models]
        except ValueError:
            # Si el user_id no es un UUID válido
            return []
        except SQLAlchemyError as e:
            logging.error(f"Error al listar proyectos por usuario: {str(e)}")
            raise ValueError(f"Error al listar proyectos: {str(e)}")
            
    async def list_all(self) -> List[Proyecto]:
        """Obtiene todos los proyectos."""
        try:
            query = await self.db.execute(select(ProyectoModel))
            proyecto_models = query.scalars().all()
            return [Proyecto(
                id=str(modelo.id),
                nombre=modelo.nombre,
                user_id=str(modelo.user_id),
                fecha_creacion=modelo.fecha_creacion,
                fecha_actualizacion=modelo.fecha_actualizacion,
                uuid_publico=str(modelo.uuid_publico)
            ) for modelo in proyecto_models]
        except SQLAlchemyError as e:
            logging.error(f"Error al listar todos los proyectos: {str(e)}")
            raise ValueError(f"Error al listar todos los proyectos: {str(e)}")
        
    async def update(self, project: Proyecto) -> None:
        """Actualiza un proyecto existente."""
        try:
            # Convertir los UUID de cadenas a objetos UUID
            proyecto_id = uuid.UUID(project.id) if isinstance(project.id, str) else project.id
            user_id = uuid.UUID(project.user_id) if isinstance(project.user_id, str) else project.user_id
            uuid_publico = uuid.UUID(project.uuid_publico) if isinstance(project.uuid_publico, str) else project.uuid_publico
            
            proyecto_model = await self.db.get(ProyectoModel, proyecto_id)
            if not proyecto_model:
                raise ValueError(f"El proyecto con ID {project.id} no existe")
            
            # Actualizar los campos del modelo
            proyecto_model.nombre = project.nombre
            proyecto_model.user_id = user_id
            proyecto_model.fecha_creacion = project.fecha_creacion
            proyecto_model.fecha_actualizacion = project.fecha_actualizacion
            proyecto_model.uuid_publico = uuid_publico
            
            await self.db.commit()
            await self.db.refresh(proyecto_model)
        except IntegrityError as e:
            logging.error(f"Error de integridad al actualizar el proyecto: {str(e)}")
            await self.db.rollback()
            raise ValueError(f"Error de integridad: {str(e)}")
        except SQLAlchemyError as e:
            logging.error(f"Error al actualizar el proyecto: {str(e)}")
            await self.db.rollback()
            raise ValueError(f"Error al actualizar el proyecto: {str(e)}")
        
    async def add_member(self, project_id: str, member: MiembroProyecto) -> None:
        """
        Agrega un miembro a un proyecto existente.
        
        Args:
            project_id: ID del proyecto
            member: Objeto MiembroProyecto con los datos del miembro
        
        Raises:
            ValueError: Si el proyecto no existe o si hay un error al añadir el miembro
        """
        try:
            # Verificar que el proyecto existe usando SQL nativo
            query = text("SELECT * FROM proyectos WHERE id = :project_id")
            result = await self.db.execute(query, {"project_id": project_id})
            proyecto_model = result.fetchone()
            
            if not proyecto_model:
                raise ValueError(f"El proyecto con ID {project_id} no existe")
            
            # Verificar si el miembro ya existe usando SQL nativo
            query = text("""
                SELECT * FROM miembros_proyecto 
                WHERE proyecto_id = :project_id AND usuario_id = :user_id
            """)
            result = await self.db.execute(query, {
                "project_id": project_id, 
                "user_id": member.usuario_id
            })
            existing_member = result.fetchone()
            
            if existing_member:
                # Si el miembro ya existe, actualizamos su rol
                update_query = text("""
                    UPDATE miembros_proyecto 
                    SET rol = :rol 
                    WHERE proyecto_id = :project_id AND usuario_id = :user_id
                """)
                await self.db.execute(update_query, {
                    "rol": member.rol.value,
                    "project_id": project_id,
                    "user_id": member.usuario_id
                })
            else:
                # Si no existe, creamos un nuevo miembro usando SQL nativo
                insert_query = text("""
                    INSERT INTO miembros_proyecto (usuario_id, proyecto_id, rol, fecha_union)
                    VALUES (:user_id, :project_id, :rol, :fecha_union)
                """)
                await self.db.execute(insert_query, {
                    "user_id": member.usuario_id,
                    "project_id": project_id,
                    "rol": member.rol.value,
                    "fecha_union": member.fecha_union
                })
            
            # Actualizamos la fecha de actualización del proyecto
            update_proyecto_query = text("""
                UPDATE proyectos 
                SET fecha_actualizacion = :fecha 
                WHERE id = :project_id
            """)
            await self.db.execute(update_proyecto_query, {
                "fecha": datetime.now(),
                "project_id": project_id
            })
            
            # Guardamos los cambios
            await self.db.commit()
            
        except ValueError as e:
            logging.error(f"Error de valor al añadir miembro: {str(e)}")
            await self.db.rollback()
            raise ValueError(f"Error de valor: {str(e)}")
        except IntegrityError as e:
            logging.error(f"Error de integridad al añadir miembro: {str(e)}")
            await self.db.rollback()
            raise ValueError(f"Error de integridad: {str(e)}")
        except SQLAlchemyError as e:
            logging.error(f"Error al añadir miembro al proyecto: {str(e)}")
            await self.db.rollback()
            raise ValueError(f"Error al añadir miembro: {str(e)}")
        except Exception as e:
            logging.error(f"Error inesperado: {str(e)}")
            await self.db.rollback()
            raise ValueError(f"Error inesperado: {str(e)}")

    async def get_projects_by_owner(self, owner_id: str) -> List[Proyecto]:
        """Obtiene todos los proyectos donde el usuario es propietario."""
        try:
            # Validar que el owner_id es un UUID válido
            logging.debug(f"[DEBUG] Valor recibido para owner_id: {owner_id}")
            owner_uuid = uuid.UUID(owner_id)

            logging.debug(f"[DEBUG] UUID convertido para owner_id: {owner_uuid}")
            query = select(ProyectoModel).where(ProyectoModel.user_id == owner_uuid)
            logging.debug(f"[DEBUG] Consulta generada: {query}")

            result = await self.db.execute(query)
            proyectos = result.scalars().all()

            logging.debug(f"[DEBUG] Proyectos obtenidos: {proyectos}")
            return [Proyecto.from_orm(proyecto) for proyecto in proyectos]
        except ValueError:
            logging.error(f"El owner_id proporcionado no es un UUID válido: {owner_id}")
            raise ValueError("El ID del propietario no es válido.")
        except SQLAlchemyError as e:
            logging.error(f"Error al obtener proyectos por propietario: {str(e)}")
            raise ValueError("Error al obtener proyectos por propietario.")

    async def get_projects_by_membership(self, user_id: str) -> List[Proyecto]:
        """Obtiene todos los proyectos donde el usuario es miembro."""
        try:
            query = text(
                """
                SELECT p.* FROM proyectos p
                JOIN miembros_proyecto mp ON p.id = mp.proyecto_id
                WHERE mp.usuario_id = :user_id                """
            )
            result = await self.db.execute(query, {"user_id": user_id})
            proyectos = result.fetchall()
            return [Proyecto.from_orm(proyecto) for proyecto in proyectos]
        except SQLAlchemyError as e:
            logging.error(f"Error al obtener proyectos por membresía: {str(e)}")
            return []
    
    async def get_accessible_projects(self, user_id: str) -> List[Dict]:
        """
        Busca proyectos en DOS TABLAS:
        1. proyectos donde user_id = usuario (es propietario)
        2. miembros_proyecto donde usuario_id = usuario (es miembro)
        """
        try:
            query = text("""
                SELECT DISTINCT 
                    p.id,
                    p.nombre,
                    p.fecha_creacion,
                    p.fecha_actualizacion,
                    p.uuid_publico,
                    p.user_id as propietario_id,
                    CASE 
                        WHEN p.user_id = :user_id THEN 'propietario'
                        ELSE COALESCE(mp.rol, 'miembro')
                    END as mi_rol,
                    CASE 
                        WHEN p.user_id = :user_id THEN 'proyecto_propio'
                        ELSE 'proyecto_compartido'
                    END as tipo_acceso
                FROM proyectos p
                LEFT JOIN miembros_proyecto mp ON p.id = mp.proyecto_id AND mp.usuario_id = :user_id
                WHERE 
                    p.user_id = :user_id  -- Es propietario
                    OR 
                    mp.usuario_id = :user_id  -- Es miembro
                ORDER BY p.fecha_actualizacion DESC
            """)
            
            result = await self.db.execute(query, {"user_id": user_id})
            proyectos = result.fetchall()
            
            # Formatear respuesta
            proyectos_formateados = []
            for proyecto in proyectos:
                proyectos_formateados.append({
                    "id": str(proyecto.id),
                    "nombre": proyecto.nombre,
                    "fecha_creacion": proyecto.fecha_creacion,
                    "fecha_actualizacion": proyecto.fecha_actualizacion,
                    "uuid_publico": str(proyecto.uuid_publico),
                    "mi_rol": proyecto.mi_rol,
                    "tipo_acceso": proyecto.tipo_acceso,
                    "soy_propietario": str(proyecto.propietario_id) == user_id,
                    "puedo_editar": proyecto.mi_rol in ["propietario", "editor"],
                    "puedo_administrar": proyecto.mi_rol == "propietario"
                })
            
            return proyectos_formateados
            
        except SQLAlchemyError as e:
            logging.error(f"Error al obtener proyectos accesibles: {str(e)}")
            return []    
        
    async def get_project_members(self, proyecto_id: str) -> List[Dict]:
        """
        Obtiene todos los miembros de un proyecto específico con información del usuario.
        Incluye tanto a los miembros de la tabla miembros_proyecto como al propietario.
        """
        try:
            query = text("""
                SELECT 
                    usuario_id,
                    proyecto_id,
                    rol,
                    fecha_union,
                    usuario_nombre,
                    usuario_email,
                    usuario_activo
                FROM (
                    SELECT 
                        mp.usuario_id,
                        mp.proyecto_id,
                        mp.rol,
                        mp.fecha_union,
                        u.nombre as usuario_nombre,
                        u.email as usuario_email,
                        u.activo as usuario_activo
                    FROM miembros_proyecto mp
                    INNER JOIN users u ON mp.usuario_id = u.id
                    WHERE mp.proyecto_id = :proyecto_id
                    
                    UNION ALL
                    
                    SELECT 
                        p.user_id as usuario_id,
                        p.id as proyecto_id,
                        'propietario' as rol,
                        p.fecha_creacion as fecha_union,
                        u.nombre as usuario_nombre,
                        u.email as usuario_email,
                        u.activo as usuario_activo
                    FROM proyectos p
                    INNER JOIN users u ON p.user_id = u.id
                    WHERE p.id = :proyecto_id
                ) as todos_miembros
                ORDER BY 
                    CASE WHEN rol = 'propietario' THEN 0 ELSE 1 END,
                    fecha_union ASC
            """)
            
            result = await self.db.execute(query, {"proyecto_id": proyecto_id})
            miembros_data = result.fetchall()
            
            miembros_formateados = []
            for miembro in miembros_data:
                miembros_formateados.append({
                    "usuario_id": str(miembro.usuario_id),
                    "proyecto_id": str(miembro.proyecto_id),
                    "rol": miembro.rol,
                    "fecha_union": miembro.fecha_union,
                    "usuario": {
                        "id": str(miembro.usuario_id),
                        "nombre": miembro.usuario_nombre,
                        "email": miembro.usuario_email,
                        "activo": miembro.usuario_activo
                    },
                    "permisos": {
                        "puede_editar": miembro.rol in ["propietario", "editor"],
                        "puede_administrar": miembro.rol == "propietario",
                        "puede_ver": True
                    }
                })
            
            return miembros_formateados
            
        except SQLAlchemyError as e:
            logging.error(f"Error al obtener miembros del proyecto: {str(e)}")
            return []