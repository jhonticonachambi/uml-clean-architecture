# app/application/services/converters/java/activity_converter.py
import re
from typing import Dict, List, Optional

class JavaActivityConverter:
    def __init__(self):
        self.activities: List[Dict] = []
        self.decision_points: List[Dict] = []
        self.swimlanes: List[str] = ["Usuario", "Sistema"]
        self.current_method = ""
        self.activity_flow: List[Dict] = []

    def convert(self, code: str) -> str:
        """Convierte código Java de métodos a diagrama UML de actividades en PlantUML"""
        # Preprocesamiento
        code = self._normalize_code(code)
        
        # Extracción de elementos
        self._extract_activity_methods(code)
        
        # Generación UML
        plantuml = self._generate_plantuml()
        return plantuml

    def _normalize_code(self, code: str) -> str:
        """Limpia el código removiendo comentarios excepto los de actividad"""
        # Preserve @Activity, @User, @System comments
        code = re.sub(r'//(?!\s*@(Activity|User|System)).*', '', code)
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Normalize whitespace but preserve line breaks for flow analysis
        code = re.sub(r'[ \t]+', ' ', code)
        # Remove string literals (simplified)
        code = re.sub(r'"[^"]*"', '""', code)
        return code

    def _extract_activity_methods(self, code: str):
        """Extrae métodos marcados con @Activity"""
        # Buscar comentarios @Activity
        activity_pattern = re.compile(
            r'//\s*@Activity:\s*([^\n]+)\n.*?'
            r'public\s+(?:ResponseEntity<?[^>]*>?|[A-Za-z<>]+)\s+'
            r'(\w+)\s*\([^)]*\)\s*\{',
            re.MULTILINE | re.DOTALL
        )
        
        for match in activity_pattern.finditer(code):
            activity_name = match.group(1).strip()
            method_name = match.group(2)
            self.current_method = method_name
            
            # Extraer el cuerpo del método
            start_idx = match.end()
            method_body = self._extract_balanced_content(code[start_idx:], '{', '}')
            
            # Analizar el flujo del método
            self._analyze_method_flow(activity_name, method_body)

    def _analyze_method_flow(self, activity_name: str, method_body: str):
        """Analiza el flujo de control dentro de un método"""
        self.activity_flow = []
        self.activity_flow.append({
            'type': 'start',
            'actor': 'Usuario',
            'description': f'Inicia {activity_name}'
        })
        
        # Analizar líneas del método
        lines = method_body.split('\n')
        current_actor = 'Sistema'  # Por defecto
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detectar cambios de actor por comentarios
            actor_match = re.match(r'//\s*@(User|System):\s*(.*)', line)
            if actor_match:
                current_actor = "Usuario" if actor_match.group(1) == "User" else "Sistema"
                description = actor_match.group(2).strip()
                self.activity_flow.append({
                    'type': 'activity',
                    'actor': current_actor,
                    'description': description
                })
                continue
            
            # Detectar estructuras de control
            if_match = re.match(r'if\s*\(\s*([^)]+)\s*\)', line)
            if if_match:
                condition = if_match.group(1)
                self._add_decision_point(condition, current_actor)
                continue
            
            # Detectar returns con ResponseEntity (interacción con usuario)
            return_response_match = re.search(r'return\s+(?:ResponseEntity|new\s+ResponseEntity)', line)
            if return_response_match:
                self.activity_flow.append({
                    'type': 'activity',
                    'actor': 'Usuario',
                    'description': 'Recibe respuesta'
                })
                continue
            
            # Detectar llamadas a servicios (actividades del sistema)
            service_call_match = re.search(r'(\w+Service|\w+Repository)\.(\w+)', line)
            if service_call_match:
                service = service_call_match.group(1)
                method = service_call_match.group(2)
                self.activity_flow.append({
                    'type': 'activity',
                    'actor': 'Sistema',
                    'description': f'{self._humanize_method_name(method)}'
                })
                continue
            
            # Detectar validaciones
            if any(keyword in line for keyword in ['validate', 'isValid', 'checkValid']):
                self._add_decision_point('Datos válidos', current_actor)
                continue
            
            # Detectar excepciones
            if re.search(r'throw\s+new\s+\w+Exception', line):
                self.activity_flow.append({
                    'type': 'activity',
                    'actor': 'Usuario',
                    'description': 'Ve mensaje de error'
                })
                continue

        # Agregar fin
        self.activity_flow.append({
            'type': 'end',
            'actor': current_actor,
            'description': 'Fin del proceso'
        })

    def _add_decision_point(self, condition: str, actor: str):
        """Agrega un punto de decisión al flujo"""
        self.activity_flow.append({
            'type': 'decision',
            'actor': actor,
            'description': condition,
            'condition': condition
        })

    def _humanize_method_name(self, method_name: str) -> str:
        """Convierte nombres de métodos Java a descripciones legibles"""
        # Separar palabras en camelCase
        words = re.sub(r'([A-Z])', r' \1', method_name).strip().split()
        
        # Mapeo de verbos comunes en español
        verb_mapping = {
            'validate': 'Validar',
            'check': 'Verificar',
            'verify': 'Verificar',
            'process': 'Procesar',
            'create': 'Crear',
            'update': 'Actualizar',
            'delete': 'Eliminar',
            'save': 'Guardar',
            'find': 'Buscar',
            'get': 'Obtener',
            'send': 'Enviar',
            'calculate': 'Calcular'
        }
        
        if words:
            first_word = words[0].lower()
            if first_word in verb_mapping:
                words[0] = verb_mapping[first_word]
        
        return ' '.join(words).lower()

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
        """Genera el código PlantUML para el diagrama de actividades"""
        plantuml = ["@startuml"]
        
        # Configuración
        plantuml.extend([
            "skinparam activity {",
            "  BackgroundColor White",
            "  BorderColor Black",
            "  ArrowColor #444444",
            "}",
            "skinparam note {",
            "  BackgroundColor #FFFACD",
            "}",
            ""
        ])
        
        # Generar swimlanes
        current_actor = None
        pending_else = []
        
        for i, flow_item in enumerate(self.activity_flow):
            # Cambiar de swimlane si es necesario
            if flow_item['actor'] != current_actor:
                if current_actor is not None:
                    plantuml.append("")
                plantuml.append(f"|{flow_item['actor']}|")
                current_actor = flow_item['actor']
            
            # Generar elementos según el tipo
            if flow_item['type'] == 'start':
                plantuml.append("start")
                plantuml.append(f":{flow_item['description']};")
            
            elif flow_item['type'] == 'activity':
                plantuml.append(f":{flow_item['description']};")
            
            elif flow_item['type'] == 'decision':
                condition = flow_item['condition']
                plantuml.append(f"if ({condition}?) then (sí)")
                
                # Buscar el próximo elemento que no sea de decisión para el flujo "sí"
                next_item = self._find_next_non_decision(i + 1)
                if next_item and next_item['actor'] != current_actor:
                    plantuml.append(f"|{next_item['actor']}|")
                    current_actor = next_item['actor']
                
                # Marcar que necesitamos manejar el "else" más tarde
                pending_else.append(i)
            
            elif flow_item['type'] == 'end':
                # Cerrar cualquier if pendiente
                for _ in pending_else:
                    plantuml.append("endif")
                pending_else.clear()
                
                plantuml.append("stop")
        
        plantuml.append("@enduml")
        return '\n'.join(plantuml)

    def _find_next_non_decision(self, start_index: int) -> Optional[Dict]:
        """Encuentra el próximo elemento que no sea una decisión"""
        for i in range(start_index, len(self.activity_flow)):
            if self.activity_flow[i]['type'] != 'decision':
                return self.activity_flow[i]
        return None
