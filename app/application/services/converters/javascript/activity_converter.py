import re
from typing import List, Dict, Set, Tuple


class JavaScriptActivityConverter:
    """
    Convertidor de código JavaScript/TypeScript a diagramas de actividades UML PlantUML.
    Analiza el flujo de control, decisiones, bucles y actividades en métodos y funciones.
    """
    
    def __init__(self):
        self.activities = []
        self.decisions = []
        self.loops = []
        self.parallel_activities = []
        self.start_end = {'start': None, 'end': None}
        
    def convert_to_plantuml(self, code: str) -> str:
        """
        Convierte código JavaScript/TypeScript a diagrama de actividades PlantUML.
        
        Args:
            code: Código fuente de JavaScript/TypeScript
            
        Returns:
            Diagrama PlantUML como string
        """
        self._reset()
        self._extract_activities(code)
        
        return self._generate_plantuml()
    
    def convert(self, code: str) -> str:
        """
        Método de compatibilidad para el protocolo BaseConverter.
        Delega a convert_to_plantuml.
        """
        return self.convert_to_plantuml(code)
    
    def _reset(self):
        """Reinicia el estado del convertidor."""
        self.activities = []
        self.decisions = []
        self.loops = []
        self.parallel_activities = []
        self.start_end = {'start': None, 'end': None}
    
    def _extract_activities(self, code: str):
        """Extrae actividades del código."""
        # Buscar funciones y métodos principales
        function_patterns = [
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}',
            r'(\w+)\s*:\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}',
            r'const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}',
            r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'  # Métodos de clase
        ]
        
        for pattern in function_patterns:
            for match in re.finditer(pattern, code, re.DOTALL):
                function_name = match.group(1)
                function_body = match.group(2)
                
                # Saltar constructores y métodos triviales
                if function_name in ['constructor'] or len(function_body.strip()) < 10:
                    continue
                
                self._analyze_function_flow(function_name, function_body)
    
    def _analyze_function_flow(self, function_name: str, function_body: str):
        """Analiza el flujo de una función específica."""
        # Establecer inicio
        self.start_end['start'] = f"Start {function_name}"
        
        # Extraer actividades secuenciales
        self._extract_sequential_activities(function_body)
        
        # Extraer decisiones (if/else, switch, ternario)
        self._extract_decisions(function_body)
        
        # Extraer bucles (for, while, forEach, map, etc.)
        self._extract_loops(function_body)
        
        # Extraer actividades paralelas (Promise.all, async/await)
        self._extract_parallel_activities(function_body)
        
        # Extraer manejo de errores
        self._extract_error_handling(function_body)
        
        # Establecer fin
        self.start_end['end'] = f"End {function_name}"
    
    def _extract_sequential_activities(self, code: str):
        """Extrae actividades secuenciales."""
        # Llamadas a métodos y funciones
        method_calls = [
            r'(?:await\s+)?(\w+)\.(\w+)\s*\([^)]*\)',  # obj.method()
            r'(?:await\s+)?(\w+)\s*\([^)]*\)',  # function()
            r'console\.log\s*\([^)]*\)',  # console.log
            r'return\s+([^;\n]+)',  # return statements
        ]
        
        for pattern in method_calls:
            for match in re.finditer(pattern, code):
                if pattern.startswith(r'(?:await\s+)?(\w+)\.(\w+)'):
                    if match.group(1) and match.group(2):
                        activity = f"{match.group(1)}.{match.group(2)}()"
                        self.activities.append({
                            'type': 'activity',
                            'name': activity,
                            'description': f"Call {activity}"
                        })
                elif pattern.startswith(r'(?:await\s+)?(\w+)\s*\('):
                    if match.group(1):
                        activity = f"{match.group(1)}()"
                        self.activities.append({
                            'type': 'activity',
                            'name': activity,
                            'description': f"Call {activity}"
                        })
                elif 'console.log' in pattern:
                    self.activities.append({
                        'type': 'activity',
                        'name': 'Log',
                        'description': 'Log information'
                    })
                elif pattern.startswith(r'return'):
                    if match.group(1):
                        self.activities.append({
                            'type': 'activity',
                            'name': 'Return',
                            'description': f"Return {match.group(1)}"
                        })
        
        # Asignaciones importantes
        assignment_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*([^;\n]+)'
        for match in re.finditer(assignment_pattern, code):
            var_name = match.group(1)
            value = match.group(2).strip()
            
            # Solo actividades importantes
            if any(keyword in value.lower() for keyword in ['new', 'await', 'fetch', 'require', 'import']):
                self.activities.append({
                    'type': 'activity',
                    'name': f"Initialize {var_name}",
                    'description': f"Initialize {var_name} = {value[:30]}..."
                })
        
        # Operaciones HTTP/API
        http_patterns = [
            r'fetch\s*\([^)]+\)',
            r'axios\.\w+\s*\([^)]+\)',
            r'http\.\w+\s*\([^)]+\)',
            r'request\s*\([^)]+\)'
        ]
        
        for pattern in http_patterns:
            for match in re.finditer(pattern, code):
                self.activities.append({
                    'type': 'activity',
                    'name': 'HTTP Request',
                    'description': 'Make HTTP request'
                })
    
    def _extract_decisions(self, code: str):
        """Extrae decisiones del código."""
        # If/else statements
        if_pattern = r'if\s*\(\s*([^)]+)\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}(?:\s*else\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\})?'
        
        for match in re.finditer(if_pattern, code, re.DOTALL):
            condition = match.group(1).strip()
            if_body = match.group(2)
            else_body = match.group(3)
            
            self.decisions.append({
                'type': 'if',
                'condition': condition,
                'if_activities': self._extract_activities_from_block(if_body),
                'else_activities': self._extract_activities_from_block(else_body) if else_body else []
            })
        
        # Switch statements
        switch_pattern = r'switch\s*\(\s*([^)]+)\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        
        for match in re.finditer(switch_pattern, code, re.DOTALL):
            switch_var = match.group(1).strip()
            switch_body = match.group(2)
            
            # Extraer casos
            case_pattern = r'case\s+([^:]+):\s*([^}]*?)(?=case|default|$)'
            cases = []
            
            for case_match in re.finditer(case_pattern, switch_body, re.DOTALL):
                case_value = case_match.group(1).strip()
                case_body = case_match.group(2)
                
                cases.append({
                    'value': case_value,
                    'activities': self._extract_activities_from_block(case_body)
                })
            
            # Default case
            default_match = re.search(r'default:\s*([^}]*)', switch_body, re.DOTALL)
            default_activities = []
            if default_match:
                default_activities = self._extract_activities_from_block(default_match.group(1))
            
            self.decisions.append({
                'type': 'switch',
                'variable': switch_var,
                'cases': cases,
                'default': default_activities
            })
        
        # Operador ternario
        ternary_pattern = r'(\w+)\s*=\s*([^?]+)\?\s*([^:]+):\s*([^;\n]+)'
        
        for match in re.finditer(ternary_pattern, code):
            var_name = match.group(1)
            condition = match.group(2).strip()
            true_value = match.group(3).strip()
            false_value = match.group(4).strip()
            
            self.decisions.append({
                'type': 'ternary',
                'variable': var_name,
                'condition': condition,
                'true_value': true_value,
                'false_value': false_value
            })
    
    def _extract_loops(self, code: str):
        """Extrae bucles del código."""
        # For loops
        for_patterns = [
            r'for\s*\(\s*([^;]+);\s*([^;]+);\s*([^)]+)\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}',
            r'for\s*\(\s*(?:const|let|var)\s+(\w+)\s+(?:in|of)\s+([^)]+)\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        ]
        
        for pattern in for_patterns:
            for match in re.finditer(pattern, code, re.DOTALL):
                if 'in|of' in pattern:
                    # for...in/of loop
                    iterator = match.group(1)
                    iterable = match.group(2)
                    loop_body = match.group(3)
                    
                    self.loops.append({
                        'type': 'for_each',
                        'iterator': iterator,
                        'iterable': iterable.strip(),
                        'activities': self._extract_activities_from_block(loop_body)
                    })
                else:
                    # Traditional for loop
                    init = match.group(1)
                    condition = match.group(2)
                    increment = match.group(3)
                    loop_body = match.group(4)
                    
                    self.loops.append({
                        'type': 'for',
                        'init': init.strip(),
                        'condition': condition.strip(),
                        'increment': increment.strip(),
                        'activities': self._extract_activities_from_block(loop_body)
                    })
        
        # While loops
        while_pattern = r'while\s*\(\s*([^)]+)\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        
        for match in re.finditer(while_pattern, code, re.DOTALL):
            condition = match.group(1).strip()
            loop_body = match.group(2)
            
            self.loops.append({
                'type': 'while',
                'condition': condition,
                'activities': self._extract_activities_from_block(loop_body)
            })
        
        # Array methods (forEach, map, filter, etc.)
        array_method_pattern = r'(\w+)\.(?:forEach|map|filter|reduce|find|some|every)\s*\(\s*(?:async\s+)?\(?\s*([^)]*)\)?\s*=>\s*\{?([^}]*)\}?'
        
        for match in re.finditer(array_method_pattern, code, re.DOTALL):
            array_name = match.group(1)
            params = match.group(2)
            method_body = match.group(3)
            
            self.loops.append({
                'type': 'array_iteration',
                'array': array_name,
                'params': params.strip() if params else 'item',
                'activities': self._extract_activities_from_block(method_body)
            })
    
    def _extract_parallel_activities(self, code: str):
        """Extrae actividades paralelas."""
        # Promise.all
        promise_all_pattern = r'Promise\.all\s*\(\s*\[([^\]]+)\]\s*\)'
        
        for match in re.finditer(promise_all_pattern, code):
            promises = match.group(1)
            promise_list = [p.strip() for p in promises.split(',')]
            
            self.parallel_activities.append({
                'type': 'promise_all',
                'promises': promise_list
            })
        
        # Promise.allSettled
        promise_settled_pattern = r'Promise\.allSettled\s*\(\s*\[([^\]]+)\]\s*\)'
        
        for match in re.finditer(promise_settled_pattern, code):
            promises = match.group(1)
            promise_list = [p.strip() for p in promises.split(',')]
            
            self.parallel_activities.append({
                'type': 'promise_settled',
                'promises': promise_list
            })
        
        # Async/await patterns que sugieren paralelismo
        parallel_await_pattern = r'const\s+\[([^\]]+)\]\s*=\s*await\s+Promise\.all'
        
        for match in re.finditer(parallel_await_pattern, code):
            results = match.group(1)
            result_list = [r.strip() for r in results.split(',')]
            
            self.parallel_activities.append({
                'type': 'parallel_await',
                'results': result_list
            })
    
    def _extract_error_handling(self, code: str):
        """Extrae manejo de errores."""
        # Try/catch blocks
        try_catch_pattern = r'try\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\s*catch\s*\(\s*(\w+)\s*\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}(?:\s*finally\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\})?'
        
        for match in re.finditer(try_catch_pattern, code, re.DOTALL):
            try_body = match.group(1)
            error_var = match.group(2)
            catch_body = match.group(3)
            finally_body = match.group(4)
            
            self.activities.append({
                'type': 'error_handling',
                'try_activities': self._extract_activities_from_block(try_body),
                'catch_activities': self._extract_activities_from_block(catch_body),
                'finally_activities': self._extract_activities_from_block(finally_body) if finally_body else [],
                'error_variable': error_var
            })
        
        # Throw statements
        throw_pattern = r'throw\s+([^;\n]+)'
        
        for match in re.finditer(throw_pattern, code):
            error_expr = match.group(1).strip()
            
            self.activities.append({
                'type': 'activity',
                'name': 'Throw Error',
                'description': f"Throw {error_expr}"
            })
    
    def _extract_activities_from_block(self, block: str) -> List[str]:
        """Extrae actividades de un bloque de código."""
        if not block:
            return []
        
        activities = []
        
        # Llamadas a métodos
        method_pattern = r'(?:await\s+)?(\w+(?:\.\w+)*)\s*\([^)]*\)'
        for match in re.finditer(method_pattern, block):
            method_call = match.group(1)
            if method_call != 'console.log':  # Filtrar logs triviales
                activities.append(method_call)
        
        # Return statements
        return_pattern = r'return\s+([^;\n]+)'
        for match in re.finditer(return_pattern, block):
            activities.append(f"Return {match.group(1)}")
        
        return activities
    
    def _generate_plantuml(self) -> str:
        """Genera el código PlantUML."""
        uml_lines = ['@startuml', '']
        
        # Configuración
        uml_lines.extend([
            'skinparam activityFontSize 12',
            'skinparam activityDiamondBorderColor black',
            'skinparam activityBorderColor black',
            ''
        ])
        
        # Inicio
        if self.start_end['start']:
            uml_lines.append('start')
        
        # Actividades secuenciales
        for activity in self.activities:
            if activity['type'] == 'activity':
                uml_lines.append(f':{activity["description"]};')
            elif activity['type'] == 'error_handling':
                uml_lines.extend([
                    'partition "Try Block" {',
                    *[f'  :{act};' for act in activity['try_activities']],
                    '}',
                    'partition "Catch Block" {',
                    *[f'  :{act};' for act in activity['catch_activities']],
                    '}'
                ])
                if activity['finally_activities']:
                    uml_lines.extend([
                        'partition "Finally Block" {',
                        *[f'  :{act};' for act in activity['finally_activities']],
                        '}'
                    ])
        
        # Decisiones
        for decision in self.decisions:
            if decision['type'] == 'if':
                uml_lines.append(f'if ({decision["condition"]}) then (yes)')
                
                for activity in decision['if_activities']:
                    uml_lines.append(f'  :{activity};')
                
                if decision['else_activities']:
                    uml_lines.append('else (no)')
                    for activity in decision['else_activities']:
                        uml_lines.append(f'  :{activity};')
                
                uml_lines.append('endif')
            
            elif decision['type'] == 'switch':
                uml_lines.append(f'switch ({decision["variable"]})')
                
                for case in decision['cases']:
                    uml_lines.append(f'case ({case["value"]})')
                    for activity in case['activities']:
                        uml_lines.append(f'  :{activity};')
                
                if decision['default']:
                    uml_lines.append('case (default)')
                    for activity in decision['default']:
                        uml_lines.append(f'  :{activity};')
                
                uml_lines.append('endswitch')
            
            elif decision['type'] == 'ternary':
                uml_lines.extend([
                    f'if ({decision["condition"]}) then (yes)',
                    f'  :{decision["variable"]} = {decision["true_value"]};',
                    'else (no)',
                    f'  :{decision["variable"]} = {decision["false_value"]};',
                    'endif'
                ])
        
        # Bucles
        for loop in self.loops:
            if loop['type'] == 'for':
                uml_lines.extend([
                    f':{loop["init"]};',
                    f'while ({loop["condition"]}) is (yes)',
                    *[f'  :{activity};' for activity in loop['activities']],
                    f'  :{loop["increment"]};',
                    'endwhile (no)'
                ])
            
            elif loop['type'] == 'for_each':
                uml_lines.extend([
                    f'while (for each {loop["iterator"]} in {loop["iterable"]}) is (yes)',
                    *[f'  :{activity};' for activity in loop['activities']],
                    'endwhile (no)'
                ])
            
            elif loop['type'] == 'while':
                uml_lines.extend([
                    f'while ({loop["condition"]}) is (yes)',
                    *[f'  :{activity};' for activity in loop['activities']],
                    'endwhile (no)'
                ])
            
            elif loop['type'] == 'array_iteration':
                uml_lines.extend([
                    f':{loop["array"]}.forEach({loop["params"]});',
                    'partition "For Each Item" {',
                    *[f'  :{activity};' for activity in loop['activities']],
                    '}'
                ])
        
        # Actividades paralelas
        for parallel in self.parallel_activities:
            if parallel['type'] in ['promise_all', 'promise_settled', 'parallel_await']:
                uml_lines.append('fork')
                
                if parallel['type'] == 'parallel_await' and 'results' in parallel:
                    for result in parallel['results']:
                        uml_lines.append(f'  :{result};')
                elif 'promises' in parallel:
                    for promise in parallel['promises']:
                        uml_lines.append(f'  :{promise};')
                
                uml_lines.append('end fork')
        
        # Fin
        if self.start_end['end']:
            uml_lines.append('stop')
        
        uml_lines.extend(['', '@enduml'])
        
        return '\n'.join(uml_lines)
