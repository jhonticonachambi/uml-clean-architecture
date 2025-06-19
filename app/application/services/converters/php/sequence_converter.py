# app/application/services/converters/php/sequence_converter.py
import re
from typing import Dict, List, Set

class PHPSequenceConverter:
    def __init__(self):
        self.participants: Set[str] = set()
        self.interactions: List[Dict] = []
        self.current_class = ""

    def convert(self, code: str) -> str:
        """Convierte código PHP a diagrama UML de secuencia en PlantUML"""
        # Preprocesamiento
        code = self._normalize_code(code)
        
        # Extracción de elementos
        self._extract_sequence_info(code)
        
        # Generación UML
        plantuml = self._generate_plantuml()
        return plantuml

    def _normalize_code(self, code: str) -> str:
        """Limpia el código removiendo comentarios y literales de string"""
        # Remove single-line comments but keep @Sequence comments
        code = re.sub(r'//(?!\s*@Sequence).*', '', code)
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Remove hash comments
        code = re.sub(r'#(?!\s*@Sequence).*', '', code)
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)
        # Remove string literals (simplified)
        code = re.sub(r'"[^"]*"', '""', code)
        code = re.sub(r"'[^']*'", "''", code)
        return code

    def _extract_sequence_info(self, code: str):
        """Extrae información de secuencia desde métodos PHP"""
        # Buscar métodos que pueden representar interacciones
        method_pattern = re.compile(
            r'(?:public|private|protected)\s+function\s+(\w+)\s*\([^)]*\)\s*\{',
            re.MULTILINE
        )
        
        for match in method_pattern.finditer(code):
            method_name = match.group(1)
            
            # Extraer el cuerpo del método
            start_idx = match.end()
            method_body = self._extract_balanced_content(code[start_idx:], '{', '}')
            
            # Analizar las interacciones dentro del método
            self._analyze_method_interactions(method_name, method_body)

    def _analyze_method_interactions(self, method_name: str, method_body: str):
        """Analiza las interacciones dentro de un método"""
        # Agregar participante principal (el controlador)
        self.participants.add("Controller")
        
        # Buscar llamadas a métodos de otros objetos
        method_call_patterns = [
            r'\$(\w+)->(\w+)\s*\([^)]*\)',  # $object->method()
            r'(\w+)::(\w+)\s*\([^)]*\)',    # Class::method()
            r'$this->(\w+)->(\w+)\s*\([^)]*\)'  # $this->property->method()
        ]
        
        for pattern in method_call_patterns:
            for match in re.finditer(pattern, method_body):
                if len(match.groups()) == 2:
                    object_name = match.group(1)
                    called_method = match.group(2)
                    
                    # Determinar el tipo de participante basado en convenciones
                    participant_type = self._determine_participant_type(object_name, called_method)
                    
                    self.participants.add(participant_type)
                    
                    # Agregar interacción
                    self.interactions.append({
                        'from': 'Controller',
                        'to': participant_type,
                        'message': called_method,
                        'type': 'sync'
                    })
                    
                    # Agregar respuesta implícita
                    self.interactions.append({
                        'from': participant_type,
                        'to': 'Controller',
                        'message': 'resultado',
                        'type': 'return'
                    })

        # Buscar returns que indican respuesta al usuario
        if re.search(r'return\s+(?:response\(|redirect\(|view\(|json\()', method_body):
            self.participants.add("Usuario")
            self.interactions.append({
                'from': 'Controller',
                'to': 'Usuario',
                'message': 'respuesta',
                'type': 'return'
            })

    def _determine_participant_type(self, object_name: str, method_name: str) -> str:
        """Determina el tipo de participante basado en convenciones PHP"""
        object_lower = object_name.lower()
        method_lower = method_name.lower()
        
        # Mapeo basado en nombres comunes en PHP/Laravel
        if any(keyword in object_lower for keyword in ['service', 'business']):
            return "Service"
        elif any(keyword in object_lower for keyword in ['repository', 'repo', 'model']):
            return "Repository"
        elif any(keyword in object_lower for keyword in ['client', 'api', 'http', 'guzzle']):
            return "ExternalAPI"
        elif any(keyword in object_lower for keyword in ['db', 'database', 'connection']):
            return "Database"
        elif any(keyword in method_lower for keyword in ['save', 'find', 'create', 'update', 'delete']):
            return "Database"
        elif any(keyword in method_lower for keyword in ['send', 'mail', 'notify', 'dispatch']):
            return "NotificationService"
        elif any(keyword in object_lower for keyword in ['cache', 'redis', 'memcached']):
            return "CacheService"
        elif any(keyword in object_lower for keyword in ['queue', 'job']):
            return "QueueService"
        else:
            return f"{object_name.capitalize()}Service"

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
                "Service -> Repository : obtenerDatos",
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
