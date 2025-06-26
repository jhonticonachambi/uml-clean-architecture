# app/application/services/converters/component_diagram_converter.py
import re
from typing import Dict, List, Set, Tuple
import os

class ComponentDiagramConverter:
    """
    Convertidor genérico para diagramas de componentes UML.
    Analiza estructura de archivos y directorios para generar diagramas de componentes.
    """
    
    def __init__(self):
        self.components: List[Dict] = []
        self.interfaces: List[Dict] = []
        self.dependencies: List[Dict] = []
        self.packages: Set[str] = set()
        
    def convert(self, code: str) -> str:
        """
        Convierte estructura de proyecto/código a diagrama UML de componentes en PlantUML.
        El 'code' puede ser:
        - Estructura de directorios (separada por líneas)
        - Código fuente con imports/includes
        - JSON con configuración de proyecto
        """
        # Detectar tipo de entrada
        if self._is_directory_structure(code):
            self._analyze_directory_structure(code)
        elif self._is_project_config(code):
            self._analyze_project_config(code)
        else:
            self._analyze_source_code(code)
            
        return self._generate_plantuml()
    
    def _is_directory_structure(self, content: str) -> bool:
        """Detecta si el contenido es una estructura de directorios"""
        lines = content.strip().split('\n')
        # Si más del 50% de las líneas contienen '/' o '\' es probablemente estructura de dirs
        path_lines = sum(1 for line in lines if '/' in line or '\\' in line)
        return path_lines > len(lines) * 0.5
    
    def _is_project_config(self, content: str) -> bool:
        """Detecta si el contenido es configuración de proyecto (JSON, YAML, etc.)"""
        content = content.strip()
        return (content.startswith('{') and content.endswith('}')) or \
               'dependencies' in content.lower() or \
               'package.json' in content or \
               'requirements.txt' in content
    
    def _analyze_directory_structure(self, structure: str):
        """Analiza estructura de directorios para extraer componentes"""
        lines = structure.strip().split('\n')
        current_package = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Extraer información del path
            path_info = self._parse_path(line)
            if path_info:
                component_name, package_name, component_type = path_info
                
                # Agregar componente
                self.components.append({
                    'name': component_name,
                    'package': package_name,
                    'type': component_type,
                    'path': line
                })
                
                # Agregar paquete
                if package_name:
                    self.packages.add(package_name)
    
    def _analyze_project_config(self, config: str):
        """Analiza configuración de proyecto para extraer dependencias"""
        # Analizar package.json (JavaScript/Node.js)
        if 'package.json' in config or ('{' in config and 'dependencies' in config):
            self._extract_npm_dependencies(config)
        # Analizar requirements.txt (Python)
        elif 'requirements.txt' in config or self._looks_like_requirements(config):
            self._extract_python_dependencies(config)
        # Analizar pom.xml o build.gradle (Java)
        elif any(keyword in config.lower() for keyword in ['maven', 'gradle', 'dependency']):
            self._extract_java_dependencies(config)
    
    def _analyze_source_code(self, code: str):
        """Analiza código fuente para extraer componentes e interfaces"""
        # Extraer imports/includes
        imports = self._extract_imports(code)
        for imp in imports:
            self.dependencies.append({
                'from': 'MainComponent',
                'to': imp,
                'type': 'uses'
            })
        
        # Extraer clases/módulos como componentes
        components = self._extract_code_components(code)
        self.components.extend(components)
        
        # Extraer interfaces
        interfaces = self._extract_interfaces(code)
        self.interfaces.extend(interfaces)
    
    def _parse_path(self, path: str) -> Tuple[str, str, str]:
        """Parsea un path para extraer nombre de componente, paquete y tipo"""
        # Normalizar separadores
        path = path.replace('\\', '/')
        
        # Remover prefijos comunes
        if path.startswith('./'):
            path = path[2:]
        
        # Separar en partes
        parts = [p for p in path.split('/') if p and p != '.']
        
        if not parts:
            return None
            
        # El último elemento es el archivo/componente
        filename = parts[-1]
        package_parts = parts[:-1]
        
        # Determinar tipo de componente
        component_type = self._determine_component_type(filename)
        
        # Nombre del componente (sin extensión)
        component_name = os.path.splitext(filename)[0]
        if not component_name:
            component_name = filename
            
        # Nombre del paquete
        package_name = '.'.join(package_parts) if package_parts else 'root'
        
        return component_name, package_name, component_type
    
    def _determine_component_type(self, filename: str) -> str:
        """Determina el tipo de componente basado en el nombre del archivo"""
        filename_lower = filename.lower()
        
        # Mapeo de extensiones/patrones a tipos
        type_mapping = {
            # Servicios y APIs
            'service': 'service',
            'api': 'api',
            'controller': 'controller',
            'handler': 'handler',
            
            # Datos y modelos
            'model': 'entity',
            'entity': 'entity',
            'repository': 'repository',
            'dao': 'repository',
            'database': 'database',
            
            # UI y presentación
            'view': 'ui',
            'component': 'ui',
            'page': 'ui',
            'form': 'ui',
            
            # Configuración
            'config': 'configuration',
            'settings': 'configuration',
            
            # Utilidades
            'util': 'utility',
            'helper': 'utility',
            'tool': 'utility',
        }
        
        # Verificar patrones en el nombre
        for pattern, comp_type in type_mapping.items():
            if pattern in filename_lower:
                return comp_type
        
        # Verificar extensiones
        ext = os.path.splitext(filename)[1].lower()
        ext_mapping = {
            '.js': 'module',
            '.py': 'module', 
            '.java': 'class',
            '.cs': 'class',
            '.php': 'module',
            '.html': 'ui',
            '.css': 'style',
            '.json': 'configuration',
            '.xml': 'configuration',
            '.yml': 'configuration',
            '.yaml': 'configuration'
        }
        
        return ext_mapping.get(ext, 'component')
    
    def _extract_imports(self, code: str) -> List[str]:
        """Extrae imports/includes del código"""
        imports = []
        
        # Patrones para diferentes lenguajes
        patterns = [
            r'import\s+(?:.*?\s+from\s+)?["\']([^"\']+)["\']',  # JavaScript/Python
            r'#include\s*[<"]([^>"]+)[>"]',  # C/C++
            r'using\s+([^;]+);',  # C#
            r'import\s+([^;]+);',  # Java
            r'require\s*\(\s*["\']([^"\']+)["\']\s*\)',  # JavaScript require
            r'include\s+["\']([^"\']+)["\']',  # PHP
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, code, re.MULTILINE)
            imports.extend(matches)
        
        return list(set(imports))  # Remover duplicados
    
    def _extract_code_components(self, code: str) -> List[Dict]:
        """Extrae componentes del código (clases, funciones, módulos)"""
        components = []
        
        # Patrones para diferentes tipos de componentes
        patterns = {
            'class': [
                r'class\s+(\w+)',  # Python, Java, C#, JavaScript
                r'public\s+class\s+(\w+)',  # Java, C#
            ],
            'interface': [
                r'interface\s+(\w+)',  # Java, C#, TypeScript
                r'@interface\s+(\w+)',  # Objective-C
            ],
            'function': [
                r'def\s+(\w+)',  # Python
                r'function\s+(\w+)',  # JavaScript
                r'public\s+(?:static\s+)?(?:\w+\s+)?(\w+)\s*\(',  # Java/C# methods
            ]
        }
        
        for comp_type, type_patterns in patterns.items():
            for pattern in type_patterns:
                matches = re.findall(pattern, code, re.MULTILINE)
                for match in matches:
                    components.append({
                        'name': match,
                        'type': comp_type,
                        'package': 'code'
                    })
        
        return components
    
    def _extract_interfaces(self, code: str) -> List[Dict]:
        """Extrae interfaces del código"""
        interfaces = []
        
        # Patrones para interfaces
        interface_patterns = [
            r'interface\s+(\w+)\s*{([^}]+)}',  # TypeScript, Java, C#
            r'@protocol\s+(\w+)',  # Objective-C
            r'trait\s+(\w+)',  # PHP, Rust
        ]
        
        for pattern in interface_patterns:
            matches = re.findall(pattern, code, re.MULTILINE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    name, body = match
                    methods = self._extract_interface_methods(body)
                else:
                    name = match
                    methods = []
                
                interfaces.append({
                    'name': name,
                    'methods': methods,
                    'type': 'interface'
                })
        
        return interfaces
    
    def _extract_interface_methods(self, interface_body: str) -> List[str]:
        """Extrae métodos de una interfaz"""
        method_patterns = [
            r'(\w+)\s*\([^)]*\)',  # Métodos generales
            r'public\s+(?:abstract\s+)?(?:\w+\s+)?(\w+)\s*\(',  # Java/C#
        ]
        
        methods = []
        for pattern in method_patterns:
            matches = re.findall(pattern, interface_body)
            methods.extend(matches)
        
        return list(set(methods))
    
    def _extract_npm_dependencies(self, config: str):
        """Extrae dependencias de package.json"""
        # Buscar bloques de dependencies
        dep_pattern = r'"dependencies"\s*:\s*{([^}]+)}'
        matches = re.findall(dep_pattern, config)
        
        for deps_block in matches:
            # Extraer nombres de paquetes individuales
            pkg_pattern = r'"([^"]+)"\s*:'
            packages = re.findall(pkg_pattern, deps_block)
            
            for pkg in packages:
                self.components.append({
                    'name': pkg,
                    'type': 'external_library',
                    'package': 'node_modules'
                })
    
    def _extract_python_dependencies(self, config: str):
        """Extrae dependencias de requirements.txt"""
        lines = config.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Extraer nombre del paquete (sin versión)
                pkg_name = re.split(r'[>=<!=]', line)[0].strip()
                if pkg_name:
                    self.components.append({
                        'name': pkg_name,
                        'type': 'external_library',
                        'package': 'pip_packages'
                    })
    
    def _extract_java_dependencies(self, config: str):
        """Extrae dependencias de Maven/Gradle"""
        # Maven dependencies
        maven_pattern = r'<artifactId>([^<]+)</artifactId>'
        maven_deps = re.findall(maven_pattern, config)
        
        # Gradle dependencies
        gradle_pattern = r'implementation\s+["\']([^:"\']+):'
        gradle_deps = re.findall(gradle_pattern, config)
        
        all_deps = maven_deps + gradle_deps
        for dep in all_deps:
            self.components.append({
                'name': dep,
                'type': 'external_library',
                'package': 'maven_central'
            })
    
    def _looks_like_requirements(self, content: str) -> bool:
        """Verifica si el contenido parece un archivo requirements.txt"""
        lines = content.strip().split('\n')
        # Si más del 70% de las líneas parecen dependencias de Python
        dep_lines = sum(1 for line in lines 
                       if line.strip() and not line.strip().startswith('#') 
                       and ('==' in line or '>=' in line or line.replace('-', '').replace('_', '').isalnum()))
        return dep_lines > len(lines) * 0.7
    
    def _generate_plantuml(self) -> str:
        """Genera el código PlantUML para el diagrama de componentes"""
        plantuml = ["@startuml"]
        
        # Configuración de estilo
        plantuml.extend([
            "!theme plain",
            "skinparam component {",
            "  BackgroundColor White",
            "  BorderColor Black",
            "  ArrowColor #444444",
            "}",
            "skinparam package {",
            "  BackgroundColor #F0F0F0",
            "  BorderColor #888888",
            "}",
            ""
        ])
        
        # Generar paquetes
        package_components = {}
        for component in self.components:
            pkg = component.get('package', 'default')
            if pkg not in package_components:
                package_components[pkg] = []
            package_components[pkg].append(component)
        
        # Generar componentes agrupados por paquete
        for package_name, components in package_components.items():
            if package_name and package_name != 'default':
                plantuml.append(f'package "{package_name}" {{')
                
            for component in components:
                comp_name = component['name']
                comp_type = component.get('type', 'component')
                
                # Iconos según el tipo
                icon = self._get_component_icon(comp_type)
                plantuml.append(f'  [{comp_name}] as {comp_name} {icon}')
            
            if package_name and package_name != 'default':
                plantuml.append('}')
                plantuml.append('')
        
        # Generar interfaces
        for interface in self.interfaces:
            interface_name = interface['name']
            plantuml.append(f'interface {interface_name}')
            
            # Agregar métodos si los hay
            methods = interface.get('methods', [])
            if methods:
                plantuml.append(f'{interface_name} : {methods[0]}()')
                for method in methods[1:3]:  # Limitar a 3 métodos para claridad
                    plantuml.append(f'{interface_name} : {method}()')
                if len(methods) > 3:
                    plantuml.append(f'{interface_name} : ...')
        
        if self.interfaces:
            plantuml.append('')
        
        # Generar dependencias
        for dependency in self.dependencies:
            from_comp = dependency['from']
            to_comp = dependency['to']
            dep_type = dependency.get('type', 'uses')
            
            arrow = '-->' if dep_type == 'uses' else '..>'
            plantuml.append(f'{from_comp} {arrow} {to_comp}')
        
        # Generar relaciones automáticas entre componentes del mismo paquete
        for package_name, components in package_components.items():
            if len(components) > 1:
                # Conectar componentes relacionados (heurística simple)
                for i, comp1 in enumerate(components):
                    for comp2 in components[i+1:]:
                        if self._are_related(comp1, comp2):
                            plantuml.append(f"{comp1['name']} --> {comp2['name']}")
        
        plantuml.append("@enduml")
        return '\n'.join(plantuml)
    
    def _get_component_icon(self, component_type: str) -> str:
        """Retorna el icono apropiado para el tipo de componente"""
        icons = {
            'service': '<<service>>',
            'api': '<<API>>',
            'controller': '<<controller>>',
            'entity': '<<entity>>',
            'repository': '<<repository>>',
            'database': '<<database>>',
            'ui': '<<UI>>',
            'configuration': '<<config>>',
            'utility': '<<utility>>',
            'external_library': '<<library>>',
            'interface': '<<interface>>',
            'module': '<<module>>',
            'class': '<<class>>'
        }
        return icons.get(component_type, '<<component>>')
    
    def _are_related(self, comp1: Dict, comp2: Dict) -> bool:
        """Determina si dos componentes están relacionados (heurística)"""
        # Componentes del mismo tipo suelen estar relacionados
        if comp1.get('type') == comp2.get('type'):
            return False  # Evitar muchas conexiones del mismo tipo
        
        # Patrones de relación común
        relations = [
            ('controller', 'service'),
            ('service', 'repository'),
            ('repository', 'entity'),
            ('ui', 'controller'),
            ('api', 'service')
        ]
        
        comp1_type = comp1.get('type', '')
        comp2_type = comp2.get('type', '')
        
        return (comp1_type, comp2_type) in relations or (comp2_type, comp1_type) in relations
