# app/application/services/converters/javascript/class_converter.py
import re
import ast
from typing import List, Dict, Set, Tuple


class JavaScriptClassConverter:
    """
    Convertidor de código JavaScript/TypeScript a diagramas de clases UML PlantUML.
    Soporta ES6+, TypeScript, interfaces, decoradores y más.
    """
    
    def __init__(self):
        self.classes = {}
        self.interfaces = {}
        self.enums = {}
        self.relationships = []
        self.imports = set()
        
    def convert_to_plantuml(self, code: str) -> str:
        """
        Convierte código JavaScript/TypeScript a diagrama de clases PlantUML.
        
        Args:
            code: Código fuente de JavaScript/TypeScript
            
        Returns:
            Diagrama PlantUML como string
        """
        self._reset()
        self._extract_imports(code)
        self._extract_classes(code)
        self._extract_interfaces(code)
        self._extract_enums(code)
        self._extract_relationships(code)
        
        return self._generate_plantuml()
    
    def convert(self, code: str) -> str:
        """
        Método de compatibilidad para el protocolo BaseConverter.
        Delega a convert_to_plantuml.
        """
        return self.convert_to_plantuml(code)
    
    def _reset(self):
        """Reinicia el estado del convertidor."""
        self.classes = {}
        self.interfaces = {}
        self.enums = {}
        self.relationships = []
        self.imports = set()
    
    def _extract_imports(self, code: str):
        """Extrae imports/requires del código."""
        # ES6 imports
        import_pattern = r'import\s+(?:\{[^}]+\}|\*\s+as\s+\w+|\w+)?\s*from\s*[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(import_pattern, code):
            self.imports.add(match.group(1))
        
        # CommonJS requires
        require_pattern = r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        for match in re.finditer(require_pattern, code):
            self.imports.add(match.group(1))
    
    def _extract_classes(self, code: str):
        """Extrae clases del código JavaScript/TypeScript."""
        # Patrón para clases ES6/TypeScript
        class_pattern = r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w\s,]+))?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        
        for match in re.finditer(class_pattern, code, re.MULTILINE | re.DOTALL):
            class_name = match.group(1)
            extends = match.group(2)
            implements = match.group(3)
            class_body = match.group(4)
            
            class_info = {
                'name': class_name,
                'type': 'class',
                'extends': extends,
                'implements': [imp.strip() for imp in implements.split(',')] if implements else [],
                'properties': self._extract_properties(class_body),
                'methods': self._extract_methods(class_body),
                'constructors': self._extract_constructors(class_body),
                'decorators': self._extract_decorators_before_class(code, class_name),
                'visibility': self._determine_class_visibility(code, class_name),
                'is_abstract': 'abstract' in match.group(0)
            }
            
            self.classes[class_name] = class_info
            
            # Agregar relaciones de herencia
            if extends:
                self.relationships.append({
                    'type': 'inheritance',
                    'from': class_name,
                    'to': extends
                })
            
            # Agregar relaciones de implementación
            for interface in class_info['implements']:
                self.relationships.append({
                    'type': 'implementation',
                    'from': class_name,
                    'to': interface.strip()
                })
    
    def _extract_interfaces(self, code: str):
        """Extrae interfaces de TypeScript."""
        interface_pattern = r'(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+([\w\s,]+))?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        
        for match in re.finditer(interface_pattern, code, re.MULTILINE | re.DOTALL):
            interface_name = match.group(1)
            extends = match.group(2)
            interface_body = match.group(3)
            
            interface_info = {
                'name': interface_name,
                'type': 'interface',
                'extends': [ext.strip() for ext in extends.split(',')] if extends else [],
                'properties': self._extract_interface_properties(interface_body),
                'methods': self._extract_interface_methods(interface_body)
            }
            
            self.interfaces[interface_name] = interface_info
            
            # Agregar relaciones de herencia de interfaces
            if extends:
                for parent in extends.split(','):
                    self.relationships.append({
                        'type': 'inheritance',
                        'from': interface_name,
                        'to': parent.strip()
                    })
    
    def _extract_enums(self, code: str):
        """Extrae enums de TypeScript."""
        enum_pattern = r'(?:export\s+)?enum\s+(\w+)\s*\{([^}]+)\}'
        
        for match in re.finditer(enum_pattern, code):
            enum_name = match.group(1)
            enum_body = match.group(2)
            
            values = []
            for line in enum_body.split(','):
                line = line.strip()
                if line and not line.startswith('//'):
                    if '=' in line:
                        name = line.split('=')[0].strip()
                        value = line.split('=')[1].strip()
                        values.append(f"{name} = {value}")
                    else:
                        values.append(line)
            
            self.enums[enum_name] = {
                'name': enum_name,
                'type': 'enum',
                'values': values
            }
    
    def _extract_properties(self, class_body: str) -> List[Dict]:
        """Extrae propiedades de una clase."""
        properties = []
        
        # Propiedades TypeScript con tipos
        ts_property_pattern = r'(?:(private|protected|public|readonly)\s+)?(\w+)(?:\?)?:\s*([^;=\n]+)(?:\s*=\s*([^;\n]+))?'
        for match in re.finditer(ts_property_pattern, class_body):
            visibility = match.group(1) or 'public'
            name = match.group(2)
            prop_type = match.group(3).strip()
            default_value = match.group(4)
            
            properties.append({
                'name': name,
                'type': prop_type,
                'visibility': visibility,
                'default_value': default_value.strip() if default_value else None,
                'is_static': False,
                'decorators': []
            })
        
        # Propiedades JavaScript con this.
        js_property_pattern = r'this\.(\w+)\s*=\s*([^;\n]+)'
        for match in re.finditer(js_property_pattern, class_body):
            name = match.group(1)
            value = match.group(2).strip()
            
            # Evitar duplicados con propiedades TypeScript
            if not any(prop['name'] == name for prop in properties):
                properties.append({
                    'name': name,
                    'type': self._infer_type_from_value(value),
                    'visibility': 'public',
                    'default_value': value,
                    'is_static': False,
                    'decorators': []
                })
        
        # Propiedades estáticas
        static_pattern = r'static\s+(?:(private|protected|public)\s+)?(\w+)(?:\?)?(?::\s*([^;=\n]+))?(?:\s*=\s*([^;\n]+))?'
        for match in re.finditer(static_pattern, class_body):
            visibility = match.group(1) or 'public'
            name = match.group(2)
            prop_type = match.group(3) or 'any'
            default_value = match.group(4)
            
            properties.append({
                'name': name,
                'type': prop_type.strip(),
                'visibility': visibility,
                'default_value': default_value.strip() if default_value else None,
                'is_static': True,
                'decorators': []
            })
        
        return properties
    
    def _extract_methods(self, class_body: str) -> List[Dict]:
        """Extrae métodos de una clase."""
        methods = []
        
        # Métodos ES6/TypeScript
        method_pattern = r'(?:(private|protected|public|static)\s+)?(?:(async)\s+)?(\w+)\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?\s*\{'
        
        for match in re.finditer(method_pattern, class_body):
            visibility = match.group(1) or 'public'
            is_async = match.group(2) is not None
            is_static = 'static' in (match.group(1) or '')
            name = match.group(3)
            params = match.group(4)
            return_type = match.group(5)
            
            # Saltar constructores
            if name == 'constructor':
                continue
            
            parameters = self._parse_parameters(params)
            
            methods.append({
                'name': name,
                'visibility': visibility.replace('static', '').strip() or 'public',
                'parameters': parameters,
                'return_type': return_type.strip() if return_type else 'void',
                'is_static': is_static,
                'is_async': is_async,
                'is_abstract': False,
                'decorators': []
            })
        
        # Métodos con decoradores
        decorator_method_pattern = r'(@\w+(?:\([^)]*\))?)\s*(?:(private|protected|public|static)\s+)?(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(decorator_method_pattern, class_body):
            decorator = match.group(1)
            visibility = match.group(2) or 'public'
            name = match.group(3)
            params = match.group(4)
            
            # Buscar si ya existe el método y agregar decorador
            for method in methods:
                if method['name'] == name:
                    method['decorators'].append(decorator)
                    break
        
        return methods
    
    def _extract_constructors(self, class_body: str) -> List[Dict]:
        """Extrae constructores de una clase."""
        constructors = []
        
        constructor_pattern = r'constructor\s*\(([^)]*)\)\s*\{'
        for match in re.finditer(constructor_pattern, class_body):
            params = match.group(1)
            parameters = self._parse_parameters(params)
            
            constructors.append({
                'parameters': parameters,
                'visibility': 'public'
            })
        
        return constructors
    
    def _extract_interface_properties(self, interface_body: str) -> List[Dict]:
        """Extrae propiedades de una interface."""
        properties = []
        
        property_pattern = r'(?:(readonly)\s+)?(\w+)(\?)?:\s*([^;\n]+)'
        for match in re.finditer(property_pattern, interface_body):
            is_readonly = match.group(1) is not None
            name = match.group(2)
            is_optional = match.group(3) is not None
            prop_type = match.group(4).strip()
            
            properties.append({
                'name': name,
                'type': prop_type,
                'is_optional': is_optional,
                'is_readonly': is_readonly
            })
        
        return properties
    
    def _extract_interface_methods(self, interface_body: str) -> List[Dict]:
        """Extrae métodos de una interface."""
        methods = []
        
        method_pattern = r'(\w+)\s*\(([^)]*)\)(?:\s*:\s*([^;\n]+))?'
        for match in re.finditer(method_pattern, interface_body):
            name = match.group(1)
            params = match.group(2)
            return_type = match.group(3)
            
            parameters = self._parse_parameters(params)
            
            methods.append({
                'name': name,
                'parameters': parameters,
                'return_type': return_type.strip() if return_type else 'void'
            })
        
        return methods
    
    def _parse_parameters(self, params_str: str) -> List[Dict]:
        """Parsea parámetros de métodos."""
        parameters = []
        
        if not params_str.strip():
            return parameters
        
        # TypeScript parameters with types
        ts_param_pattern = r'(?:(\.\.\.))?\s*(\w+)(\?)?(?:\s*:\s*([^,=]+))?(?:\s*=\s*([^,]+))?'
        
        for param in params_str.split(','):
            param = param.strip()
            if not param:
                continue
            
            match = re.match(ts_param_pattern, param)
            if match:
                is_rest = match.group(1) is not None
                name = match.group(2)
                is_optional = match.group(3) is not None
                param_type = match.group(4)
                default_value = match.group(5)
                
                parameters.append({
                    'name': name,
                    'type': param_type.strip() if param_type else 'any',
                    'is_optional': is_optional or default_value is not None,
                    'default_value': default_value.strip() if default_value else None,
                    'is_rest': is_rest
                })
            else:
                # Fallback para parámetros simples
                parameters.append({
                    'name': param,
                    'type': 'any',
                    'is_optional': False,
                    'default_value': None,
                    'is_rest': False
                })
        
        return parameters
    
    def _extract_decorators_before_class(self, code: str, class_name: str) -> List[str]:
        """Extrae decoradores antes de una clase."""
        decorators = []
        
        # Buscar decoradores antes de la declaración de clase
        class_pattern = rf'(@\w+(?:\([^)]*\))?(?:\s*@\w+(?:\([^)]*\))?)*)\s*(?:export\s+)?(?:abstract\s+)?class\s+{class_name}'
        match = re.search(class_pattern, code, re.MULTILINE)
        
        if match:
            decorator_text = match.group(1)
            decorator_pattern = r'@(\w+)(?:\(([^)]*)\))?'
            for dec_match in re.finditer(decorator_pattern, decorator_text):
                decorator_name = dec_match.group(1)
                decorator_args = dec_match.group(2)
                
                if decorator_args:
                    decorators.append(f"@{decorator_name}({decorator_args})")
                else:
                    decorators.append(f"@{decorator_name}")
        
        return decorators
    
    def _determine_class_visibility(self, code: str, class_name: str) -> str:
        """Determina la visibilidad de una clase."""
        if f'export class {class_name}' in code or f'export abstract class {class_name}' in code:
            return 'public'
        return 'package'
    
    def _infer_type_from_value(self, value: str) -> str:
        """Infiere el tipo de una propiedad basado en su valor."""
        value = value.strip()
        
        if value.startswith('"') or value.startswith("'") or value.startswith('`'):
            return 'string'
        elif value in ['true', 'false']:
            return 'boolean'
        elif value.isdigit() or re.match(r'^\d+\.\d+$', value):
            return 'number'
        elif value.startswith('[') and value.endswith(']'):
            return 'Array'
        elif value.startswith('{') and value.endswith('}'):
            return 'object'
        elif value == 'null':
            return 'null'
        elif value == 'undefined':
            return 'undefined'
        else:
            return 'any'
    
    def _extract_relationships(self, code: str):
        """Extrae relaciones adicionales del código."""
        # Composición y agregación basada en propiedades
        for class_name, class_info in self.classes.items():
            for prop in class_info['properties']:
                prop_type = prop['type']
                
                # Si la propiedad es de un tipo que es otra clase
                if prop_type in self.classes or prop_type in self.interfaces:
                    self.relationships.append({
                        'type': 'composition',
                        'from': class_name,
                        'to': prop_type,
                        'label': prop['name']
                    })
                
                # Arrays de otros tipos
                array_match = re.match(r'(\w+)\[\]|Array<(\w+)>', prop_type)
                if array_match:
                    target_type = array_match.group(1) or array_match.group(2)
                    if target_type in self.classes or target_type in self.interfaces:
                        self.relationships.append({
                            'type': 'aggregation',
                            'from': class_name,
                            'to': target_type,
                            'label': prop['name']
                        })
    
    def _generate_plantuml(self) -> str:
        """Genera el código PlantUML."""
        uml_lines = ['@startuml', '']
        
        # Configuración
        uml_lines.extend([
            '!define RECTANGLE class',
            'skinparam classAttributeIconSize 0',
            'skinparam monochrome true',
            'skinparam packageStyle rectangle',
            ''
        ])
        
        # Enums
        for enum_name, enum_info in self.enums.items():
            uml_lines.append(f'enum {enum_name} {{')
            for value in enum_info['values']:
                uml_lines.append(f'  {value}')
            uml_lines.extend(['}', ''])
        
        # Interfaces
        for interface_name, interface_info in self.interfaces.items():
            uml_lines.append(f'interface {interface_name} {{')
            
            # Propiedades de la interface
            for prop in interface_info['properties']:
                readonly = 'readonly ' if prop.get('is_readonly') else ''
                optional = '?' if prop.get('is_optional') else ''
                uml_lines.append(f'  +{readonly}{prop["name"]}{optional}: {prop["type"]}')
            
            if interface_info['properties'] and interface_info['methods']:
                uml_lines.append('  --')
            
            # Métodos de la interface
            for method in interface_info['methods']:
                params = ', '.join([f'{p["name"]}: {p["type"]}' for p in method['parameters']])
                uml_lines.append(f'  +{method["name"]}({params}): {method["return_type"]}')
            
            uml_lines.extend(['}', ''])
        
        # Clases
        for class_name, class_info in self.classes.items():
            # Estereotipos y decoradores
            stereotypes = []
            if class_info.get('is_abstract'):
                stereotypes.append('abstract')
            if class_info.get('decorators'):
                for decorator in class_info['decorators']:
                    stereotypes.append(decorator)
            
            if stereotypes:
                stereotype_str = ' <<' + ', '.join(stereotypes) + '>>'
            else:
                stereotype_str = ''
            
            uml_lines.append(f'class {class_name}{stereotype_str} {{')
            
            # Propiedades
            static_props = [p for p in class_info['properties'] if p.get('is_static')]
            instance_props = [p for p in class_info['properties'] if not p.get('is_static')]
            
            # Propiedades estáticas primero
            for prop in static_props:
                visibility = self._convert_visibility(prop['visibility'])
                decorators_str = ' '.join(prop.get('decorators', []))
                if decorators_str:
                    decorators_str = decorators_str + ' '
                uml_lines.append(f'  {visibility}{{static}} {decorators_str}{prop["name"]}: {prop["type"]}')
            
            # Propiedades de instancia
            for prop in instance_props:
                visibility = self._convert_visibility(prop['visibility'])
                decorators_str = ' '.join(prop.get('decorators', []))
                if decorators_str:
                    decorators_str = decorators_str + ' '
                uml_lines.append(f'  {visibility}{decorators_str}{prop["name"]}: {prop["type"]}')
            
            # Separador si hay propiedades y métodos
            if (class_info['properties'] or class_info['constructors']) and class_info['methods']:
                uml_lines.append('  --')
            
            # Constructores
            for constructor in class_info['constructors']:
                params = ', '.join([f'{p["name"]}: {p["type"]}' for p in constructor['parameters']])
                uml_lines.append(f'  +{class_name}({params})')
            
            # Métodos estáticos primero
            static_methods = [m for m in class_info['methods'] if m.get('is_static')]
            instance_methods = [m for m in class_info['methods'] if not m.get('is_static')]
            
            for method in static_methods:
                visibility = self._convert_visibility(method['visibility'])
                async_prefix = 'async ' if method.get('is_async') else ''
                decorators_str = ' '.join(method.get('decorators', []))
                if decorators_str:
                    decorators_str = decorators_str + ' '
                params = ', '.join([f'{p["name"]}: {p["type"]}' for p in method['parameters']])
                uml_lines.append(f'  {visibility}{{static}} {decorators_str}{async_prefix}{method["name"]}({params}): {method["return_type"]}')
            
            # Métodos de instancia
            for method in instance_methods:
                visibility = self._convert_visibility(method['visibility'])
                async_prefix = 'async ' if method.get('is_async') else ''
                abstract_prefix = '{abstract} ' if method.get('is_abstract') else ''
                decorators_str = ' '.join(method.get('decorators', []))
                if decorators_str:
                    decorators_str = decorators_str + ' '
                params = ', '.join([f'{p["name"]}: {p["type"]}' for p in method['parameters']])
                uml_lines.append(f'  {visibility}{abstract_prefix}{decorators_str}{async_prefix}{method["name"]}({params}): {method["return_type"]}')
            
            uml_lines.extend(['}', ''])
        
        # Relaciones
        for rel in self.relationships:
            if rel['type'] == 'inheritance':
                uml_lines.append(f'{rel["to"]} <|-- {rel["from"]}')
            elif rel['type'] == 'implementation':
                uml_lines.append(f'{rel["to"]} <|.. {rel["from"]}')
            elif rel['type'] == 'composition':
                label = f' : {rel["label"]}' if 'label' in rel else ''
                uml_lines.append(f'{rel["from"]} *-- {rel["to"]}{label}')
            elif rel['type'] == 'aggregation':
                label = f' : {rel["label"]}' if 'label' in rel else ''
                uml_lines.append(f'{rel["from"]} o-- {rel["to"]}{label}')
            elif rel['type'] == 'association':
                label = f' : {rel["label"]}' if 'label' in rel else ''
                uml_lines.append(f'{rel["from"]} -- {rel["to"]}{label}')
        
        uml_lines.extend(['', '@enduml'])
        
        return '\n'.join(uml_lines)
    
    def _convert_visibility(self, visibility: str) -> str:
        """Convierte visibilidad a símbolos PlantUML."""
        visibility_map = {
            'public': '+',
            'private': '-',
            'protected': '#',
            'package': '~'
        }
        return visibility_map.get(visibility, '+')