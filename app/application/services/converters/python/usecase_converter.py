# app/application/services/converters/python/usecase_converter.py
import ast
import re
from typing import Dict, List, Set

class PythonUseCaseConverter:
    def __init__(self):
        self.actors: Set[str] = set()
        self.use_cases: List[Dict] = []
        self.relationships: List[Dict] = []
        self.current_class = ""

    def convert(self, code: str) -> str:
        """Convierte código Python de APIs a diagrama UML de casos de uso en PlantUML"""
        try:
            # Intentar usar AST para análisis preciso
            tree = ast.parse(code)
            self._extract_from_ast(tree)
        except SyntaxError:
            # Fallback a análisis por regex
            self._extract_from_regex(code)
        
        # Analizar relaciones
        self._analyze_actor_relationships()
        
        # Generación UML
        plantuml = self._generate_plantuml()
        return plantuml

    def _extract_from_ast(self, tree: ast.AST):
        """Extrae casos de uso usando AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Buscar clases que parezcan controladores/routers
                if any(keyword in node.name.lower() for keyword in ['router', 'controller', 'api', 'view']):
                    self.current_class = node.name.replace('Router', '').replace('Controller', '').replace('API', '')
                    self._analyze_class_methods(node)

    def _analyze_class_methods(self, class_node: ast.ClassDef):
        """Analiza métodos de una clase para extraer casos de uso"""
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                # Analizar decoradores para encontrar rutas HTTP
                http_method, path = self._extract_route_info(node)
                
                if http_method:
                    # Generar caso de uso
                    use_case_name = self._generate_use_case_name(http_method, node.name, path)
                    actor = self._determine_default_actor(http_method, node.name)
                    
                    self.use_cases.append({
                        'name': use_case_name,
                        'method_name': node.name,
                        'http_method': http_method,
                        'path': path,
                        'class': self.current_class,
                        'actor': actor
                    })

    def _extract_route_info(self, func_node: ast.FunctionDef) -> tuple:
        """Extrae información de rutas desde decoradores"""
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Name):
                # Decoradores simples como @get, @post
                decorator_name = decorator.id.lower()
                if decorator_name in ['get', 'post', 'put', 'delete', 'patch']:
                    return decorator_name.upper(), ""
            
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    # Decoradores con argumentos como @app.get("/path")
                    decorator_name = decorator.func.id.lower()
                    if decorator_name in ['get', 'post', 'put', 'delete', 'patch']:
                        path = self._extract_path_from_args(decorator.args)
                        return decorator_name.upper(), path
                
                elif isinstance(decorator.func, ast.Attribute):
                    # Decoradores como @app.get(), @router.post()
                    method_name = decorator.func.attr.lower()
                    if method_name in ['get', 'post', 'put', 'delete', 'patch']:
                        path = self._extract_path_from_args(decorator.args)
                        return method_name.upper(), path
        
        return None, None

    def _extract_path_from_args(self, args: List[ast.expr]) -> str:
        """Extrae el path desde los argumentos del decorador"""
        if args and isinstance(args[0], ast.Str):
            return args[0].s
        elif args and isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
            return args[0].value
        return ""

    def _extract_from_regex(self, code: str):
        """Extrae casos de uso usando regex como fallback"""
        code = self._normalize_code(code)
        
        # Buscar decoradores de rutas
        route_pattern = re.compile(
            r'@(?:app\.|router\.)?(\w+)(?:\(["\']([^"\']*)["\'].*?\))?\s*\n\s*def\s+(\w+)',
            re.MULTILINE
        )
        
        for match in route_pattern.finditer(code):
            decorator_name = match.group(1).lower()
            path = match.group(2) or ""
            method_name = match.group(3)
            
            if decorator_name in ['get', 'post', 'put', 'delete', 'patch']:
                http_method = decorator_name.upper()
                use_case_name = self._generate_use_case_name(http_method, method_name, path)
                actor = self._determine_default_actor(http_method, method_name)
                
                self.use_cases.append({
                    'name': use_case_name,
                    'method_name': method_name,
                    'http_method': http_method,
                    'path': path,
                    'class': 'API',
                    'actor': actor
                })

        # Buscar comentarios @Actor
        self._extract_actor_comments(code)

    def _extract_actor_comments(self, code: str):
        """Extrae comentarios especiales @Actor"""
        actor_pattern = re.compile(
            r'#\s*@Actor:\s*(\w+)\s*->\s*(\w+)',
            re.MULTILINE
        )
        
        for match in actor_pattern.finditer(code):
            actor_name = match.group(1)
            method_name = match.group(2)
            
            # Actualizar el actor para el caso de uso correspondiente
            for use_case in self.use_cases:
                if use_case['method_name'] == method_name:
                    use_case['actor'] = actor_name
                    break

    def _normalize_code(self, code: str) -> str:
        """Normaliza el código para análisis"""
        # Remove comments except @Actor
        code = re.sub(r'#(?!\s*@Actor).*', '', code)
        # Remove docstrings
        code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
        code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)
        return code

    def _generate_use_case_name(self, http_method: str, method_name: str, path: str) -> str:
        """Genera nombres descriptivos para casos de uso"""
        # Mapeo de verbos HTTP a acciones
        verb_mapping = {
            'GET': 'Consultar',
            'POST': 'Crear',
            'PUT': 'Actualizar',
            'DELETE': 'Eliminar',
            'PATCH': 'Modificar'
        }
        
        # Limpiar nombre del método
        clean_name = re.sub(r'(get|post|put|delete|patch)_?', '', method_name, flags=re.IGNORECASE)
        clean_name = re.sub(r'_+', ' ', clean_name).strip()
        
        # Si el nombre está vacío, usar el path
        if not clean_name and path:
            clean_name = path.replace('/', ' ').replace('{', '').replace('}', '').strip()
        
        # Construir nombre del caso de uso
        action = verb_mapping.get(http_method, http_method.lower())
        if clean_name:
            return f"{action} {clean_name}"
        else:
            return f"{action} en {self.current_class or 'API'}"

    def _determine_default_actor(self, http_method: str, method_name: str) -> str:
        """Determina el actor por defecto basado en el contexto"""
        method_lower = method_name.lower()
        
        if any(keyword in method_lower for keyword in ['admin', 'administrator']):
            return "Administrador"
        elif any(keyword in method_lower for keyword in ['user', 'client', 'customer']):
            return "Usuario"
        elif any(keyword in method_lower for keyword in ['auth', 'login', 'register']):
            return "Usuario"
        else:
            return "Usuario"

    def _analyze_actor_relationships(self):
        """Analiza y consolida las relaciones entre actores y casos de uso"""
        for use_case in self.use_cases:
            actor = use_case['actor']
            self.actors.add(actor)
            
            self.relationships.append({
                'actor': actor,
                'use_case': use_case['name'],
                'type': 'uses'
            })

    def _generate_plantuml(self) -> str:
        """Genera el código PlantUML para el diagrama de casos de uso"""
        plantuml = ["@startuml"]
        
        # Configuración
        plantuml.extend([
            "left to right direction",
            "skinparam usecase {",
            "  BackgroundColor White",
            "  BorderColor Black",
            "  ArrowColor #444444",
            "}",
            "skinparam actor {",
            "  BackgroundColor #EEEEEE",
            "  BorderColor Black",
            "}",
            ""
        ])
        
        # Actores
        for actor in sorted(self.actors):
            plantuml.append(f'actor "{actor}" as {actor.replace(" ", "")}')
        
        plantuml.append("")
        
        # Sistema (rectángulo contenedor)
        system_name = f"Sistema {self.current_class}" if self.current_class else "Sistema API"
        plantuml.append(f'rectangle "{system_name}" {{')
        
        # Casos de uso
        for use_case in self.use_cases:
            use_case_id = use_case['name'].replace(' ', '').replace('/', '')
            plantuml.append(f'  usecase "{use_case["name"]}" as {use_case_id}')
        
        plantuml.append("}")
        plantuml.append("")
        
        # Relaciones
        for rel in self.relationships:
            actor_id = rel['actor'].replace(" ", "")
            use_case_id = rel['use_case'].replace(' ', '').replace('/', '')
            plantuml.append(f"{actor_id} --> {use_case_id}")
        
        plantuml.append("@enduml")
        return '\n'.join(plantuml)
