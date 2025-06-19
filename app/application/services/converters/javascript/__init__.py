"""
Convertidores de JavaScript/TypeScript a diagramas UML PlantUML.

Este módulo contiene convertidores especializados para analizar código JavaScript y TypeScript
y generar diferentes tipos de diagramas UML:

- class_converter: Convierte clases, interfaces y enums a diagramas de clases
- sequence_converter: Analiza llamadas y flujo de métodos para diagramas de secuencia
- usecase_converter: Extrae casos de uso de rutas, controladores y servicios
- activity_converter: Mapea flujo de control y actividades en funciones

Soporta:
- ES6+ y TypeScript
- Clases, interfaces, herencia e implementación
- Decoradores y metadatos
- Async/await y Promises
- Frameworks web (Express, Next.js, etc.)
- Patrones de arquitectura comunes
"""

from .class_converter import JavaScriptClassConverter
from .sequence_converter import JavaScriptSequenceConverter
from .usecase_converter import JavaScriptUseCaseConverter
from .activity_converter import JavaScriptActivityConverter

__all__ = [
    'JavaScriptClassConverter',
    'JavaScriptSequenceConverter', 
    'JavaScriptUseCaseConverter',
    'JavaScriptActivityConverter'
]

# Alias para TypeScript (mismo convertidor)
TypeScriptClassConverter = JavaScriptClassConverter
TypeScriptSequenceConverter = JavaScriptSequenceConverter
TypeScriptUseCaseConverter = JavaScriptUseCaseConverter
TypeScriptActivityConverter = JavaScriptActivityConverter
