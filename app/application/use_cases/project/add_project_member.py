#application/use_cases/project/add_project_member.py
from app.domain.entities.project import Proyecto, MiembroProyecto
from app.domain.entities.base import RolProyecto
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.user_repository import UserRepository

class AgregarMiembroUseCase:
    def __init__(self, proyecto_repository: ProjectRepository, usuario_repository: UserRepository):
        self.proyecto_repository = proyecto_repository
        self.usuario_repository = usuario_repository
    
    async def execute(self, proyecto_id: str, usuario_id: str, rol: str, usuario_solicitante_id: str) -> MiembroProyecto:
        """
        Agrega un miembro a un proyecto.
        
        Args:
            proyecto_id: ID del proyecto
            usuario_id: ID del usuario a agregar
            rol: Rol que tendrá el usuario ('propietario', 'editor', 'visualizador')
            usuario_solicitante_id: ID del usuario que solicita la operación
            
        Returns:
            MiembroProyecto: El nuevo miembro agregado
            
        Raises:
            ValueError: Si el usuario no existe o el rol es inválido
            PermissionError: Si el solicitante no tiene permisos para agregar miembros
        """
        # 1. Verificar que el proyecto existe
        proyecto = await self.proyecto_repository.get_by_id(proyecto_id)
        if not proyecto:
            raise ValueError(f"El proyecto con ID {proyecto_id} no existe")
            
        # 2. Verificar que el usuario existe
        usuario = await self.usuario_repository.get_by_id(usuario_id)
        if not usuario:
            raise ValueError(f"El usuario con ID {usuario_id} no existe")
              # 3. Verificar que el solicitante tiene permisos (debe ser propietario del proyecto)
        if not proyecto.es_propietario(usuario_solicitante_id):
            raise PermissionError("Solo el propietario puede agregar miembros")
            
        # 4. Convertir el string de rol a enum
        try:
            rol_enum = RolProyecto(rol)
        except ValueError:
            raise ValueError(f"Rol inválido: {rol}. Debe ser: propietario, editor o visualizador")
        
        # 5. Crear el objeto MiembroProyecto
        miembro = MiembroProyecto(
            usuario_id=usuario_id,
            proyecto_id=proyecto_id,
            rol=rol_enum
        )
        
        # 6. Agregar el miembro usando el nuevo método
        await self.proyecto_repository.add_member(proyecto_id, miembro)
        
        return miembro