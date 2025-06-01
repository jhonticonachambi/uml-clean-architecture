# app/application/use_cases/diagram/generate_diagram.py
from typing import Dict, List
from app.application.services.diagram_factory import DiagramFactory
from app.application.services.diagram_builder import DiagramBuilder
from app.domain.entities.diagram import Diagrama
from datetime import datetime
from app.domain.entities.diagram import TipoDiagrama

class GenerarDiagramaDesdeCodigoUseCase:
    """
    Caso de uso para generar diagramas UML desde código fuente.
    Esta versión simplificada solo usa los conversores y DiagramFactory.
    """
    def __init__(self, factory=None, builder=None):
        self.factory = factory or DiagramFactory()
        self.builder = builder or DiagramBuilder(self.factory)

    def ejecutar(
        self,
        codigo_fuente: str,
        lenguaje: str,
        diagramas_solicitados: List[str] = None,
        proyecto_id: str = None,
        creado_por: str = None
    ) -> List[Diagrama]:
        """
        Genera diagramas UML desde código fuente sin validación de proyecto.
        """
        # Valor por defecto
        if not diagramas_solicitados:
            diagramas_solicitados = ['class']

        # Mapeo de tipos de diagrama al formato esperado
        tipo_diagrama_map = {
            "clases": "class",
            "secuencia": "sequence",
            "actividad": "activity",
            "casos_de_uso": "use_case"
        }

        # Normalizar los tipos de diagramas solicitados
        diagramas_normalizados = [
            tipo_diagrama_map.get(tipo, tipo) for tipo in diagramas_solicitados
        ]

        # Usar el builder para generar los diagramas solicitados
        resultados = self.builder.build_diagrams(
            code=codigo_fuente,
            language=lenguaje,
            diagram_types=diagramas_normalizados
        )

        # Convertir los resultados en entidades Diagrama
        diagramas = []
        for tipo, contenido in resultados.items():
            diagrama = Diagrama(
                nombre=f"Diagrama {tipo}",
                proyecto_id=proyecto_id,
                creado_por=creado_por or "sistema",
                tipo_diagrama=TipoDiagrama(tipo),  # Convertir el tipo al Enum
                contenido_plantuml=contenido if not contenido.startswith("Error:") else None,
                errores=[contenido] if contenido.startswith("Error:") else [],
                fecha_creacion=datetime.now(),
                fecha_actualizacion=datetime.now()
            )
            
            # Marcar como validado o agregar error
            if not contenido.startswith("Error:"):
                diagrama.marcar_como_validado(contenido)
            else:
                diagrama.agregar_error(contenido)

            diagramas.append(diagrama)

        return diagramas

    # def ejecutar(
    #     self,
    #     codigo_fuente: str,
    #     lenguaje: str,
    #     diagramas_solicitados: List[str] = None,
    #     proyecto_id: str = None,
    #     creado_por: str = None
    # ) -> List[Diagrama]:
    #     """
    #     Genera diagramas UML desde código fuente sin validación de proyecto.
        
    #     Args:
    #         codigo_fuente: Código a convertir en diagrama
    #         lenguaje: Lenguaje del código fuente (java, csharp, python)
    #         diagramas_solicitados: Lista de tipos de diagramas a generar
    #         proyecto_id: ID del proyecto (opcional)
    #         creado_por: ID de usuario que genera el diagrama (opcional)
            
    #     Returns:
    #         Lista de objetos Diagrama generados
    #     """
    #     # Valor por defecto
    #     if not diagramas_solicitados:
    #         diagramas_solicitados = ['class']

    #     # Usar el builder para generar los diagramas solicitados
    #     resultados = self.builder.build_diagrams(
    #         code=codigo_fuente,
    #         language=lenguaje,
    #         diagram_types=diagramas_solicitados
    #     )

    #     # Convertir los resultados en entidades Diagrama
    #     diagramas = []
    #     for tipo, contenido in resultados.items():
    #         diagrama = Diagrama(
    #             nombre=f"Diagrama {tipo}",
    #             proyecto_id=proyecto_id,
    #             creado_por=creado_por or "sistema",
    #             tipo_diagrama=TipoDiagrama(tipo),  # Convertir el tipo al Enum
    #             contenido_plantuml=contenido if not contenido.startswith("Error:") else None,
    #             errores=[contenido] if contenido.startswith("Error:") else [],
    #             fecha_creacion=datetime.now(),
    #             fecha_actualizacion=datetime.now()
    #         )
            
    #         # Marcar como validado o agregar error
    #         if not contenido.startswith("Error:"):
    #             diagrama.marcar_como_validado(contenido)
    #         else:
    #             diagrama.agregar_error(contenido)

    #         diagramas.append(diagrama)

    #     return diagramas
