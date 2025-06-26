# app/application/services/diagram_factory.py
from typing import Protocol
from app.application.services.converters import (
    # C# Converters
    CSharpClassConverter,
    CSharpSequenceConverter,
    CSharpUseCaseConverter,
    CSharpActivityConverter,
    
    # Java Converters
    JavaClassConverter,
    JavaSequenceConverter,
    JavaUseCaseConverter,
    JavaActivityConverter,
    
    # Python Converters
    PythonClassConverter,
    PythonSequenceConverter,
    PythonUseCaseConverter,
    PythonActivityConverter,
    
    # PHP Converters
    PHPClassConverter,
    PHPSequenceConverter,
    PHPUseCaseConverter,
    PHPActivityConverter,
    
    # JavaScript/TypeScript Converters
    JavaScriptClassConverter,
    JavaScriptSequenceConverter,
    JavaScriptUseCaseConverter,
    JavaScriptActivityConverter,
    
    # Generic Converters (language-independent)
    ComponentDiagramConverter,
    PackageDiagramConverter,
)

class BaseConverter(Protocol):
    def convert(self, code: str) -> str: ...

class DiagramFactory:
    @staticmethod
    def create_converter(language: str, diagram_type: str) -> BaseConverter:
        converters = {            # C# Converters
            ('csharp', 'class'): CSharpClassConverter(),
            ('csharp', 'sequence'): CSharpSequenceConverter(),
            ('csharp', 'usecase'): CSharpUseCaseConverter(),
            ('csharp', 'use_case'): CSharpUseCaseConverter(),  # Alias
            ('csharp', 'activity'): CSharpActivityConverter(),
            
            # Java Converters
            ('java', 'class'): JavaClassConverter(),
            ('java', 'sequence'): JavaSequenceConverter(),
            ('java', 'usecase'): JavaUseCaseConverter(),
            ('java', 'use_case'): JavaUseCaseConverter(),  # Alias
            ('java', 'activity'): JavaActivityConverter(),
            
            # Python Converters
            ('python', 'class'): PythonClassConverter(),
            ('python', 'sequence'): PythonSequenceConverter(),
            ('python', 'usecase'): PythonUseCaseConverter(),
            ('python', 'use_case'): PythonUseCaseConverter(),  # Alias
            ('python', 'activity'): PythonActivityConverter(),
            
            # PHP Converters
            ('php', 'class'): PHPClassConverter(),
            ('php', 'sequence'): PHPSequenceConverter(),
            ('php', 'usecase'): PHPUseCaseConverter(),
            ('php', 'use_case'): PHPUseCaseConverter(),  # Alias
            ('php', 'activity'): PHPActivityConverter(),
              # JavaScript/TypeScript Converters
            ('javascript', 'class'): JavaScriptClassConverter(),
            ('javascript', 'sequence'): JavaScriptSequenceConverter(),
            ('javascript', 'usecase'): JavaScriptUseCaseConverter(),
            ('javascript', 'use_case'): JavaScriptUseCaseConverter(),  # Alias
            ('javascript', 'activity'): JavaScriptActivityConverter(),
            
            # TypeScript aliases (same converters as JavaScript)
            ('typescript', 'class'): JavaScriptClassConverter(),
            ('typescript', 'sequence'): JavaScriptSequenceConverter(),
            ('typescript', 'usecase'): JavaScriptUseCaseConverter(),
            ('typescript', 'use_case'): JavaScriptUseCaseConverter(),  # Alias
            ('typescript', 'activity'): JavaScriptActivityConverter(),
            
            # Additional language aliases
            ('js', 'class'): JavaScriptClassConverter(),
            ('js', 'sequence'): JavaScriptSequenceConverter(),
            ('js', 'usecase'): JavaScriptUseCaseConverter(),
            ('js', 'use_case'): JavaScriptUseCaseConverter(),  # Alias
            ('js', 'activity'): JavaScriptActivityConverter(),
            
            ('ts', 'class'): JavaScriptClassConverter(),
            ('ts', 'sequence'): JavaScriptSequenceConverter(),
            ('ts', 'usecase'): JavaScriptUseCaseConverter(),
            ('ts', 'use_case'): JavaScriptUseCaseConverter(),  # Alias
            ('ts', 'activity'): JavaScriptActivityConverter(),
            
            # Generic Converters (language-independent)
            ('any', 'component'): ComponentDiagramConverter(),
            ('any', 'package'): PackageDiagramConverter(),
            
            # Aliases for generic converters with all languages
            ('csharp', 'component'): ComponentDiagramConverter(),
            ('csharp', 'package'): PackageDiagramConverter(),
            ('java', 'component'): ComponentDiagramConverter(),
            ('java', 'package'): PackageDiagramConverter(),
            ('python', 'component'): ComponentDiagramConverter(),
            ('python', 'package'): PackageDiagramConverter(),
            ('php', 'component'): ComponentDiagramConverter(),
            ('php', 'package'): PackageDiagramConverter(),
            ('javascript', 'component'): ComponentDiagramConverter(),
            ('javascript', 'package'): PackageDiagramConverter(),
            ('typescript', 'component'): ComponentDiagramConverter(),
            ('typescript', 'package'): PackageDiagramConverter(),
            ('js', 'component'): ComponentDiagramConverter(),
            ('js', 'package'): PackageDiagramConverter(),
            ('ts', 'component'): ComponentDiagramConverter(),
            ('ts', 'package'): PackageDiagramConverter(),
        }
        
        # Normalizar lenguaje a minúsculas
        language = language.lower()
        diagram_type = diagram_type.lower()
        
        if (language, diagram_type) not in converters:
            available_combinations = sorted(converters.keys())
            raise ValueError(
                f"Unsupported combination: {language} + {diagram_type}. "
                f"Available combinations: {available_combinations}"
            )
        
        return converters[(language, diagram_type)]