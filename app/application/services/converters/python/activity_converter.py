# app/application/services/converters/python/activity_converter.py
import ast
import re
from typing import Dict, List, Optional

class PythonActivityConverter:
    def __init__(self):
        self.activities: List[Dict] = []
        self.decision_points: List[Dict] = []
        self.swimlanes: List[str] = ["Usuario", "Sistema"]
        self.current_function = ""
        self.activity_flow: List[Dict] = []

    def convert(self, code: str) -> str:
        """Convierte código Python de funciones a diagrama UML de actividades en PlantUML"""
        try:
            # Intentar usar AST para análisis preciso
            tree = ast.parse(code)
            self._extract_from_ast(tree)
        except SyntaxError:
            # Fallback a análisis por regex
            self._extract_from_regex(code)
        
        # Generación UML
        plantuml = self._generate_plantuml()
        return plantuml

    def _extract_from_ast(self, tree: ast.AST):
        """Extrae actividades usando AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Buscar funciones marcadas con @Activity en docstring o comentarios
                activity_name = self._extract_activity_name(node)
                if activity_name:
                    self.current_function = node.name
                    self._analyze_function_flow(activity_name, node)

    def _extract_activity_name(self, func_node: ast.FunctionDef) -> Optional[str]:
        """Extrae el nombre de la actividad desde docstring o comentarios"""
        # Verificar docstring
        if (func_node.body and 
            isinstance(func_node.body[0], ast.Expr) and 
            isinstance(func_node.body[0].value, ast.Str)):
            docstring = func_node.body[0].value.s
            activity_match = re.search(r'@Activity:\s*([^\n]+)', docstring)
            if activity_match:
                return activity_match.group(1).strip()
        
        # Si no se encuentra en docstring, buscar en comentarios antes de la función
        return None

    def _analyze_function_flow(self, activity_name: str, func_node: ast.FunctionDef):
        """Analiza el flujo de una función"""
        self.activity_flow = []
        self.activity_flow.append({
            'type': 'start',
            'actor': 'Usuario',
            'description': f'Inicia {activity_name}'
        })
        
        # Analizar el cuerpo de la función
        self._analyze_statements(func_node.body, 'Sistema')
        
        # Agregar fin
        self.activity_flow.append({
            'type': 'end',
            'actor': 'Sistema',
            'description': 'Fin del proceso'
        })

    def _analyze_statements(self, statements: List[ast.stmt], current_actor: str):
        """Analiza una lista de statements"""
        for stmt in statements:
            self._analyze_statement(stmt, current_actor)

    def _analyze_statement(self, stmt: ast.stmt, current_actor: str):
        """Analiza un statement individual"""
        if isinstance(stmt, ast.If):
            # Punto de decisión
            condition = self._extract_condition(stmt.test)
            self._add_decision_point(condition, current_actor)
            
            # Analizar rama then
            self._analyze_statements(stmt.body, current_actor)
            
            # Analizar rama else si existe
            if stmt.orelse:
                self._analyze_statements(stmt.orelse, current_actor)
        
        elif isinstance(stmt, ast.Return):
            # Return puede indicar respuesta al usuario
            if isinstance(stmt.value, ast.Call):
                func_name = self._extract_function_name(stmt.value.func)
                if any(keyword in func_name.lower() for keyword in ['jsonify', 'render', 'redirect']):
                    self.activity_flow.append({
                        'type': 'activity',
                        'actor': 'Usuario',
                        'description': 'Recibe respuesta'
                    })
        
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            # Llamada a función
            func_name = self._extract_function_name(stmt.value.func)
            
            # Determinar si es actividad del sistema
            if self._is_system_activity(func_name):
                description = self._humanize_function_name(func_name)
                self.activity_flow.append({
                    'type': 'activity',
                    'actor': 'Sistema',
                    'description': description
                })

    def _extract_from_regex(self, code: str):
        """Extrae actividades usando regex como fallback"""
        code = self._normalize_code(code)
        
        # Buscar funciones marcadas con @Activity
        activity_pattern = re.compile(
            r'#\s*@Activity:\s*([^\n]+).*?def\s+(\w+)',
            re.MULTILINE | re.DOTALL
        )
        
        for match in activity_pattern.finditer(code):
            activity_name = match.group(1).strip()
            function_name = match.group(2)
            self.current_function = function_name
            
            # Extraer el cuerpo de la función
            func_body = self._extract_function_body(code, function_name)
            self._analyze_function_body_regex(activity_name, func_body)

    def _analyze_function_body_regex(self, activity_name: str, func_body: str):
        """Analiza el cuerpo de una función usando regex"""
        self.activity_flow = []
        self.activity_flow.append({
            'type': 'start',
            'actor': 'Usuario',
            'description': f'Inicia {activity_name}'
        })
        
        lines = func_body.split('\n')
        current_actor = 'Sistema'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detectar cambios de actor por comentarios
            actor_match = re.match(r'#\s*@(User|System):\s*(.*)', line)
            if actor_match:
                current_actor = "Usuario" if actor_match.group(1) == "User" else "Sistema"
                description = actor_match.group(2).strip()
                self.activity_flow.append({
                    'type': 'activity',
                    'actor': current_actor,
                    'description': description
                })
                continue
            
            # Detectar if statements
            if re.match(r'if\s+.*:', line):
                condition = re.search(r'if\s+(.*?):', line)
                if condition:
                    self._add_decision_point(condition.group(1), current_actor)
                continue
            
            # Detectar returns
            if line.startswith('return'):
                if any(keyword in line for keyword in ['jsonify', 'render', 'redirect']):
                    self.activity_flow.append({
                        'type': 'activity',
                        'actor': 'Usuario',
                        'description': 'Recibe respuesta'
                    })
                continue
            
            # Detectar llamadas a funciones/métodos
            func_call_match = re.search(r'(\w+)\.(\w+)\s*\(|(\w+)\s*\(', line)
            if func_call_match:
                if func_call_match.group(2):  # método de objeto
                    func_name = func_call_match.group(2)
                else:  # función directa
                    func_name = func_call_match.group(3)
                
                if self._is_system_activity(func_name):
                    description = self._humanize_function_name(func_name)
                    self.activity_flow.append({
                        'type': 'activity',
                        'actor': 'Sistema',
                        'description': description
                    })
        
        # Agregar fin
        self.activity_flow.append({
            'type': 'end',
            'actor': current_actor,
            'description': 'Fin del proceso'
        })

    def _extract_condition(self, test_node: ast.expr) -> str:
        """Extrae la condición de un nodo de test"""
        if isinstance(test_node, ast.Compare):
            return "Condición válida"
        elif isinstance(test_node, ast.Name):
            return f"{test_node.id} es verdadero"
        elif isinstance(test_node, ast.UnaryOp) and isinstance(test_node.op, ast.Not):
            return "Condición negativa"
        else:
            return "Condición"

    def _extract_function_name(self, func_node: ast.expr) -> str:
        """Extrae el nombre de una función"""
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            return func_node.attr
        else:
            return "function"

    def _is_system_activity(self, func_name: str) -> bool:
        """Determina si una función es una actividad del sistema"""
        system_keywords = [
            'save', 'create', 'update', 'delete', 'find', 'get', 'fetch',
            'send', 'process', 'validate', 'check', 'calculate', 'generate',
            'execute', 'run', 'handle', 'manage'
        ]
        return any(keyword in func_name.lower() for keyword in system_keywords)

    def _add_decision_point(self, condition: str, actor: str):
        """Agrega un punto de decisión al flujo"""
        self.activity_flow.append({
            'type': 'decision',
            'actor': actor,
            'description': condition,
            'condition': condition
        })

    def _humanize_function_name(self, func_name: str) -> str:
        """Convierte nombres de función a descripciones legibles"""
        # Separar palabras por guiones bajos o camelCase
        words = re.sub(r'([A-Z])', r' \1', func_name).replace('_', ' ').strip().split()
        
        # Mapeo de verbos comunes
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
            'fetch': 'Obtener',
            'send': 'Enviar',
            'calculate': 'Calcular',
            'generate': 'Generar'
        }
        
        if words:
            first_word = words[0].lower()
            if first_word in verb_mapping:
                words[0] = verb_mapping[first_word]
        
        return ' '.join(words).lower()

    def _extract_function_body(self, code: str, function_name: str) -> str:
        """Extrae el cuerpo de una función"""
        pattern = rf'def\s+{function_name}\s*\([^)]*\):\s*\n(.*?)(?=\ndef|\Z)'
        match = re.search(pattern, code, re.DOTALL)
        return match.group(1) if match else ""

    def _normalize_code(self, code: str) -> str:
        """Normaliza el código para análisis"""
        # Preserve @Activity, @User, @System comments
        code = re.sub(r'#(?!\s*@(Activity|User|System)).*', '', code)
        return code

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
