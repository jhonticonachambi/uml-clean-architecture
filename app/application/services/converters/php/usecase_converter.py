# app/application/services/converters/php/usecase_converter.py
import re
from typing import Dict, List, Set

class PHPUseCaseConverter:
    def __init__(self):
        self.actors: Set[str] = set()
        self.use_cases: List[Dict] = []
        self.relationships: List[Dict] = []
        self.current_controller = ""

    def convert(self, code: str) -> str:
        """Convierte código PHP de controladores a diagrama UML de casos de uso en PlantUML"""
        # Preprocesamiento
        code = self._normalize_code(code)
        
        # Extracción de elementos
        self._extract_controllers(code)
        self._analyze_actor_relationships()
        
        # Generación UML
        plantuml = self._generate_plantuml()
        return plantuml

    def _normalize_code(self, code: str) -> str:
        """Limpia el código removiendo comentarios y literales de string"""
        # Remove single-line comments but keep @Actor comments
        code = re.sub(r'//(?!\s*@Actor).*', '', code)
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Remove hash comments but keep @Actor
        code = re.sub(r'#(?!\s*@Actor).*', '', code)
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)
        # Remove string literals (simplified)
        code = re.sub(r'"[^"]*"', '""', code)
        code = re.sub(r"'[^']*'", "''", code)
        return code

    def _extract_controllers(self, code: str):
        """Extrae controladores y sus métodos de endpoint"""
        # Buscar clases controladoras
        controller_pattern = re.compile(
            r'class\s+(\w*Controller)(?:\s+extends\s+\w+)?\s*\{',
            re.MULTILINE
        )
        
        for match in controller_pattern.finditer(code):
            controller_name = match.group(1)
            self.current_controller = controller_name.replace('Controller', '')
            
            # Extraer el cuerpo del controlador
            start_idx = match.end()
            controller_body = self._extract_balanced_content(code[start_idx:], '{', '}')
            self._extract_endpoints(controller_body)

    def _extract_endpoints(self, controller_body: str):
        """Extrae métodos de endpoint del controlador"""
        # Buscar métodos públicos que parezcan endpoints
        endpoint_patterns = [
            # Métodos con Route annotations
            r'#\[Route\(["\']([^"\']*)["\'].*?methods:\s*\[["\'](\w+)["\'].*?\]\s*\]\s*public\s+function\s+(\w+)',
            # Métodos públicos típicos de controladores
            r'public\s+function\s+(index|show|create|store|edit|update|destroy|(\w*)).*?\s*\(',
        ]
        
        for pattern in endpoint_patterns:
            for match in re.finditer(pattern, controller_body, re.MULTILINE | re.DOTALL):
                if len(match.groups()) >= 3:  # Route annotation pattern
                    route = match.group(1)
                    http_method = match.group(2).upper()
                    method_name = match.group(3)
                else:  # Simple method pattern
                    method_name = match.group(1) or match.group(2)
                    http_method = self._infer_http_method(method_name)
                    route = ""
                
                # Generar caso de uso
                use_case_name = self._generate_use_case_name(http_method, method_name, route)
                actor = self._determine_default_actor(http_method, method_name)
                
                self.use_cases.append({
                    'name': use_case_name,
                    'method_name': method_name,
                    'http_method': http_method,
                    'route': route,
                    'controller': self.current_controller,
                    'actor': actor
                })

        # También buscar métodos con docblocks que contengan información de rutas
        self._extract_from_docblocks(controller_body)
        
        # Buscar comentarios @Actor para sobrescribir actores
        self._extract_actor_comments(controller_body)

    def _extract_from_docblocks(self, controller_body: str):
        """Extrae endpoints desde docblocks con información de rutas"""
        docblock_pattern = re.compile(
            r'/\*\*.*?@Route\s*\(["\']([^"\']*)["\'].*?methods=\{["\'](\w+)["\'].*?\*\/\s*public\s+function\s+(\w+)',
            re.MULTILINE | re.DOTALL
        )
        
        for match in docblock_pattern.finditer(controller_body):
            route = match.group(1)
            http_method = match.group(2).upper()
            method_name = match.group(3)
            
            use_case_name = self._generate_use_case_name(http_method, method_name, route)
            actor = self._determine_default_actor(http_method, method_name)
            
            # Evitar duplicados
            if not any(uc['method_name'] == method_name for uc in self.use_cases):
                self.use_cases.append({
                    'name': use_case_name,
                    'method_name': method_name,
                    'http_method': http_method,
                    'route': route,
                    'controller': self.current_controller,
                    'actor': actor
                })

    def _infer_http_method(self, method_name: str) -> str:
        """Infiere el método HTTP basado en el nombre del método"""
        method_lower = method_name.lower()
        
        if method_lower in ['index', 'show', 'get']:
            return 'GET'
        elif method_lower in ['store', 'create']:
            return 'POST'
        elif method_lower in ['update']:
            return 'PUT'
        elif method_lower in ['destroy', 'delete']:
            return 'DELETE'
        else:
            return 'GET'  # Por defecto

    def _extract_actor_comments(self, controller_body: str):
        """Extrae comentarios especiales @Actor para casos de uso específicos"""
        actor_patterns = [
            r'//\s*@Actor:\s*(\w+)\s*->\s*(\w+)',
            r'#\s*@Actor:\s*(\w+)\s*->\s*(\w+)'
        ]
        
        for pattern in actor_patterns:
            for match in re.finditer(pattern, controller_body):
                actor_name = match.group(1)
                method_name = match.group(2)
                
                # Actualizar el actor para el caso de uso correspondiente
                for use_case in self.use_cases:
                    if use_case['method_name'] == method_name:
                        use_case['actor'] = actor_name
                        break

    def _generate_use_case_name(self, http_method: str, method_name: str, route: str) -> str:
        """Genera nombres descriptivos para casos de uso"""
        # Mapeo de verbos HTTP a acciones
        verb_mapping = {
            'GET': 'Consultar',
            'POST': 'Crear',
            'PUT': 'Actualizar',
            'DELETE': 'Eliminar',
            'PATCH': 'Modificar'
        }
        
        # Mapeo de métodos Laravel comunes
        laravel_methods = {
            'index': 'Listar',
            'show': 'Ver',
            'create': 'Crear',
            'store': 'Guardar',
            'edit': 'Editar',
            'update': 'Actualizar',
            'destroy': 'Eliminar'
        }
        
        # Usar mapeo de Laravel si coincide
        if method_name.lower() in laravel_methods:
            action = laravel_methods[method_name.lower()]
            return f"{action} {self.current_controller}"
        
        # Limpiar nombre del método
        clean_name = re.sub(r'(get|post|put|delete|patch)', '', method_name, flags=re.IGNORECASE)
        clean_name = re.sub(r'([A-Z])', r' \1', clean_name).strip()
        
        # Si el nombre está vacío, usar la ruta
        if not clean_name and route:
            clean_name = route.replace('/', ' ').strip()
        
        # Construir nombre del caso de uso
        action = verb_mapping.get(http_method, http_method.lower())
        if clean_name:
            return f"{action} {clean_name}"
        else:
            return f"{action} en {self.current_controller}"

    def _determine_default_actor(self, http_method: str, method_name: str) -> str:
        """Determina el actor por defecto basado en el contexto"""
        method_lower = method_name.lower()
        
        if any(keyword in method_lower for keyword in ['admin', 'administrator']):
            return "Administrador"
        elif any(keyword in method_lower for keyword in ['user', 'client', 'customer']):
            return "Usuario"
        elif any(keyword in method_lower for keyword in ['auth', 'login', 'register']):
            return "Usuario"
        elif method_lower in ['destroy', 'delete', 'update', 'edit']:
            return "Usuario"  # Operaciones que requieren permisos
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
        system_name = f"Sistema {self.current_controller}" if self.current_controller else "Sistema"
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
