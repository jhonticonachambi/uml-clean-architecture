# app/application/services/converters/python/sequence_converter.py
import ast
import re
from typing import Dict, List, Set

class PythonSequenceConverter:
    def __init__(self):
        self.participants: Set[str] = set()
        self.interactions: List[Dict] = []
        self.current_class = ""

    def convert(self, code: str) -> str:
        """Convierte código Python a diagrama UML de secuencia en PlantUML"""
        try:
            # Intentar usar AST para análisis preciso
            tree = ast.parse(code)
            self._extract_sequence_from_ast(tree)
        except SyntaxError:
            # Fallback a análisis por regex si hay errores de sintaxis
            self._extract_sequence_from_regex(code)
        
        # Generación UML
        plantuml = self._generate_plantuml()
        return plantuml

    def _extract_sequence_from_ast(self, tree: ast.AST):
        """Extrae información de secuencia usando AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Analizar métodos que pueden representar interacciones
                if not node.name.startswith('_'):  # Métodos públicos
                    self._analyze_function_interactions(node)

    def _analyze_function_interactions(self, func_node: ast.FunctionDef):
        """Analiza las interacciones dentro de una función"""
        self.participants.add("Controller")
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                # Analizar llamadas a métodos
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        object_name = node.func.value.id
                        method_name = node.func.attr
                        
                        # Determinar el tipo de participante
                        participant_type = self._determine_participant_type(object_name, method_name)
                        
                        self.participants.add(participant_type)
                        
                        # Agregar interacción
                        self.interactions.append({
                            'from': 'Controller',
                            'to': participant_type,
                            'message': method_name,
                            'type': 'sync'
                        })
                        
                        # Agregar respuesta implícita
                        self.interactions.append({
                            'from': participant_type,
                            'to': 'Controller',
                            'message': 'resultado',
                            'type': 'return'
                        })

    def _extract_sequence_from_regex(self, code: str):
        """Extrae información de secuencia usando regex como fallback"""
        # Normalizar código
        code = self._normalize_code(code)
        
        # Buscar llamadas a métodos
        method_call_pattern = re.compile(
            r'(\w+)\.(\w+)\s*\([^)]*\)',
            re.MULTILINE
        )
        
        self.participants.add("Controller")
        
        for match in method_call_pattern.finditer(code):
            object_name = match.group(1)
            method_name = match.group(2)
            
            # Filtrar métodos especiales de Python
            if method_name.startswith('__'):
                continue
            
            # Determinar el tipo de participante
            participant_type = self._determine_participant_type(object_name, method_name)
            
            self.participants.add(participant_type)
            
            # Agregar interacción
            self.interactions.append({
                'from': 'Controller',
                'to': participant_type,
                'message': method_name,
                'type': 'sync'
            })

    def _normalize_code(self, code: str) -> str:
        """Limpia el código removiendo comentarios y strings"""
        # Remove comments
        code = re.sub(r'#.*', '', code)
        # Remove docstrings
        code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
        code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)
        # Remove string literals
        code = re.sub(r'"[^"]*"', '""', code)
        code = re.sub(r"'[^']*'", "''", code)
        return code

    def _determine_participant_type(self, object_name: str, method_name: str) -> str:
        """Determina el tipo de participante basado en convenciones Python"""
        object_lower = object_name.lower()
        method_lower = method_name.lower()
        
        # Mapeo basado en nombres comunes en Python
        if any(keyword in object_lower for keyword in ['service', 'business', 'logic']):
            return "Service"
        elif any(keyword in object_lower for keyword in ['repo', 'repository', 'dao', 'db']):
            return "Repository"
        elif any(keyword in object_lower for keyword in ['client', 'api', 'http', 'requests']):
            return "ExternalAPI"
        elif any(keyword in method_lower for keyword in ['save', 'find', 'get', 'delete', 'update', 'create']):
            return "Database"
        elif any(keyword in method_lower for keyword in ['send', 'notify', 'email', 'mail']):
            return "NotificationService"
        elif object_name in ['session', 'db', 'database']:
            return "Database"
        elif object_name in ['request', 'response']:
            return "Usuario"
        else:
            return f"{object_name.capitalize()}Service"

    def _generate_plantuml(self) -> str:
        """Genera el código PlantUML para el diagrama de secuencia"""
        plantuml = ["@startuml"]
        
        # Configuración
        plantuml.extend([
            "skinparam participant {",
            "  BackgroundColor White",
            "  BorderColor Black",
            "}",
            "skinparam sequence {",
            "  ArrowColor #444444",
            "  LifeLineBorderColor #444444",
            "}",
            ""
        ])
        
        # Participantes
        for participant in sorted(self.participants):
            plantuml.append(f"participant {participant}")
        
        plantuml.append("")
        
        # Si no hay interacciones, crear un ejemplo básico
        if not self.interactions:
            plantuml.extend([
                "Usuario -> Controller : solicitud",
                "Controller -> Service : procesar",
                "Service -> Repository : obtener_datos",
                "Repository --> Service : datos",
                "Service --> Controller : resultado",
                "Controller --> Usuario : respuesta"
            ])
        else:
            # Interacciones extraídas
            for interaction in self.interactions:
                arrow = "-->" if interaction['type'] == 'return' else "->"
                plantuml.append(f"{interaction['from']} {arrow} {interaction['to']} : {interaction['message']}")
        
        plantuml.append("@enduml")
        return '\n'.join(plantuml)
