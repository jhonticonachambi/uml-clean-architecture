import re
from typing import List, Dict, Set, Tuple


class JavaScriptSequenceConverter:
    """
    Convertidor de código JavaScript/TypeScript a diagramas de secuencia UML PlantUML.
    Analiza llamadas entre objetos, métodos, funciones y APIs para generar el flujo de interacciones.
    """
    
    def __init__(self):
        self.participants = set()
        self.interactions = []
        self.current_method = None
        self.call_stack = []
        
    def convert_to_plantuml(self, code: str) -> str:
        """
        Convierte código JavaScript/TypeScript a diagrama de secuencia PlantUML.
        
        Args:
            code: Código fuente de JavaScript/TypeScript
            
        Returns:
            Diagrama PlantUML como string
        """
        self._reset()
        self._extract_sequence_info(code)
        
        return self._generate_plantuml()
    
    def convert(self, code: str) -> str:
        """
        Método de compatibilidad para el protocolo BaseConverter.
        Delega a convert_to_plantuml.
        """
        return self.convert_to_plantuml(code)
    
    def _reset(self):
        """Reinicia el estado del convertidor."""
        self.participants = set()
        self.interactions = []
        self.current_method = None
        self.call_stack = []
    
    def _extract_sequence_info(self, code: str):
        """Extrae información de secuencia del código."""
        # Normalizar código
        normalized_code = self._normalize_code(code)
        
        # Extraer clases y sus métodos
        self._extract_classes_and_methods(normalized_code)
        
        # Extraer rutas y controladores
        self._extract_routes_and_controllers(normalized_code)
        
        # Extraer llamadas a servicios
        self._extract_service_calls(normalized_code)
        
        # Extraer llamadas HTTP/API
        self._extract_http_calls(normalized_code)
        
        # Extraer llamadas a base de datos
        self._extract_database_calls(normalized_code)
        
        # Extraer middleware y filtros
        self._extract_middleware_calls(normalized_code)
    
    def _normalize_code(self, code: str) -> str:
        """Normaliza el código removiendo comentarios y strings."""
        # Remover comentarios de línea
        code = re.sub(r'//.*?\n', '\n', code)
        
        # Remover comentarios de bloque
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        
        # Remover strings (mantener estructura)
        code = re.sub(r'"[^"]*"', '""', code)
        code = re.sub(r"'[^']*'", "''", code)
        code = re.sub(r'`[^`]*`', '``', code)
        
        return code
    
    def _extract_classes_and_methods(self, code: str):
        """Extrae clases y sus métodos."""
        # Patrón para clases
        class_pattern = r'(?:export\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        
        for match in re.finditer(class_pattern, code, re.DOTALL):
            class_name = match.group(1)
            class_body = match.group(2)
            
            self.participants.add(class_name)
            
            # Extraer métodos de la clase
            method_pattern = r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
            
            for method_match in re.finditer(method_pattern, class_body, re.DOTALL):
                method_name = method_match.group(1)
                method_body = method_match.group(2)
                
                if method_name == 'constructor':
                    continue
                
                self.current_method = f"{class_name}.{method_name}"
                self._analyze_method_calls(method_body, class_name)
    
    def _extract_routes_and_controllers(self, code: str):
        """Extrae rutas HTTP y controladores."""
        # Rutas Express.js
        route_pattern = r'(?:app|router)\.(get|post|put|delete|patch)\s*\([^,]+,\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        
        for match in re.finditer(route_pattern, code, re.DOTALL):
            method = match.group(1).upper()
            route_body = match.group(2)
            
            self.participants.add("Client")
            self.participants.add("Router")
            
            self.interactions.append({
                'from': 'Client',
                'to': 'Router',
                'message': f'{method} Request',
                'type': 'sync'
            })
            
            self._analyze_method_calls(route_body, "Router")
        
        # Next.js API routes
        nextjs_pattern = r'export\s+(?:default\s+)?(?:async\s+)?function\s+(\w+)?\s*\(\s*req\s*,\s*res\s*\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        
        for match in re.finditer(nextjs_pattern, code, re.DOTALL):
            handler_name = match.group(1) or 'handler'
            handler_body = match.group(2)
            
            self.participants.add("Client")
            self.participants.add("API")
            
            self.interactions.append({
                'from': 'Client',
                'to': 'API',
                'message': 'API Request',
                'type': 'sync'
            })
            
            self._analyze_method_calls(handler_body, "API")
    
    def _extract_service_calls(self, code: str):
        """Extrae llamadas a servicios."""
        # Llamadas a métodos de servicios
        service_call_pattern = r'(?:await\s+)?(\w*[Ss]ervice\w*)\.(\w+)\s*\([^)]*\)'
        
        for match in re.finditer(service_call_pattern, code):
            service_name = match.group(1)
            method_name = match.group(2)
            
            self.participants.add(service_name)
            
            # Determinar el llamador actual
            caller = self._determine_current_caller(code, match.start())
            
            self.interactions.append({
                'from': caller,
                'to': service_name,
                'message': method_name,
                'type': 'async' if 'await' in match.group(0) else 'sync'
            })
    
    def _extract_http_calls(self, code: str):
        """Extrae llamadas HTTP y API."""
        # Fetch API
        fetch_pattern = r'(?:await\s+)?fetch\s*\([^)]+\)'
        
        for match in re.finditer(fetch_pattern, code):
            self.participants.add("External API")
            
            caller = self._determine_current_caller(code, match.start())
            
            self.interactions.append({
                'from': caller,
                'to': 'External API',
                'message': 'HTTP Request',
                'type': 'async' if 'await' in match.group(0) else 'sync'
            })
        
        # Axios
        axios_patterns = [
            r'(?:await\s+)?axios\.(get|post|put|delete|patch)\s*\([^)]+\)',
            r'(?:await\s+)?axios\s*\([^)]+\)'
        ]
        
        for pattern in axios_patterns:
            for match in re.finditer(pattern, code):
                self.participants.add("External API")
                
                caller = self._determine_current_caller(code, match.start())
                
                self.interactions.append({
                    'from': caller,
                    'to': 'External API',
                    'message': 'HTTP Request',
                    'type': 'async' if 'await' in match.group(0) else 'sync'
                })
    
    def _extract_database_calls(self, code: str):
        """Extrae llamadas a base de datos."""
        # Mongoose
        mongoose_pattern = r'(\w+)\.(?:find|findOne|findById|create|update|delete|save)\s*\([^)]*\)'
        
        for match in re.finditer(mongoose_pattern, code):
            model_name = match.group(1)
            
            self.participants.add("Database")
            
            caller = self._determine_current_caller(code, match.start())
            
            self.interactions.append({
                'from': caller,
                'to': 'Database',
                'message': f'{model_name} Query',
                'type': 'sync'
            })
        
        # Prisma
        prisma_pattern = r'prisma\.(\w+)\.(?:findMany|findUnique|create|update|delete|upsert)\s*\([^)]*\)'
        
        for match in re.finditer(prisma_pattern, code):
            model_name = match.group(1)
            
            self.participants.add("Prisma")
            self.participants.add("Database")
            
            caller = self._determine_current_caller(code, match.start())
            
            self.interactions.extend([
                {
                    'from': caller,
                    'to': 'Prisma',
                    'message': f'{model_name} Operation',
                    'type': 'sync'
                },
                {
                    'from': 'Prisma',
                    'to': 'Database',
                    'message': 'SQL Query',
                    'type': 'sync'
                }
            ])
    
    def _extract_middleware_calls(self, code: str):
        """Extrae llamadas de middleware."""
        # Express middleware
        middleware_pattern = r'app\.use\s*\(\s*(\w+)\s*\)'
        
        for match in re.finditer(middleware_pattern, code):
            middleware_name = match.group(1)
            
            self.participants.add(middleware_name)
            
            self.interactions.append({
                'from': 'Router',
                'to': middleware_name,
                'message': 'Process Request',
                'type': 'sync'
            })
        
        # Autenticación middleware
        auth_patterns = [
            r'passport\.authenticate\s*\([^)]+\)',
            r'jwt\.verify\s*\([^)]+\)',
            r'verifyToken\s*\([^)]*\)'
        ]
        
        for pattern in auth_patterns:
            for match in re.finditer(pattern, code):
                self.participants.add("Auth Middleware")
                
                caller = self._determine_current_caller(code, match.start())
                
                self.interactions.append({
                    'from': caller,
                    'to': 'Auth Middleware',
                    'message': 'Verify Authentication',
                    'type': 'sync'
                })
    
    def _analyze_method_calls(self, method_body: str, caller: str):
        """Analiza las llamadas dentro de un método."""
        # Llamadas a métodos de otros objetos
        method_call_pattern = r'(?:await\s+)?(\w+)\.(\w+)\s*\([^)]*\)'
        
        for match in re.finditer(method_call_pattern, method_body):
            object_name = match.group(1)
            method_name = match.group(2)
            
            # Filtrar llamadas triviales
            if object_name in ['console', 'Math', 'Date', 'JSON', 'Object', 'Array']:
                continue
            
            self.participants.add(object_name)
            
            self.interactions.append({
                'from': caller,
                'to': object_name,
                'message': method_name,
                'type': 'async' if 'await' in match.group(0) else 'sync'
            })
        
        # Llamadas a funciones
        function_call_pattern = r'(?:await\s+)?(\w+)\s*\([^)]*\)'
        
        for match in re.finditer(function_call_pattern, method_body):
            function_name = match.group(1)
            
            # Filtrar funciones built-in y palabras clave
            if function_name in ['console', 'require', 'setTimeout', 'setInterval', 'if', 'for', 'while', 'return', 'throw']:
                continue
            
            # Solo agregar si parece ser una función importante
            if function_name[0].isupper() or function_name.endswith('Service') or function_name.endswith('Controller'):
                self.participants.add(function_name)
                
                self.interactions.append({
                    'from': caller,
                    'to': function_name,
                    'message': 'execute',
                    'type': 'async' if 'await' in match.group(0) else 'sync'
                })
    
    def _determine_current_caller(self, code: str, position: int) -> str:
        """Determina el objeto/clase que está haciendo la llamada."""
        # Buscar hacia atrás para encontrar el contexto
        before_code = code[:position]
        
        # Buscar la función/método más cercano
        function_patterns = [
            r'class\s+(\w+).*?(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{[^}]*$',
            r'(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{[^}]*$',
            r'(\w+)\s*:\s*(?:async\s+)?function\s*\([^)]*\)\s*\{[^}]*$'
        ]
        
        for pattern in function_patterns:
            matches = list(re.finditer(pattern, before_code, re.DOTALL))
            if matches:
                last_match = matches[-1]
                if len(last_match.groups()) == 2:
                    return f"{last_match.group(1)}.{last_match.group(2)}"
                else:
                    return last_match.group(1)
        
        return "Unknown"
    
    def _generate_plantuml(self) -> str:
        """Genera el código PlantUML."""
        uml_lines = ['@startuml', '']
        
        # Configuración
        uml_lines.extend([
            'skinparam sequenceArrowThickness 2',
            'skinparam sequenceParticipantBorderThickness 1',
            'skinparam sequenceActorBorderThickness 2',
            'skinparam sequenceGroupBorderThickness 2',
            ''
        ])
        
        # Participantes
        for participant in sorted(self.participants):
            if any(keyword in participant.lower() for keyword in ['client', 'user']):
                uml_lines.append(f'actor {participant}')
            elif any(keyword in participant.lower() for keyword in ['database', 'db']):
                uml_lines.append(f'database {participant}')
            elif any(keyword in participant.lower() for keyword in ['api', 'service']):
                uml_lines.append(f'control {participant}')
            else:
                uml_lines.append(f'participant {participant}')
        
        uml_lines.append('')
        
        # Interacciones
        for interaction in self.interactions:
            from_participant = interaction['from']
            to_participant = interaction['to']
            message = interaction['message']
            interaction_type = interaction['type']
            
            # Tipo de flecha según el tipo de interacción
            if interaction_type == 'async':
                arrow = '->>>'
            else:
                arrow = '->>'
            
            uml_lines.append(f'{from_participant} {arrow} {to_participant}: {message}')
        
        uml_lines.extend(['', '@enduml'])
        
        return '\n'.join(uml_lines)
