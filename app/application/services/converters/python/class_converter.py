# # app/application/services/converters/python/class_converter.py
# class PythonClassConverter:
#     def convert(self, code: str) -> str:
#         plantuml = ["@startuml"]
        
#         if "class" in code:
#             class_name = self._extract_python_class_name(code)
#             plantuml.append(f"class {class_name} {{")
            
#             if "def __init__" in code:
#                 plantuml.append("  +__init__()")
#             if "def " in code:
#                 plantuml.append("  +method1()")
                
#             plantuml.append("}")
        
#         plantuml.append("@enduml")
#         return "\n".join(plantuml)
    
#     def _extract_python_class_name(self, code: str) -> str:
#         for line in code.split('\n'):
#             if line.strip().startswith("class "):
#                 return line.split('class')[-1].split('(')[0].strip()
#         return "PythonClass"





# app/application/services/converters/python/class_converter.py

import ast
from typing import List

class PythonClassConverter:
    def convert(self, code: str) -> str:
        tree = ast.parse(code)
        class_defs = [node for node in tree.body if isinstance(node, ast.ClassDef)]

        plantuml_lines = ["@startuml"]
        inheritance_links = []

        for cls in class_defs:
            class_name = cls.name
            bases = [self._get_base_name(base) for base in cls.bases]
            attributes = self._extract_attributes(cls)
            methods = self._extract_methods(cls)

            plantuml_lines.append(f"class {class_name} {{")
            for attr in attributes:
                plantuml_lines.append(f"  - {attr}")
            for method in methods:
                plantuml_lines.append(f"  + {method}()")
            plantuml_lines.append("}")

            for base in bases:
                if base != "object":
                    inheritance_links.append(f"{base} <|-- {class_name}")

        plantuml_lines.extend(inheritance_links)
        plantuml_lines.append("@enduml")
        return "\n".join(plantuml_lines)

    def _get_base_name(self, base: ast.expr) -> str:
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
        return "object"

    def _extract_attributes(self, cls: ast.ClassDef) -> List[str]:
        attributes = []
        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and node.name == "__init__":
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                                attributes.append(target.attr)
        return attributes

    def _extract_methods(self, cls: ast.ClassDef) -> List[str]:
        methods = []
        for node in cls.body:
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("__"):
                methods.append(node.name)
        return methods
