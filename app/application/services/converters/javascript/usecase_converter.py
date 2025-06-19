import re
from typing import List, Dict, Set


class JavaScriptUseCaseConverter:
    """
    Convertidor de código JavaScript/TypeScript a diagramas de casos de uso UML PlantUML.
    Detecta actores, casos de uso y relaciones basándose en rutas, controladores,
    servicios, middlewares y patrones comunes de frameworks web.
    """
    
    def __init__(self):
        self.actors = set()
        self.use_cases = set()
        self.relationships = []
        self.includes = []
        self.extends = []
        
    def convert_to_plantuml(self, code: str) -> str:
        """
        Convierte código JavaScript/TypeScript a diagrama de casos de uso PlantUML.
        
        Args:
            code: Código fuente de JavaScript/TypeScript
            
        Returns:
            Diagrama PlantUML como string
        """
        self._reset()
        self._extract_actors_and_use_cases(code)
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
        self.actors = set()
        self.use_cases = set()
        self.relationships = []
        self.includes = []
        self.extends = []
    
    def _extract_actors_and_use_cases(self, code: str):
        """Extrae actores y casos de uso del código."""
        # Detectar rutas Express.js
        self._extract_express_routes(code)
        
        # Detectar rutas Next.js API
        self._extract_nextjs_api_routes(code)
        
        # Detectar controladores
        self._extract_controllers(code)
        
        # Detectar servicios y casos de uso
        self._extract_services_and_use_cases(code)
        
        # Detectar middlewares de autenticación
        self._extract_auth_middleware(code)
        
        # Detectar GraphQL resolvers
        self._extract_graphql_resolvers(code)
        
        # Detectar Socket.IO eventos
        self._extract_socket_events(code)
    
    def _extract_express_routes(self, code: str):
        """Extrae rutas de Express.js."""
        # Rutas HTTP (GET, POST, PUT, DELETE, PATCH)
        route_pattern = r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,?\s*(?:async\s+)?\(?(?:\w+\s*,\s*)*(?:req|request)\s*,\s*(?:res|response)\)?'
        
        for match in re.finditer(route_pattern, code, re.IGNORECASE):
            method = match.group(1).upper()
            path = match.group(2)
            
            # Extraer el caso de uso del path
            use_case = self._extract_use_case_from_path(method, path)
            self.use_cases.add(use_case)
            
            # Detectar actor basado en el path
            actor = self._detect_actor_from_path(path)
            self.actors.add(actor)
            
            # Agregar relación
            self.relationships.append({
                'actor': actor,
                'use_case': use_case,
                'type': 'uses'
            })
    
    def _extract_nextjs_api_routes(self, code: str):
        """Extrae rutas de Next.js API."""
        # Handler functions en Next.js API routes
        handler_pattern = r'export\s+(?:default\s+)?(?:async\s+)?function\s+(\w+)?\s*\(\s*req\s*,\s*res\s*\)'
        
        for match in re.finditer(handler_pattern, code):
            handler_name = match.group(1) or 'handler'
            
            # Buscar el método HTTP en el cuerpo de la función
            method_pattern = r'req\.method\s*===?\s*[\'"](\w+)[\'"]'
            methods = re.findall(method_pattern, code)
            
            if not methods:
                methods = ['GET']  # Default para Next.js
            
            for method in methods:
                use_case = f"{method} API Handler"
                if handler_name != 'handler':
                    use_case = f"{method} {handler_name}"
                
                self.use_cases.add(use_case)
                self.actors.add("API Client")
                
                self.relationships.append({
                    'actor': "API Client",
                    'use_case': use_case,
                    'type': 'uses'
                })
    
    def _extract_controllers(self, code: str):
        """Extrae controladores y sus métodos."""
        # Controladores de clase
        controller_pattern = r'(?:export\s+)?class\s+(\w+Controller)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        
        for match in re.finditer(controller_pattern, code, re.DOTALL):
            controller_name = match.group(1)
            controller_body = match.group(2)
            
            # Extraer métodos del controlador
            method_pattern = r'(?:async\s+)?(\w+)\s*\(\s*(?:req|request)\s*,\s*(?:res|response)\s*\)'
            
            for method_match in re.finditer(method_pattern, controller_body):
                method_name = method_match.group(1)
                
                # Convertir nombre del método a caso de uso
                use_case = self._method_to_use_case(method_name)
                self.use_cases.add(use_case)
                
                # Detectar actor basado en el controlador
                actor = self._detect_actor_from_controller(controller_name)
                self.actors.add(actor)
                
                self.relationships.append({
                    'actor': actor,
                    'use_case': use_case,
                    'type': 'uses'
                })
    
    def _extract_services_and_use_cases(self, code: str):
        """Extrae servicios y casos de uso."""
        # Servicios de clase
        service_pattern = r'(?:export\s+)?class\s+(\w+Service)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        
        for match in re.finditer(service_pattern, code, re.DOTALL):
            service_name = match.group(1)
            service_body = match.group(2)
            
            # Extraer métodos del servicio
            method_pattern = r'(?:async\s+)?(\w+)\s*\('
            
            for method_match in re.finditer(method_pattern, service_body):
                method_name = method_match.group(1)
                
                # Saltar constructores y métodos privados
                if method_name in ['constructor'] or method_name.startswith('_'):
                    continue
                
                # Convertir método a caso de uso
                use_case = self._method_to_use_case(method_name)
                self.use_cases.add(use_case)
                
                # Los servicios suelen ser usados por el sistema
                self.actors.add("System")
                
                self.relationships.append({
                    'actor': "System",
                    'use_case': use_case,
                    'type': 'uses'
                })
        
        # Funciones de casos de uso
        use_case_function_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w*[Uu]se[Cc]ase\w*)\s*\('
        for match in re.finditer(use_case_function_pattern, code):
            function_name = match.group(1)
            use_case = self._function_to_use_case(function_name)
            self.use_cases.add(use_case)
            
            self.actors.add("User")
            self.relationships.append({
                'actor': "User",
                'use_case': use_case,
                'type': 'uses'
            })
    
    def _extract_auth_middleware(self, code: str):
        """Extrae middleware de autenticación."""
        # Middleware de autenticación
        auth_patterns = [
            r'(?:requireAuth|authenticate|verifyToken|checkAuth)',
            r'passport\.(authenticate|use)',
            r'jwt\.verify',
            r'verifyJWT',
            r'authMiddleware'
        ]
        
        for pattern in auth_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                self.use_cases.add("Authenticate User")
                self.actors.add("User")
                self.actors.add("Authentication System")
                
                self.relationships.append({
                    'actor': "User",
                    'use_case': "Authenticate User",
                    'type': 'uses'
                })
                
                # Relación include con otros casos de uso que requieren autenticación
                for use_case in list(self.use_cases):
                    if use_case != "Authenticate User" and any(keyword in use_case.lower() for keyword in ['create', 'update', 'delete', 'manage']):
                        self.includes.append({
                            'from': use_case,
                            'to': "Authenticate User"
                        })
                break
    
    def _extract_graphql_resolvers(self, code: str):
        """Extrae resolvers de GraphQL."""
        # Resolvers de GraphQL
        resolver_pattern = r'(\w+):\s*(?:async\s+)?\(\s*(?:parent|root)?\s*,?\s*(?:args|arguments)?\s*,?\s*(?:context|ctx)?\s*,?\s*(?:info)?\s*\)\s*=>'
        
        for match in re.finditer(resolver_pattern, code):
            resolver_name = match.group(1)
            use_case = self._resolver_to_use_case(resolver_name)
            self.use_cases.add(use_case)
            
            self.actors.add("GraphQL Client")
            self.relationships.append({
                'actor': "GraphQL Client",
                'use_case': use_case,
                'type': 'uses'
            })
    
    def _extract_socket_events(self, code: str):
        """Extrae eventos de Socket.IO."""
        # Eventos de Socket.IO
        socket_pattern = r'socket\.on\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*(?:async\s+)?\('
        
        for match in re.finditer(socket_pattern, code):
            event_name = match.group(1)
            use_case = f"Handle {event_name.replace('_', ' ').title()}"
            self.use_cases.add(use_case)
            
            self.actors.add("WebSocket Client")
            self.relationships.append({
                'actor': "WebSocket Client",
                'use_case': use_case,
                'type': 'uses'
            })
    
    def _extract_relationships(self, code: str):
        """Extrae relaciones include y extend."""
        # Buscar llamadas a otros servicios (include)
        for use_case in self.use_cases:
            # Buscar llamadas a servicios dentro de métodos
            service_call_pattern = r'(?:await\s+)?(\w+Service)\.(\w+)\s*\('
            for match in re.finditer(service_call_pattern, code):
                service_name = match.group(1)
                method_name = match.group(2)
                
                included_use_case = self._method_to_use_case(method_name)
                if included_use_case in self.use_cases and included_use_case != use_case:
                    self.includes.append({
                        'from': use_case,
                        'to': included_use_case
                    })
        
        # Buscar validaciones (extend)
        validation_patterns = [
            r'validate\w*',
            r'check\w*',
            r'verify\w*'
        ]
        
        for pattern in validation_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                validation_use_case = "Validate Input"
                self.use_cases.add(validation_use_case)
                
                for use_case in list(self.use_cases):
                    if use_case != validation_use_case and any(keyword in use_case.lower() for keyword in ['create', 'update', 'submit']):
                        self.extends.append({
                            'from': validation_use_case,
                            'to': use_case
                        })
    
    def _extract_use_case_from_path(self, method: str, path: str) -> str:
        """Extrae caso de uso de una ruta HTTP."""
        # Limpiar el path
        clean_path = re.sub(r'/:\w+', '', path)  # Remover parámetros
        clean_path = clean_path.strip('/')
        
        # Convertir a palabras
        words = re.split(r'[/_-]', clean_path)
        words = [word.title() for word in words if word]
        
        # Mapear método HTTP a acción
        action_map = {
            'GET': 'View' if not words else 'Get',
            'POST': 'Create',
            'PUT': 'Update',
            'PATCH': 'Update',
            'DELETE': 'Delete'
        }
        
        action = action_map.get(method, method.title())
        
        if words:
            return f"{action} {' '.join(words)}"
        else:
            return f"{action} Resource"
    
    def _detect_actor_from_path(self, path: str) -> str:
        """Detecta el actor basado en el path."""
        path_lower = path.lower()
        
        if 'admin' in path_lower:
            return "Administrator"
        elif any(keyword in path_lower for keyword in ['auth', 'login', 'register', 'user']):
            return "User"
        elif 'api' in path_lower:
            return "API Client"
        else:
            return "User"
    
    def _detect_actor_from_controller(self, controller_name: str) -> str:
        """Detecta el actor basado en el nombre del controlador."""
        controller_lower = controller_name.lower()
        
        if 'admin' in controller_lower:
            return "Administrator"
        elif 'auth' in controller_lower:
            return "User"
        elif 'api' in controller_lower:
            return "API Client"
        else:
            return "User"
    
    def _method_to_use_case(self, method_name: str) -> str:
        """Convierte nombre de método a caso de uso."""
        # Dividir por camelCase
        words = re.sub(r'([a-z])([A-Z])', r'\1 \2', method_name).split()
        words = [word.title() for word in words]
        
        return ' '.join(words)
    
    def _function_to_use_case(self, function_name: str) -> str:
        """Convierte nombre de función a caso de uso."""
        # Remover sufijos comunes
        function_name = re.sub(r'UseCase$', '', function_name)
        
        # Dividir por camelCase
        words = re.sub(r'([a-z])([A-Z])', r'\1 \2', function_name).split()
        words = [word.title() for word in words]
        
        return ' '.join(words)
    
    def _resolver_to_use_case(self, resolver_name: str) -> str:
        """Convierte nombre de resolver a caso de uso."""
        # Dividir por camelCase
        words = re.sub(r'([a-z])([A-Z])', r'\1 \2', resolver_name).split()
        words = [word.title() for word in words]
        
        return f"Resolve {' '.join(words)}"
    
    def _generate_plantuml(self) -> str:
        """Genera el código PlantUML."""
        uml_lines = ['@startuml', '']
        
        # Configuración
        uml_lines.extend([
            'left to right direction',
            'skinparam packageStyle rectangle',
            ''
        ])
        
        # Actores
        for actor in sorted(self.actors):
            if ' ' in actor:
                uml_lines.append(f'actor "{actor}" as {actor.replace(" ", "")}')
            else:
                uml_lines.append(f'actor {actor}')
        
        uml_lines.append('')
        
        # Casos de uso
        for use_case in sorted(self.use_cases):
            if ' ' in use_case:
                use_case_id = use_case.replace(' ', '').replace('-', '')
                uml_lines.append(f'usecase "{use_case}" as {use_case_id}')
            else:
                uml_lines.append(f'usecase {use_case}')
        
        uml_lines.append('')
        
        # Relaciones actor-caso de uso
        for rel in self.relationships:
            actor_id = rel['actor'].replace(' ', '')
            use_case_id = rel['use_case'].replace(' ', '').replace('-', '')
            uml_lines.append(f'{actor_id} --> {use_case_id}')
        
        # Relaciones include
        if self.includes:
            uml_lines.append('')
            for include in self.includes:
                from_id = include['from'].replace(' ', '').replace('-', '')
                to_id = include['to'].replace(' ', '').replace('-', '')
                uml_lines.append(f'{from_id} ..> {to_id} : <<include>>')
        
        # Relaciones extend
        if self.extends:
            uml_lines.append('')
            for extend in self.extends:
                from_id = extend['from'].replace(' ', '').replace('-', '')
                to_id = extend['to'].replace(' ', '').replace('-', '')
                uml_lines.append(f'{from_id} ..> {to_id} : <<extend>>')
        
        uml_lines.extend(['', '@enduml'])
        
        return '\n'.join(uml_lines)
