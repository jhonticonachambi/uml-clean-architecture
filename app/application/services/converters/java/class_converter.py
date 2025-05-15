# app/application/services/converters/java/class_converter.py
import re

class JavaClassConverter:
    def convert(self, code: str) -> str:
        plantuml = ["@startuml"]
        
        # Eliminar comentarios para simplificar el análisis
        code = re.sub(r'//.*?\n', '\n', code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        
        # Buscar todas las clases
        class_matches = list(re.finditer(r'(?:public\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{', code))
        
        for i, match in enumerate(class_matches):
            class_name = match.group(1)
            parent_class = match.group(2)
            
            # Obtener el contenido de la clase
            start_pos = match.end()
            end_pos = class_matches[i+1].start() if i+1 < len(class_matches) else len(code)
            class_body = code[start_pos:end_pos]
            
            plantuml.append(f"class {class_name} {{")
            
            # Extraer campos
            fields = re.finditer(r'(private|protected|public)\s+([\w<>]+)\s+(\w+)\s*;', class_body)
            for field in fields:
                visibility = self._get_uml_visibility(field.group(1))
                plantuml.append(f"  {visibility}{field.group(3)} : {field.group(2)}")
            
            # Extraer métodos
            methods = re.finditer(r'(private|protected|public)\s+([\w<>]+)\s+(\w+)\s*\(([^)]*)\)', class_body)
            for method in methods:
                visibility = self._get_uml_visibility(method.group(1))
                return_type = method.group(2)
                method_name = method.group(3)
                params = self._parse_parameters(method.group(4))
                plantuml.append(f"  {visibility}{method_name}({params}) : {return_type}")
            
            plantuml.append("}")
            
            # Agregar relación de herencia si existe
            if parent_class:
                plantuml.append(f"{class_name} --|> {parent_class}")
        
        plantuml.append("@enduml")
        return "\n".join(plantuml)
    
    def _get_uml_visibility(self, modifier: str) -> str:
        return {
            'private': '-',
            'protected': '#',
            'public': '+'
        }.get(modifier.lower(), '~')
    
    def _parse_parameters(self, params_str: str) -> str:
        params = []
        for param in filter(None, map(str.strip, params_str.split(','))):
            parts = re.split(r'\s+', param)
            if len(parts) >= 2:
                param_type = parts[-2]
                param_name = parts[-1]
                params.append(f"{param_name} : {param_type}")
        return ', '.join(params)