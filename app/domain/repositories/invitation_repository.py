# app/domain/repositories/invitation_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.collaboration import InvitacionProyecto

class InvitationRepository(ABC):
    @abstractmethod
    def save(self, invitation: InvitacionProyecto) -> None: ...

    @abstractmethod
    def get_by_token(self, token: str) -> Optional[InvitacionProyecto]: ...

    @abstractmethod
    def list_by_project(self, project_id: str) -> List[InvitacionProyecto]: ...
