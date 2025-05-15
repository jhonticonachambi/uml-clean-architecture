# # app/application/services/converters/csharp/sequence_converter.py
import re
from collections import defaultdict

class CSharpSequenceConverter:
    def __init__(self):
        self.role_mapping = {
            'View': 'boundary',
            'Screen': 'boundary',
            'Form': 'boundary',
            'Service': 'control',
            'Controller': 'control',
            'Manager': 'control',
            'Repository': 'database',
            'Context': 'database',
            'Db': 'database'
        }
        self.field_mappings = defaultdict(dict)
        self.current_class = None

    def convert(self, code: str) -> str:
        code = self._clean_code(code)
        self._analyze_class_structure(code)
        interactions = self._analyze_method_calls(code)
        
        plantuml = ["@startuml"]
        plantuml += self._generate_participants()
        plantuml += self._generate_sequence(interactions)
        plantuml.append("@enduml")
        
        return "\n".join(plantuml)

    def _clean_code(self, code):
        code = re.sub(r'//.*?\n', '\n', code)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        return code

    def _analyze_class_structure(self, code):
        class_pattern = r'public class (\w+).*?\{([^}]*)\}'
        for class_match in re.finditer(class_pattern, code, re.DOTALL):
            class_name = class_match.group(1)
            self.current_class = class_name
            class_body = class_match.group(2)
            
            # Analizar campos
            field_pattern = r'(?:private|protected|public)\s+(\w+)\s+(\w+)\s*;'
            for field_match in re.finditer(field_pattern, class_body):
                field_type = field_match.group(1)
                field_name = field_match.group(2)
                self.field_mappings[class_name][field_name] = field_type

    def _analyze_method_calls(self, code):
        interactions = []
        method_pattern = r'public \w+ (\w+)\(.*?\)\s*\{([^}]*)\}'
        
        for method_match in re.finditer(method_pattern, code, re.DOTALL):
            method_name = method_match.group(1)
            method_body = method_match.group(2)
            caller_class = self._find_class_by_position(code, method_match.start())
            
            # Llamadas a métodos
            call_pattern = r'(\w+)\.(\w+)\(([^)]*)\)'
            for call_match in re.finditer(call_pattern, method_body):
                instance = call_match.group(1)
                method_called = call_match.group(2)
                params = call_match.group(3)
                
                callee_class = self._resolve_instance_type(caller_class, instance)
                if callee_class:
                    interactions.append({
                        'from': caller_class,
                        'to': callee_class,
                        'message': f"{method_called}({params})"
                    })
            
            # Creación de objetos
            new_pattern = r'new (\w+)\(([^)]*)\)'
            for new_match in re.finditer(new_pattern, method_body):
                class_name = new_match.group(1)
                params = new_match.group(2)
                interactions.append({
                    'from': caller_class,
                    'to': class_name,
                    'message': f"new({params})"
                })
        
        return interactions

    def _generate_participants(self):
        lines = ["actor Usuario"]
        added_classes = set()
        
        # Primero agregar boundary (si existe)
        for class_name, fields in self.field_mappings.items():
            if self._get_role(class_name) == 'boundary':
                lines.append(f'boundary "{class_name}" as {class_name}')
                added_classes.add(class_name)
                break
        
        # Luego agregar control, entity y database
        role_order = ['control', 'entity', 'database']
        for role in role_order:
            for class_name in self.field_mappings:
                if self._get_role(class_name) == role and class_name not in added_classes:
                    if role == 'control':
                        lines.append(f'control "{class_name}" as {class_name}')
                    elif role == 'database':
                        lines.append(f'database "{class_name}" as {class_name}')
                    else:
                        lines.append(f'entity "{class_name}" as {class_name}')
                    added_classes.add(class_name)
        
        return lines

    def _generate_sequence(self, interactions):
        lines = []
        
        # Encontrar el boundary para iniciar la secuencia
        boundary = next((c for c in self.field_mappings if self._get_role(c) == 'boundary'), None)
        if boundary:
            lines.append(f"Usuario -> {boundary} : [Inicia acción]")
        
        # Agregar interacciones
        for interaction in interactions:
            lines.append(f"{interaction['from']} -> {interaction['to']} : {interaction['message']}")
        
        # Finalizar con respuesta al usuario
        if boundary:
            lines.append(f"{boundary} --> Usuario : [Resultado]")
        
        return lines

    def _get_role(self, class_name):
        for suffix, role in self.role_mapping.items():
            if class_name.endswith(suffix):
                return role
        return 'entity'

    def _find_class_by_position(self, code, pos):
        classes = list(re.finditer(r'public class (\w+)', code))
        for i, class_match in enumerate(classes):
            start = class_match.start()
            end = classes[i+1].start() if i+1 < len(classes) else len(code)
            if start <= pos < end:
                return class_match.group(1)
        return None

    def _resolve_instance_type(self, current_class, instance_name):
        # Resolver campos privados (_service -> Service)
        if instance_name.startswith('_'):
            field_name = instance_name[1:]
            return self.field_mappings[current_class].get(field_name)
        
        # Resolver variables locales (buscar en el contexto)
        return instance_name if instance_name[0].isupper() else None

