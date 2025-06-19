# app/application/services/converters/csharp/usecase_converter.py
import re
from typing import Dict, List, Set

class CSharpUseCaseConverter:
    def __init__(self):
        self.actors: Set[str] = set()
        self.use_cases: List[Dict] = []
        self.relationships: List[Dict] = []
        self.current_controller = ""

    def convert(self, code: str) -> str:
        """Convierte código C# de controladores a diagrama UML de casos de uso en PlantUML"""
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
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)
        # Remove string literals (simplified)
        code = re.sub(r'"[^"]*"', '""', code)
        return code

    def _extract_controllers(self, code: str):
        """Extrae controladores y sus métodos de acción"""
        # Buscar controladores
        controller_pattern = re.compile(
            r'(?:public\s+)?class\s+(\w*Controller)\s*:\s*(?:Controller|ControllerBase)\s*\{',
            re.MULTILINE
        )
        
        for match in controller_pattern.finditer(code):
            controller_name = match.group(1)
            self.current_controller = controller_name.replace('Controller', '')
            
            # Extraer el cuerpo del controlador
            start_idx = match.end()
            controller_body = self._extract_balanced_content(code[start_idx:], '{', '}')
            self._extract_actions(controller_body)

    def _extract_actions(self, controller_body: str):
        """Extrae métodos de acción del controlador"""
        # Buscar métodos públicos con atributos HTTP
        action_pattern = re.compile(
            r'\[Http(Get|Post|Put|Delete|Patch)(?:\("([^"]+)"\))?\]\s*'
            r'(?:\[.*?\]\s*)*'  # Otros atributos opcionales
            r'public\s+(?:async\s+)?(?:Task<)?(?:ActionResult|IActionResult)(?:<[^>]+>)?\??(?:>)?\s+'
            r'(\w+)\s*\([^)]*\)',
            re.MULTILINE | re.DOTALL
        )
        
        for match in action_pattern.finditer(controller_body):
            http_method = match.group(1).upper()
            route = match.group(2) or ""
            method_name = match.group(3)
            
            # Generar nombre del caso de uso basado en el método HTTP y nombre
            use_case_name = self._generate_use_case_name(http_method, method_name, route)
            
            # Determinar actor por defecto (puede ser sobrescrito por comentarios)
            actor = self._determine_default_actor(http_method, method_name)
            
            self.use_cases.append({
                'name': use_case_name,
                'method_name': method_name,
                'http_method': http_method,
                'route': route,
                'controller': self.current_controller,
                'actor': actor
            })

        # Buscar comentarios @Actor para sobrescribir actores
        self._extract_actor_comments(controller_body)

    def _extract_actor_comments(self, controller_body: str):
        """Extrae comentarios especiales @Actor para casos de uso específicos"""
        actor_pattern = re.compile(
            r'//\s*@Actor:\s*(\w+)\s*->\s*(\w+)',
            re.MULTILINE
        )
        
        for match in actor_pattern.finditer(controller_body):
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
        
        # Limpiar nombre del método
        clean_name = re.sub(r'(Get|Post|Put|Delete|Patch)', '', method_name, flags=re.IGNORECASE)
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
        # Buscar palabras clave que indiquen tipos de usuario
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
