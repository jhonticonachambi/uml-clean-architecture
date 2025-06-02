from typing import Optional
from app.domain.entities.base import RolProyecto

class MemberRepository:
    async def get_user_role_in_project(self, user_id: str, project_id: str) -> Optional[RolProyecto]:
        """Obtiene el rol del usuario en un proyecto específico."""
        pass
