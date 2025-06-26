# app/application/services/converters/package_diagram_converter.py
import re
from typing import Dict, List, Set, Tuple
import os
from collections import defaultdict

class PackageDiagramConverter:
    """
    Convertidor genérico para diagramas de paquetes UML.
    Analiza estructura de directorios y dependencias para generar diagramas de paquetes.
    """
    
    def __init__(self):
        self.packages: Dict[str, Dict] = {}
        self.dependencies: List[Dict] = []
        self.hierarchies: Dict[str, List[str]] = defaultdict(list)
        self.imports_map: Dict[str, Set[str]] = defaultdict(set)
        
    def convert(self, code: str) -> str:
        """
        Convierte estructura de proyecto/código a diagrama UML de paquetes en PlantUML.
        El 'code' puede ser:
        - Estructura de directorios (separada por líneas)
        - Múltiples archivos con imports (separados por ---FILE--- markers)
        - Configuración de proyecto con dependencias
        """
        # Limpiar estado anterior
        self.packages.clear()
        self.dependencies.clear()
        self.hierarchies.clear()
        self.imports_map.clear()
        
        # Detectar tipo de entrada y procesar
        if '---FILE---' in code:
            self._analyze_multiple_files(code)
        elif self._is_directory_structure(code):
            self._analyze_directory_structure(code)
        elif self._is_project_config(code):
            self._analyze_project_dependencies(code)
        else:
            self._analyze_single_file(code)
            
        # Generar dependencias entre paquetes
        self._generate_package_dependencies()
        
        return self._generate_plantuml()
    
    def _is_directory_structure(self, content: str) -> bool:
        """Detecta si el contenido es una estructura de directorios"""
        lines = content.strip().split('\n')
        path_lines = sum(1 for line in lines if '/' in line or '\\' in line or line.strip().endswith('/'))
        return path_lines > len(lines) * 0.4
    
    def _is_project_config(self, content: str) -> bool:
        """Detecta si el contenido es configuración de proyecto"""
        return any(keyword in content.lower() for keyword in [
            'package.json', 'requirements.txt', 'pom.xml', 'build.gradle',
            'composer.json', 'dependencies', 'imports'
        ])
    
    def _analyze_directory_structure(self, structure: str):
        """Analiza estructura de directorios para crear jerarquía de paquetes"""
        lines = structure.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parsear el path
            path_info = self._parse_directory_path(line)
            if path_info:
                self._add_package_from_path(path_info)
    
    def _analyze_multiple_files(self, content: str):
        """Analiza múltiples archivos separados por markers"""
        files = content.split('---FILE---')
        
        for file_content in files:
            file_content = file_content.strip()
            if not file_content:
                continue
                
            # Extraer nombre del archivo (primera línea después del marker)
            lines = file_content.split('\n')
            if lines:
                filename = lines[0].strip()
                file_code = '\n'.join(lines[1:]) if len(lines) > 1 else ''
                self._analyze_file_imports(filename, file_code)
    
    def _analyze_single_file(self, code: str):
        """Analiza un solo archivo para extraer imports"""
        self._analyze_file_imports('main', code)
    
    def _analyze_project_dependencies(self, config: str):
        """Analiza configuración de proyecto para extraer dependencias externas"""
        if 'package.json' in config.lower() or ('{' in config and 'dependencies' in config):
            self._extract_npm_packages(config)
        elif 'requirements.txt' in config.lower() or self._looks_like_requirements(config):
            self._extract_python_packages(config)
        elif any(keyword in config.lower() for keyword in ['maven', 'gradle', 'pom.xml']):
            self._extract_java_packages(config)
        elif 'composer.json' in config.lower():
            self._extract_php_packages(config)
    
    def _parse_directory_path(self, path: str) -> Tuple[str, List[str], bool]:
        """
        Parsea un path de directorio.
        Retorna: (nombre_completo, partes_del_path, es_archivo)
        """
        # Normalizar separadores
        path = path.replace('\\', '/')
        
        # Remover prefijos comunes
        if path.startswith('./'):
            path = path[2:]
        
        # Determinar si es archivo o directorio
        is_file = not path.endswith('/') and '.' in os.path.basename(path)
        
        # Separar en partes
        parts = [p for p in path.strip('/').split('/') if p and p != '.']
        
        if not parts:
            return None
            
        return path.strip('/'), parts, is_file
    
    def _add_package_from_path(self, path_info: Tuple[str, List[str], bool]):
        """Agrega un paquete basado en información del path"""
        full_path, parts, is_file = path_info
        
        # Si es archivo, el paquete es su directorio padre
        if is_file and len(parts) > 1:
            package_parts = parts[:-1]
            filename = parts[-1]
        else:
            package_parts = parts
            filename = None
        
        # Crear jerarquía de paquetes
        for i in range(len(package_parts)):
            package_name = '.'.join(package_parts[:i+1])
            parent_name = '.'.join(package_parts[:i]) if i > 0 else None
            
            # Agregar paquete
            if package_name not in self.packages:
                self.packages[package_name] = {
                    'name': package_name,
                    'short_name': package_parts[i],
                    'level': i,
                    'parent': parent_name,
                    'files': [],
                    'type': self._determine_package_type(package_parts[i])
                }
            
            # Agregar archivo al paquete
            if filename and i == len(package_parts) - 1:
                self.packages[package_name]['files'].append(filename)
            
            # Establecer jerarquías
            if parent_name:
                self.hierarchies[parent_name].append(package_name)
    
    def _analyze_file_imports(self, filename: str, code: str):
        """Analiza imports de un archivo específico"""
        # Determinar paquete del archivo
        file_package = self._get_package_from_filename(filename)
        
        # Extraer imports
        imports = self._extract_all_imports(code)
        
        # Mapear imports a paquetes
        for imp in imports:
            target_package = self._get_package_from_import(imp)
            if target_package and target_package != file_package:
                self.imports_map[file_package].add(target_package)
        
        # Agregar paquete si no existe
        if file_package not in self.packages:
            self.packages[file_package] = {
                'name': file_package,
                'short_name': file_package.split('.')[-1],
                'level': len(file_package.split('.')) - 1,
                'parent': '.'.join(file_package.split('.')[:-1]) if '.' in file_package else None,
                'files': [filename],
                'type': self._determine_package_type(file_package)
            }
    
    def _get_package_from_filename(self, filename: str) -> str:
        """Determina el paquete basado en el nombre del archivo"""
        # Remover extensión
        name = os.path.splitext(filename)[0]
        
        # Si contiene path, usar la estructura de directorios
        if '/' in filename or '\\' in filename:
            path_parts = filename.replace('\\', '/').split('/')
            if len(path_parts) > 1:
                return '.'.join(path_parts[:-1])
        
        # Determinar paquete por tipo de archivo
        if any(keyword in name.lower() for keyword in ['controller', 'api']):
            return 'controllers'
        elif any(keyword in name.lower() for keyword in ['service', 'business']):
            return 'services'
        elif any(keyword in name.lower() for keyword in ['model', 'entity', 'domain']):
            return 'models'
        elif any(keyword in name.lower() for keyword in ['repository', 'dao', 'data']):
            return 'repositories'
        elif any(keyword in name.lower() for keyword in ['view', 'ui', 'component']):
            return 'views'
        elif any(keyword in name.lower() for keyword in ['util', 'helper', 'tool']):
            return 'utils'
        elif any(keyword in name.lower() for keyword in ['config', 'setting']):
            return 'config'
        else:
            return 'main'
    
    def _extract_all_imports(self, code: str) -> List[str]:
        """Extrae todos los imports del código independientemente del lenguaje"""
        imports = []
        
        # Patrones para diferentes lenguajes
        patterns = [
            # Python
            r'from\s+([^\s]+)\s+import',
            r'import\s+([^\s,]+)',
            
            # JavaScript/TypeScript
            r'import\s+.*?\s+from\s+["\']([^"\']+)["\']',
            r'import\s+["\']([^"\']+)["\']',
            r'require\s*\(\s*["\']([^"\']+)["\']\s*\)',
            
            # Java
            r'import\s+([^;]+);',
            r'package\s+([^;]+);',
            
            # C#
            r'using\s+([^;]+);',
            r'namespace\s+([^{]+)',
            
            # PHP
            r'use\s+([^;]+);',
            r'include\s*\(\s*["\']([^"\']+)["\']\s*\)',
            r'require\s*\(\s*["\']([^"\']+)["\']\s*\)',
            
            # C/C++
            r'#include\s*[<"]([^>"]+)[>"]',
            
            # Go
            r'import\s+["\']([^"\']+)["\']',
            
            # Rust
            r'use\s+([^;]+);',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, code, re.MULTILINE)
            for match in matches:
                # Limpiar y normalizar
                cleaned = match.strip().split()[0]  # Tomar solo la primera parte
                if cleaned and not cleaned.startswith('.'):  # Evitar imports relativos
                    imports.append(cleaned)
        
        return list(set(imports))  # Remover duplicados
    
    def _get_package_from_import(self, import_path: str) -> str:
        """Convierte un import a nombre de paquete"""
        # Limpiar el import
        import_path = import_path.strip()
        
        # Para imports con puntos, tomar la parte base
        if '.' in import_path:
            parts = import_path.split('.')
            # Si es un paquete conocido de librería estándar
            if parts[0] in ['java', 'javax', 'org', 'com']:
                return f"external.{parts[0]}"
            elif parts[0] in ['System', 'Microsoft']:  # C#
                return f"external.{parts[0]}"
            elif parts[0] in ['std', 'core']:  # Rust, C++
                return f"external.{parts[0]}"
            else:
                return parts[0]  # Paquete interno
        
        # Para imports de archivos/módulos
        if '/' in import_path:
            return import_path.split('/')[0]
        
        # Determinar si es externo
        external_indicators = [
            'node_modules', 'pip', 'maven', 'composer',
            'react', 'angular', 'vue', 'django', 'flask',
            'spring', 'hibernate', 'junit', 'mockito'
        ]
        
        if any(indicator in import_path.lower() for indicator in external_indicators):
            return f"external.{import_path}"
        
        return import_path
    
    def _determine_package_type(self, package_name: str) -> str:
        """Determina el tipo de paquete basado en su nombre"""
        name_lower = package_name.lower()
        
        type_mapping = {
            # Capas de arquitectura
            'controller': 'presentation',
            'api': 'presentation',
            'view': 'presentation',
            'ui': 'presentation',
            
            'service': 'business',
            'business': 'business',
            'logic': 'business',
            'application': 'business',
            
            'model': 'domain',
            'entity': 'domain',
            'domain': 'domain',
            'core': 'domain',
            
            'repository': 'data',
            'dao': 'data',
            'data': 'data',
            'persistence': 'data',
            'database': 'data',
            
            # Tipos especiales
            'config': 'configuration',
            'setting': 'configuration',
            'properties': 'configuration',
            
            'util': 'utility',
            'helper': 'utility',
            'tool': 'utility',
            'common': 'utility',
            
            'test': 'testing',
            'spec': 'testing',
            
            'external': 'external',
            'lib': 'external',
            'vendor': 'external',
        }
        
        for keyword, pkg_type in type_mapping.items():
            if keyword in name_lower:
                return pkg_type
        
        return 'module'
    
    def _generate_package_dependencies(self):
        """Genera dependencias entre paquetes basado en imports"""
        for source_pkg, target_packages in self.imports_map.items():
            for target_pkg in target_packages:
                # Evitar auto-dependencias
                if source_pkg != target_pkg:
                    self.dependencies.append({
                        'from': source_pkg,
                        'to': target_pkg,
                        'type': 'depends'
                    })
    
    def _extract_npm_packages(self, config: str):
        """Extrae paquetes de package.json"""
        self._add_external_package('external.npm', 'external')
        
        # Buscar dependencias
        dep_patterns = [
            r'"dependencies"\s*:\s*{([^}]+)}',
            r'"devDependencies"\s*:\s*{([^}]+)}'
        ]
        
        for pattern in dep_patterns:
            matches = re.findall(pattern, config)
            for deps_block in matches:
                pkg_pattern = r'"([^"]+)"\s*:'
                packages = re.findall(pkg_pattern, deps_block)
                for pkg in packages[:5]:  # Limitar para claridad
                    self._add_external_package(f'external.{pkg}', 'external')
    
    def _extract_python_packages(self, config: str):
        """Extrae paquetes de requirements.txt"""
        self._add_external_package('external.pypi', 'external')
        
        lines = config.split('\n')
        for line in lines[:10]:  # Limitar para claridad
            line = line.strip()
            if line and not line.startswith('#'):
                pkg_name = re.split(r'[>=<!=]', line)[0].strip()
                if pkg_name:
                    self._add_external_package(f'external.{pkg_name}', 'external')
    
    def _extract_java_packages(self, config: str):
        """Extrae paquetes de Maven/Gradle"""
        self._add_external_package('external.maven', 'external')
        
        # Maven
        maven_pattern = r'<artifactId>([^<]+)</artifactId>'
        maven_deps = re.findall(maven_pattern, config)
        
        # Gradle
        gradle_pattern = r'implementation\s+["\']([^:"\']+):'
        gradle_deps = re.findall(gradle_pattern, config)
        
        all_deps = (maven_deps + gradle_deps)[:10]  # Limitar
        for dep in all_deps:
            self._add_external_package(f'external.{dep}', 'external')
    
    def _extract_php_packages(self, config: str):
        """Extrae paquetes de composer.json"""
        self._add_external_package('external.packagist', 'external')
        
        dep_pattern = r'"require"\s*:\s*{([^}]+)}'
        matches = re.findall(dep_pattern, config)
        
        for deps_block in matches:
            pkg_pattern = r'"([^"]+)"\s*:'
            packages = re.findall(pkg_pattern, deps_block)
            for pkg in packages[:5]:  # Limitar
                if '/' in pkg:  # Formato vendor/package
                    self._add_external_package(f'external.{pkg.split("/")[1]}', 'external')
    
    def _add_external_package(self, package_name: str, package_type: str):
        """Agrega un paquete externo"""
        if package_name not in self.packages:
            self.packages[package_name] = {
                'name': package_name,
                'short_name': package_name.split('.')[-1],
                'level': len(package_name.split('.')) - 1,
                'parent': '.'.join(package_name.split('.')[:-1]) if '.' in package_name else None,
                'files': [],
                'type': package_type
            }
    
    def _looks_like_requirements(self, content: str) -> bool:
        """Verifica si parece un archivo requirements.txt"""
        lines = content.strip().split('\n')
        dep_lines = sum(1 for line in lines 
                       if line.strip() and not line.strip().startswith('#') 
                       and ('==' in line or '>=' in line or re.match(r'^[a-zA-Z][\w-]*$', line.strip())))
        return dep_lines > len(lines) * 0.6
    
    def _generate_plantuml(self) -> str:
        """Genera el código PlantUML para el diagrama de paquetes"""
        plantuml = ["@startuml"]
        
        # Configuración de estilo
        plantuml.extend([
            "!theme plain",
            "skinparam package {",
            "  BackgroundColor White",
            "  BorderColor Black",
            "  FontSize 12",
            "}",
            "skinparam arrow {",
            "  Color #444444",
            "}",
            ""
        ])
        
        # Agrupar paquetes por tipo
        packages_by_type = defaultdict(list)
        for pkg_name, pkg_info in self.packages.items():
            pkg_type = pkg_info.get('type', 'module')
            packages_by_type[pkg_type].append((pkg_name, pkg_info))
        
        # Generar paquetes agrupados por tipo
        type_colors = {
            'presentation': '#E8F4FD',
            'business': '#FFF2CC',
            'domain': '#D4E6B7',
            'data': '#F8CECC',
            'configuration': '#E1D5E7',
            'utility': '#DAE8FC',
            'testing': '#FFE6CC',
            'external': '#F5F5F5',
            'module': '#FFFFFF'
        }
        
        for pkg_type, packages in packages_by_type.items():
            if not packages:
                continue
                
            color = type_colors.get(pkg_type, '#FFFFFF')
            
            # Si hay muchos paquetes del mismo tipo, agruparlos
            if len(packages) > 1 and pkg_type != 'external':
                plantuml.append(f'package "{pkg_type.title()} Layer" #{color} {{')
                
                for pkg_name, pkg_info in packages:
                    short_name = pkg_info.get('short_name', pkg_name)
                    plantuml.append(f'  package "{short_name}"')
                
                plantuml.append('}')
            else:
                # Paquetes individuales
                for pkg_name, pkg_info in packages:
                    short_name = pkg_info.get('short_name', pkg_name)
                    if pkg_type == 'external':
                        plantuml.append(f'package "{short_name}" #{color} <<external>>')
                    else:
                        plantuml.append(f'package "{short_name}" #{color}')
            
            plantuml.append('')
        
        # Generar dependencias
        generated_deps = set()  # Evitar duplicados
        
        for dependency in self.dependencies:
            from_pkg = dependency['from']
            to_pkg = dependency['to']
            
            # Obtener nombres cortos
            from_short = self.packages.get(from_pkg, {}).get('short_name', from_pkg)
            to_short = self.packages.get(to_pkg, {}).get('short_name', to_pkg)
            
            # Evitar duplicados
            dep_key = (from_short, to_short)
            if dep_key in generated_deps:
                continue
            generated_deps.add(dep_key)
            
            # Tipo de flecha según el tipo de dependencia
            arrow = '-->'
            if to_pkg.startswith('external.'):
                arrow = '..>'
            
            plantuml.append(f'"{from_short}" {arrow} "{to_short}"')
        
        # Agregar algunas dependencias típicas si no se detectaron
        if not self.dependencies and len(self.packages) > 1:
            pkg_names = list(self.packages.keys())
            # Crear algunas dependencias lógicas
            for i, pkg_name in enumerate(pkg_names[:3]):
                for j, other_pkg in enumerate(pkg_names[i+1:i+3]):
                    if pkg_name != other_pkg:
                        pkg_short = self.packages[pkg_name].get('short_name', pkg_name)
                        other_short = self.packages[other_pkg].get('short_name', other_pkg)
                        plantuml.append(f'"{pkg_short}" --> "{other_short}"')
        
        # Agregar notas explicativas
        if packages_by_type.get('external'):
            plantuml.append('')
            plantuml.append('note right : External dependencies\\nfrom package managers')
        
        plantuml.append("@enduml")
        return '\n'.join(plantuml)
