# app/application/services/converters/php/class_converter.py
import re
from typing import Dict, List, Tuple, Set

class PHPClassConverter:
    def __init__(self):
        self.classes: Dict[str, Dict] = {}
        self.relationships: List[Tuple] = []
        self.processed_relationships: Set[Tuple] = set()
        self.current_namespace = ""

    def convert(self, code: str) -> str:
        """Convierte código PHP a diagrama UML de clases en PlantUML"""
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
        # Remove hash comments
        code = re.sub(r'#.*', '', code)
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)
        # Remove string literals (simplified)
        code = re.sub(r'"[^"]*"', '""', code)
        code = re.sub(r"'[^']*'", "''", code)
        return code

    def _extract_namespaces(self, code: str):
        """Extrae namespaces para manejar nombres completos"""
        namespace_matches = re.finditer(r'namespace\s+([\w\\]+)\s*;', code)
        for match in namespace_matches:
            self.current_namespace = match.group(1) + "\\"

    def _extract_classes(self, code: str):
        """Extrae clases, interfaces, traits y sus miembros"""
        class_pattern = re.compile(
            r'(?:abstract\s+|final\s+)?(class|interface|trait)\s+(\w+)(?:\s+extends\s+([\w\\]+))?(?:\s+implements\s+([\w\\,\s]+))?\s*\{',
            re.MULTILINE
        )
        
        for match in class_pattern.finditer(code):
            class_type = match.group(1)
            class_name = match.group(2)
            extends_class = match.group(3)
            implements_interfaces = match.group(4)
            
            full_name = f"{self.current_namespace}{class_name}"
            
            base_types = []
            if extends_class:
                base_types.append(extends_class.strip())
            if implements_interfaces:
                interfaces = [iface.strip() for iface in implements_interfaces.split(',')]
                base_types.extend(interfaces)
            
            self.classes[full_name] = {
                'type': class_type,
                'base_types': base_types,
                'properties': [],
                'methods': [],
                'constants': [],
                'is_abstract': 'abstract' in match.group(0),
                'is_final': 'final' in match.group(0)
            }
            
            start_idx = match.end()
            class_body = self._extract_balanced_content(code[start_idx:], '{', '}')
            self._parse_class_members(full_name, class_body)

    def _parse_class_members(self, class_name: str, class_body: str):
        """Analiza los miembros de una clase (propiedades, métodos, constantes)"""
        # Constantes
        const_pattern = re.compile(
            r'(?:public\s+|private\s+|protected\s+)?const\s+(\w+)\s*=',
            re.MULTILINE
        )
        for match in const_pattern.finditer(class_body):
            const_name = match.group(1)
            self.classes[class_name]['constants'].append({
                'name': const_name,
                'visibility': 'public'  # Las constantes son públicas por defecto
            })

        # Propiedades
        prop_pattern = re.compile(
            r'(public|private|protected)(?:\s+static)?\s+(?:\?\w+\s+)?\$(\w+)',
            re.MULTILINE
        )
        for match in prop_pattern.finditer(class_body):
            visibility = match.group(1)
            prop_name = match.group(2)
            is_static = 'static' in match.group(0)
            self.classes[class_name]['properties'].append({
                'visibility': visibility,
                'name': prop_name,
                'is_static': is_static
            })

        # Métodos
        method_pattern = re.compile(
            r'(public|private|protected)(?:\s+static)?(?:\s+abstract)?(?:\s+final)?\s+function\s+(\w+)\s*\((.*?)\)',
            re.MULTILINE | re.DOTALL
        )
        for match in method_pattern.finditer(class_body):
            visibility = match.group(1)
            method_name = match.group(2)
            params = match.group(3)
            
            modifiers = match.group(0)
            is_static = 'static' in modifiers
            is_abstract = 'abstract' in modifiers
            is_final = 'final' in modifiers
            
            self.classes[class_name]['methods'].append({
                'visibility': visibility,
                'name': method_name,
                'parameters': self._parse_parameters(params),
                'is_static': is_static,
                'is_abstract': is_abstract,
                'is_final': is_final
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
            # Extract type and variable name
            parts = re.split(r'\s+', p)
            if len(parts) >= 1:
                var_name = parts[-1].lstrip('$')
                type_hint = ' '.join(parts[:-1]) if len(parts) > 1 else 'mixed'
                params.append({'type': type_hint, 'name': var_name})
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
        """Analiza relaciones entre clases (herencia, implementación, etc.)"""
        for class_name, class_info in self.classes.items():
            # Herencia/Implementación
            for base_type in class_info['base_types']:
                base_type = self._resolve_type(base_type)
                if base_type in self.classes:
                    rel_key = (base_type, class_name, 'inheritance')
                    if rel_key not in self.processed_relationships:
                        self.relationships.append((base_type, class_name, 'inheritance', ''))
                        self.processed_relationships.add(rel_key)

    def _resolve_type(self, type_name: str) -> str:
        """Resuelve nombres de tipo complejos"""
        # Remove leading backslash
        type_name = type_name.lstrip('\\')
        # Add current namespace if not fully qualified
        if '\\' not in type_name and self.current_namespace:
            type_name = f"{self.current_namespace}{type_name}"
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
        if class_info['is_final']:
            class_decl.append("final ")
            
        # Tipo y nombre
        simple_name = class_name.split('\\')[-1]
        class_decl.append(f"{class_info['type']} {simple_name}")
        
        # Cuerpo de la clase
        class_str = "".join(class_decl) + " {\n"
        
        # Constantes
        for const in class_info['constants']:
            class_str += f"    +{const['name']} : const\n"
        
        # Propiedades
        for prop in class_info['properties']:
            vis = self._visibility_to_symbol(prop['visibility'])
            static_marker = "{static}" if prop['is_static'] else ""
            class_str += f"    {vis}{prop['name']} {static_marker}\n"
        
        # Métodos
        for method in class_info['methods']:
            vis = self._visibility_to_symbol(method['visibility'])
            params = ', '.join(
                f"{p['name']} : {p['type']}" 
                for p in method['parameters']
            )
            
            modifiers = []
            if method['is_static']: modifiers.append("static")
            if method['is_abstract']: modifiers.append("abstract")
            if method['is_final']: modifiers.append("final")
            
            modifier_str = f" {{{','.join(modifiers)}}}" if modifiers else ""
            class_str += f"    {vis}{method['name']}({params}){modifier_str}\n"
        
        class_str += "}"
        return class_str

    def _generate_relationship_uml(self, rel: Tuple) -> str:
        """Genera la definición UML para una relación"""
        source, target, rel_type, label = rel
        source = source.split('\\')[-1]
        target = target.split('\\')[-1]
        
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
            'protected': '#'
        }.get(visibility.lower(), '+')