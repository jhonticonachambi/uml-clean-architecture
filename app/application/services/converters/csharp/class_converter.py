
# app/application/services/converters/csharp/class_converter.py
import re
from typing import Dict, List, Tuple, Set

class CSharpClassConverter:
    def __init__(self):
        self.classes: Dict[str, Dict] = {}
        self.relationships: List[Tuple] = []
        self.processed_relationships: Set[Tuple] = set()
        self.current_namespace = ""

    def convert(self, code: str) -> str:
        """Convierte código C# a diagrama UML de clases en PlantUML"""
        # Preprocesamiento
        code = self._normalize_code(code)
        
        # Extracción de elementos
        self._extract_namespaces(code)
        self._extract_classes(code)
        self._analyze_relationships()
        
        # Generación UML
        plantuml = self._generate_plantuml()
        return plantuml

    def _normalize_code(self, code: str) -> str:
        """Limpia el código removiendo comentarios y literales de string"""
        # Remove single-line comments
        code = re.sub(r'//.*', '', code)
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)
        # Remove string literals (simplified)
        code = re.sub(r'"[^"]*"', '""', code)
        return code

    def _extract_namespaces(self, code: str):
        """Extrae namespaces para manejar nombres completos"""
        namespace_matches = re.finditer(r'namespace\s+([\w.]+)\s*\{', code)
        for match in namespace_matches:
            self.current_namespace = match.group(1) + "."

    def _extract_classes(self, code: str):
        """Extrae clases, interfaces, structs y sus miembros"""
        class_pattern = re.compile(
            r'(?:public\s+|private\s+|protected\s+|internal\s+|abstract\s+|sealed\s+|static\s+|partial\s+)*'
            r'(class|interface|struct)\s+(\w+)(?:\s*:\s*([\w<>,\s]+))?\s*\{',
            re.MULTILINE
        )
        
        for match in class_pattern.finditer(code):
            class_type = match.group(1)
            class_name = match.group(2)
            base_types = [bt.strip() for bt in match.group(3).split(',')] if match.group(3) else []
            
            full_name = f"{self.current_namespace}{class_name}"
            
            self.classes[full_name] = {
                'type': class_type,
                'base_types': base_types,
                'properties': [],
                'fields': [],
                'methods': [],
                'is_abstract': 'abstract' in match.group(0),
                'is_static': 'static' in match.group(0)
            }
            
            start_idx = match.end()
            class_body = self._extract_balanced_content(code[start_idx:], '{', '}')
            self._parse_class_members(full_name, class_body)

    def _parse_class_members(self, class_name: str, class_body: str):
        """Analiza los miembros de una clase (campos, propiedades, métodos)"""
        # Propiedades (con getters/setters)
        prop_pattern = re.compile(
            r'(public|private|protected|internal)\s+([\w<>,\s]+)\s+(\w+)\s*\{[^}]*\}'
        )
        for match in prop_pattern.finditer(class_body):
            visibility, prop_type, prop_name = match.groups()
            self.classes[class_name]['properties'].append({
                'visibility': visibility,
                'type': prop_type.strip(),
                'name': prop_name
            })

        # Campos
        field_pattern = re.compile(
            r'(public|private|protected|internal)\s+([\w<>,\s]+)\s+(\w+)\s*(?:=|;)'
        )
        for match in field_pattern.finditer(class_body):
            visibility, field_type, field_name = match.groups()
            self.classes[class_name]['fields'].append({
                'visibility': visibility,
                'type': field_type.strip(),
                'name': field_name
            })

        # Métodos
        method_pattern = re.compile(
            r'(public|private|protected|internal|abstract|virtual|override|static)\s+'
            r'([\w<>,\s]+)\s+(\w+)\s*\((.*?)\)\s*(?:where\s+[^{]*)?\{?'
        )
        for match in method_pattern.finditer(class_body):
            modifiers, return_type, method_name, params = match.groups()
            visibility = next(
                (m for m in modifiers.split() 
                 if m in ['public', 'private', 'protected', 'internal']),
                'private'
            )
            self.classes[class_name]['methods'].append({
                'visibility': visibility,
                'return_type': return_type.strip(),
                'name': method_name,
                'parameters': self._parse_parameters(params),
                'is_abstract': 'abstract' in modifiers,
                'is_virtual': 'virtual' in modifiers,
                'is_override': 'override' in modifiers,
                'is_static': 'static' in modifiers
            })

    def _parse_parameters(self, param_str: str) -> List[Dict]:
        """Parsea los parámetros de métodos"""
        params = []
        for p in param_str.split(','):
            p = p.strip()
            if not p:
                continue
            # Handle params with default values
            p = re.sub(r'\s*=\s*.*', '', p)
            parts = re.split(r'\s+', p)
            if len(parts) >= 2:
                type_ = ' '.join(parts[:-1])
                name = parts[-1]
                params.append({'type': type_, 'name': name})
        return params

    def _extract_balanced_content(self, text: str, open_char: str, close_char: str) -> str:
        """Extrae contenido balanceado entre delimitadores"""
        balance = 1
        result = []
        for char in text:
            if char == open_char:
                balance += 1
            elif char == close_char:
                balance -= 1
                if balance == 0:
                    break
            result.append(char)
        return ''.join(result)

    def _analyze_relationships(self):
        """Analiza relaciones entre clases (herencia, asociaciones, etc.)"""
        for class_name, class_info in self.classes.items():
            # Herencia/Implementación
            for base_type in class_info['base_types']:
                base_type = self._resolve_type(base_type)
                if base_type in self.classes:
                    rel_key = (base_type, class_name, 'inheritance')
                    if rel_key not in self.processed_relationships:
                        self.relationships.append((base_type, class_name, 'inheritance', ''))
                        self.processed_relationships.add(rel_key)

            # Asociaciones a través de miembros
            for member in class_info['properties'] + class_info['fields']:
                member_type = self._resolve_type(member['type'])
                if member_type in self.classes:
                    rel_key = (class_name, member_type, 'association', member['name'])
                    if rel_key not in self.processed_relationships:
                        self.relationships.append(rel_key)
                        self.processed_relationships.add(rel_key)

            # Dependencias a través de parámetros de métodos
            for method in class_info['methods']:
                for param in method['parameters']:
                    param_type = self._resolve_type(param['type'])
                    if param_type in self.classes:
                        rel_key = (class_name, param_type, 'dependency', method['name'])
                        if rel_key not in self.processed_relationships:
                            self.relationships.append(rel_key)
                            self.processed_relationships.add(rel_key)

    def _resolve_type(self, type_name: str) -> str:
        """Resuelve nombres de tipo complejos (genéricos, arrays, etc.)"""
        # Remove generic type parameters
        type_name = re.sub(r'<.*>', '', type_name)
        # Remove array brackets
        type_name = re.sub(r'\[\]', '', type_name)
        # Remove nullable marker
        type_name = re.sub(r'\?', '', type_name)
        return type_name.strip()

    def _generate_plantuml(self) -> str:
        """Genera el código PlantUML a partir de las clases y relaciones"""
        plantuml = ["@startuml"]
        
        # Configuración
        plantuml.extend([
            "skinparam class {",
            "  BackgroundColor White",
            "  BorderColor Black",
            "  ArrowColor #444444",
            "}",
            "hide empty members",
            ""
        ])
        
        # Clases
        for class_name, class_info in self.classes.items():
            plantuml.append(self._generate_class_uml(class_name, class_info))
        
        # Relaciones
        plantuml.append("")
        for rel in self.relationships:
            plantuml.append(self._generate_relationship_uml(rel))
        
        plantuml.append("@enduml")
        return '\n'.join(plantuml)

    def _generate_class_uml(self, class_name: str, class_info: Dict) -> str:
        """Genera la definición UML para una clase"""
        class_decl = []
        
        # Modificadores
        if class_info['is_abstract']:
            class_decl.append("abstract ")
        if class_info['is_static']:
            class_decl.append("static ")
            
        # Tipo y nombre
        class_decl.append(f"{class_info['type']} {class_name.split('.')[-1]}")
        
        # Herencia
        if class_info['base_types']:
            bases = [bt.split('.')[-1] for bt in class_info['base_types']]
            class_decl.append(f" extends {', '.join(bases)}")
        
        # Cuerpo de la clase
        class_str = "".join(class_decl) + " {\n"
        
        # Campos
        for field in class_info['fields']:
            vis = self._visibility_to_symbol(field['visibility'])
            class_str += f"    {vis}{field['name']} : {field['type'].split('.')[-1]}\n"
        
        # Propiedades
        for prop in class_info['properties']:
            vis = self._visibility_to_symbol(prop['visibility'])
            class_str += f"    {vis}{prop['name']} : {prop['type'].split('.')[-1]}\n"
        
        # Métodos
        for method in class_info['methods']:
            vis = self._visibility_to_symbol(method['visibility'])
            params = ', '.join(
                f"{p['name']} : {p['type'].split('.')[-1]}" 
                for p in method['parameters']
            )
            modifiers = []
            if method['is_abstract']: modifiers.append("abstract")
            if method['is_virtual']: modifiers.append("virtual")
            if method['is_override']: modifiers.append("override")
            if method['is_static']: modifiers.append("static")
            
            modifier_str = f" {{{','.join(modifiers)}}}" if modifiers else ""
            class_str += (
                f"    {vis}{method['name']}({params}) : "
                f"{method['return_type'].split('.')[-1]}{modifier_str}\n"
            )
        
        class_str += "}"
        return class_str

    def _generate_relationship_uml(self, rel: Tuple) -> str:
        """Genera la definición UML para una relación"""
        source, target, rel_type, label = rel
        source = source.split('.')[-1]
        target = target.split('.')[-1]
        
        if rel_type == 'inheritance':
            return f"{target} <|-- {source}"
        elif rel_type == 'association':
            return f"{source} --> \"{label}\" {target}"
        elif rel_type == 'dependency':
            return f"{source} ..> \"{label}\" {target}"
        return ""

    def _visibility_to_symbol(self, visibility: str) -> str:
        """Convierte modificadores de visibilidad a símbolos UML"""
        return {
            'public': '+',
            'private': '-',
            'protected': '#',
            'internal': '~'
        }.get(visibility.lower(), '~')