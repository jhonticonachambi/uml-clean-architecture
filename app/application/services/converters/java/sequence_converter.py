import re
from typing import Dict, List, Set, Optional

class JavaSequenceConverter:
    def __init__(self):
        self.participants: Set[str] = set()
        self.interactions: List[Dict] = []
        self.current_class = ""
        self.stack: List[Dict] = []

    def convert(self, code: str) -> str:
        """Convierte código Java a diagrama UML de secuencia en PlantUML"""
        # Preprocesamiento
        code = self._normalize_code(code)
        
        # Extracción de elementos
        self._extract_sequence_info(code)
        
        # Generación UML
        plantuml = self._generate_plantuml()
        return plantuml

    def _normalize_code(self, code: str) -> str:
        """Limpia el código removiendo comentarios y literales de string"""
        # Remove single-line comments
        code = re.sub(r'//.*', '', code)
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)
        # Remove string literals (simplified)
        code = re.sub(r'"[^"]*"', '""', code)
        return code.strip()

    def _extract_sequence_info(self, code: str):
        """Extrae información de secuencia desde métodos Java"""
        # Primero identificar la clase principal
        class_match = re.search(r'class\s+(\w+)', code)
        if class_match:
            self.current_class = class_match.group(1)
            self.participants.add(self.current_class)
        
        # Extraer métodos públicos (asumimos que son puntos de entrada)
        method_pattern = re.compile(
            r'(public|protected)\s+(\w+)\s+(\w+)\s*\(([^)]*)\)\s*\{([^{}]*)\}',
            re.DOTALL
        )
        
        for match in method_pattern.finditer(code):
            modifier, return_type, method_name, params, body = match.groups()
            
            # Solo procesamos métodos públicos
            if modifier == 'public':
                self._analyze_method_interactions(method_name, body)

    def _analyze_method_interactions(self, method_name: str, method_body: str):
        """Analiza las interacciones dentro de un método"""
        # Agregar al usuario como participante inicial
        self.participants.add("Client")
        
        # Primera interacción: el cliente llama al método
        self.interactions.append({
            'from': "Client",
            'to': self.current_class,
            'message': method_name,
            'type': 'sync'
        })
        
        # Buscar llamadas a métodos de otros objetos
        method_call_pattern = re.compile(
            r'(?:(\w+)\.)?(\w+)\s*\(([^)]*)\)\s*(?:;|\{)',
            re.MULTILINE
        )
        
        for match in method_call_pattern.finditer(method_body):
            object_name, called_method, params = match.groups()
            
            # Si no hay objeto, es un método de la misma clase
            if not object_name:
                continue
                
            # Determinar el tipo de participante
            participant_type = self._determine_participant_type(object_name, called_method)
            
            self.participants.add(participant_type)
            
            # Agregar interacción
            self.interactions.append({
                'from': self.current_class,
                'to': participant_type,
                'message': called_method,
                'type': 'sync'
            })
            
            # Agregar respuesta implícita
            self.interactions.append({
                'from': participant_type,
                'to': self.current_class,
                'message': f"{called_method}Result",
                'type': 'return'
            })

        # Respuesta final al cliente
        self.interactions.append({
            'from': self.current_class,
            'to': "Client",
            'message': f"{method_name}Result",
            'type': 'return'
        })

    def _determine_participant_type(self, object_name: str, method_name: str) -> str:
        """Determina el tipo de participante basado en convenciones Java"""
        object_lower = object_name.lower()
        method_lower = method_name.lower()
        
        # Mapeo basado en nombres comunes
        if any(keyword in object_lower for keyword in ['service', 'business']):
            return f"{object_name}Service"
        elif any(keyword in object_lower for keyword in ['repository', 'dao']):
            return f"{object_name}Repository"
        elif any(keyword in object_lower for keyword in ['client', 'api', 'external']):
            return f"{object_name}Client"
        elif any(keyword in method_lower for keyword in ['save', 'find', 'delete', 'update', 'select']):
            return "Database"
        elif any(keyword in method_lower for keyword in ['send', 'notify', 'email']):
            return "NotificationService"
        else:
            return object_name

    def _generate_plantuml(self) -> str:
        """Genera el código PlantUML para el diagrama de secuencia"""
        plantuml = ["@startuml"]
        
        # Configuración básica
        plantuml.extend([
            "skinparam monochrome true",
            "skinparam shadowing false",
            "skinparam defaultFontName Arial",
            "skinparam defaultFontSize 10",
            "",
        ])
        
        # Participantes (ordenados para mejor visualización)
        ordered_participants = ["Client"] + sorted(
            [p for p in self.participants if p != "Client" and p != self.current_class],
            key=lambda x: ("Service" in x, "Repository" in x, "Database" in x, x)
        ) + [self.current_class]
        
        for participant in ordered_participants:
            plantuml.append(f"participant \"{participant}\" as {participant.replace(' ', '')}")
        
        plantuml.append("")
        
        # Interacciones
        for interaction in self.interactions:
            from_part = interaction['from'].replace(' ', '')
            to_part = interaction['to'].replace(' ', '')
            
            if interaction['type'] == 'return':
                arrow = "-->"
                color = "#777777"
            else:
                arrow = "->"
                color = "#000000"
            
            plantuml.append(f"{from_part} {arrow} {to_part} : <color:{color}>{interaction['message']}")

        plantuml.append("@enduml")
        return '\n'.join(plantuml)