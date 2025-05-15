from app.application.services.project_service import ProjectService
from app.application.services.diagram_service import DiagramService
from app.domain.entities.diagrama import Diagrama

class GenerarDiagramaUseCase:
    def __init__(self, project_service: ProjectService, diagram_service: DiagramService):
        self.project_service = project_service
        self.diagram_service = diagram_service

    async def ejecutar(self, proyecto_id: str, nombre: str, contenido: str, lenguaje: str, tipo_diagrama: str) -> Diagrama:
        """Genera un diagrama asociado a un proyecto válido con el tipo y lenguaje especificados."""
        # Validar que el proyecto existe
        proyecto = await self.project_service.obtener_proyecto_por_id(proyecto_id)
        if not proyecto:
            raise ValueError("El proyecto especificado no existe")

        # Crear el diagrama asociado al proyecto
        diagrama = Diagrama(
            nombre=nombre,
            proyecto_id=proyecto_id,
            contenido_original=contenido,
            lenguaje_original=lenguaje
        )

        # Generar el contenido del diagrama usando DiagramBuilder
        builder = self.diagram_service.get_builder()
        resultado = builder.build_diagrams(contenido, lenguaje, [tipo_diagrama])

        if tipo_diagrama in resultado and not resultado[tipo_diagrama].startswith("Error:"):
            diagrama.marcar_como_validado(resultado[tipo_diagrama])
        else:
            diagrama.agregar_error(resultado.get(tipo_diagrama, "Error desconocido"))

        await self.diagram_service.guardar_diagrama(diagrama)
        return diagrama
