# app/application/services/diagram_factory.py
from typing import Protocol
from app.application.services.converters import (
    CSharpClassConverter,
    JavaClassConverter,
    PythonClassConverter,
    CSharpSequenceConverter,
    JavaSequenceConverter
)

class BaseConverter(Protocol):
    def convert(self, code: str) -> str: ...

class DiagramFactory:
    @staticmethod
    def create_converter(language: str, diagram_type: str) -> BaseConverter:
        converters = {
            # Class Diagrams
            ('csharp', 'class'): CSharpClassConverter(),
            ('java', 'class'): JavaClassConverter(),
            ('python', 'class'): PythonClassConverter(),
            
            # Sequence Diagrams
            ('csharp', 'sequence'): CSharpSequenceConverter(),
            ('java', 'sequence'): JavaSequenceConverter(),
            
            # Agregar más combinaciones aquí
        }
        
        if (language, diagram_type) not in converters:
            raise ValueError(f"Unsupported combination: {language} + {diagram_type}")
        
        return converters[(language, diagram_type)]