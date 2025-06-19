# app/application/services/converters/php/activity_converter.py
import re
from typing import Dict, List, Optional

class PHPActivityConverter:
    def __init__(self):
        self.activities: List[Dict] = []
        self.decision_points: List[Dict] = []
        self.swimlanes: List[str] = ["Usuario", "Sistema"]
        self.current_method = ""
        self.activity_flow: List[Dict] = []

    def convert(self, code: str) -> str:
        """Convierte código PHP de métodos a diagrama UML de actividades en PlantUML"""
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
        # Remove multi-line comments but preserve @Activity docblocks
        code = re.sub(r'/\*(?!.*@Activity).*?\*/', '', code, flags=re.DOTALL)
        # Remove hash comments but preserve activity markers
        code = re.sub(r'#(?!\s*@(Activity|User|System)).*', '', code)
        # Normalize whitespace but preserve line breaks for flow analysis
        code = re.sub(r'[ \t]+', ' ', code)
        # Remove string literals (simplified)
        code = re.sub(r'"[^"]*"', '""', code)
        code = re.sub(r"'[^']*'", "''", code)
        return code

    def _extract_activity_methods(self, code: str):
        """Extrae métodos marcados con @Activity"""
        # Buscar comentarios @Activity en líneas individuales
        activity_pattern = re.compile(
            r'(?://\s*@Activity:\s*([^\n]+)|#\s*@Activity:\s*([^\n]+))\n.*?'
            r'(?:public|private|protected)\s+function\s+(\w+)\s*\([^)]*\)\s*\{',
            re.MULTILINE | re.DOTALL
        )
        
        for match in activity_pattern.finditer(code):
            activity_name = (match.group(1) or match.group(2) or "").strip()
            method_name = match.group(3)
            self.current_method = method_name
            
            # Extraer el cuerpo del método
            start_idx = match.end()
            method_body = self._extract_balanced_content(code[start_idx:], '{', '}')
            
            # Analizar el flujo del método
            self._analyze_method_flow(activity_name, method_body)

        # También buscar @Activity en docblocks
        self._extract_from_docblocks(code)

    def _extract_from_docblocks(self, code: str):
        """Extrae actividades desde docblocks con @Activity"""
        docblock_pattern = re.compile(
            r'/\*\*.*?@Activity:\s*([^\n\*]+).*?\*/\s*(?:public|private|protected)\s+function\s+(\w+)\s*\([^)]*\)\s*\{',
            re.MULTILINE | re.DOTALL
        )
        
        for match in docblock_pattern.finditer(code):
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
            actor_match = re.match(r'(?://|#)\s*@(User|System):\s*(.*)', line)
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
            
            # Detectar returns con respuestas (interacción con usuario)
            return_patterns = [
                r'return\s+(?:response\(|redirect\(|view\(|json\()',
                r'return\s+back\(\)',
                r'return\s+\$this->render'
            ]
            
            for pattern in return_patterns:
                if re.search(pattern, line):
                    self.activity_flow.append({
                        'type': 'activity',
                        'actor': 'Usuario',
                        'description': 'Recibe respuesta'
                    })
                    break
            
            # Detectar llamadas a servicios (actividades del sistema)
            service_call_patterns = [
                r'\$(\w+Service|\w+Repository)->(\w+)',
                r'\$this->(\w+Service|\w+Repository)->(\w+)',
                r'(\w+)::(\w+)\s*\('
            ]
            
            for pattern in service_call_patterns:
                match = re.search(pattern, line)
                if match:
                    if len(match.groups()) == 2:
                        service = match.group(1)
                        method = match.group(2)
                    else:
                        continue
                    
                    self.activity_flow.append({
                        'type': 'activity',
                        'actor': 'Sistema',
                        'description': f'{self._humanize_method_name(method)}'
                    })
                    break
            
            # Detectar validaciones
            validation_patterns = [
                r'validate\(',
                r'Validator::',
                r'->fails\(\)',
                r'->passes\(\)'
            ]
            
            for pattern in validation_patterns:
                if re.search(pattern, line):
                    self._add_decision_point('Datos válidos', current_actor)
                    break
            
            # Detectar excepciones y errores
            error_patterns = [
                r'throw\s+new\s+\w+Exception',
                r'abort\(',
                r'->error\('
            ]
            
            for pattern in error_patterns:
                if re.search(pattern, line):
                    self.activity_flow.append({
                        'type': 'activity',
                        'actor': 'Usuario',
                        'description': 'Ve mensaje de error'
                    })
                    break

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
        """Convierte nombres de métodos PHP a descripciones legibles"""
        # Separar palabras en camelCase o snake_case
        words = re.sub(r'([A-Z])', r' \1', method_name).replace('_', ' ').strip().split()
        
        # Mapeo de verbos comunes en español
        verb_mapping = {
            'validate': 'Validar',
            'check': 'Verificar',
            'verify': 'Verificar',
            'process': 'Procesar',
            'create': 'Crear',
            'store': 'Guardar',
            'update': 'Actualizar',
            'delete': 'Eliminar',
            'destroy': 'Eliminar',
            'save': 'Guardar',
            'find': 'Buscar',
            'get': 'Obtener',
            'send': 'Enviar',
            'mail': 'Enviar email',
            'dispatch': 'Ejecutar',
            'handle': 'Manejar',
            'execute': 'Ejecutar'
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
