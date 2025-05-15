# app/application/services/diagram_builder.py
from typing import Dict, List

class DiagramBuilder:
    def __init__(self, factory):
        self.factory = factory
    
    def build_diagrams(self, code: str, language: str, diagram_types: List[str]) -> Dict[str, str]:
        results = {}
        for diagram_type in diagram_types:
            try:
                converter = self.factory.create_converter(language, diagram_type)
                results[diagram_type] = converter.convert(code)
            except ValueError as e:
                results[diagram_type] = f"Error: {str(e)}"
        return results