from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Dict, List
from uuid import uuid4
from tempfile import mkdtemp
from git import Repo, GitCommandError
import logging
import os
import re
from pathlib import Path
from app.application.services.diagram_factory import DiagramFactory

router = APIRouter()
logger = logging.getLogger(__name__)

cloned_repositories: Dict[str, Dict] = {}

class RepositoryRequest(BaseModel):
    github_url: HttpUrl

class RepositoryResponse(BaseModel):
    repo_id: str
    message: str
    temp_path: str

class FileStat(BaseModel):
    path: str
    size_kb: float
    classes: int
    functions: int
    extension: str
    comments: int
    loc: int
    is_test: bool

class RepoAnalysisResponse(BaseModel):
    total_files: int
    code_files: int
    total_lines: int
    total_classes: int
    total_functions: int
    total_comments: int
    total_loc: int
    files: List[FileStat]

class DiagramRequest(BaseModel):
    repo_id: str
    diagram_type: str
    language: str

class DiagramResponse(BaseModel):
    diagram: str

class ComponentDiagramRequest(BaseModel):
    repo_id: str
    include_external_deps: bool = True
    max_depth: int = None  # Profundidad máxima de directorios a analizar

class PackageDiagramRequest(BaseModel):
    repo_id: str
    include_external_deps: bool = True
    group_by_layer: bool = True  # Agrupar por capas de arquitectura

class AutoDiagramRequest(BaseModel):
    repo_id: str
    diagram_type: str = "class"  # Tipo por defecto, pero se puede cambiar
    auto_detect_language: bool = True  # Detectar lenguaje automáticamente

def clone_github_repository(url: str) -> Dict:
    try:
        temp_path = mkdtemp(prefix="repo_")
        Repo.clone_from(url, temp_path)
        repo_id = str(uuid4())
        return {
            "repo_id": repo_id,
            "temp_path": temp_path,
            "github_url": url
        }
    except GitCommandError as git_err:
        raise RuntimeError(f"Error al ejecutar git: {git_err}")
    except Exception as e:
        raise RuntimeError(f"Fallo al clonar el repositorio: {e}")

def parse_gitignore(path: str) -> List[str]:
    ignore_path = os.path.join(path, ".gitignore")
    patterns = []
    if os.path.exists(ignore_path):
        with open(ignore_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns

def is_ignored(path: str, patterns: List[str]) -> bool:
    for pattern in patterns:
        if Path(path).match(pattern):
            return True
    return False

def analyze_repository(temp_path: str) -> RepoAnalysisResponse:
    valid_extensions = (".ts", ".tsx", ".js", ".py", ".java", ".cs")
    ignore_patterns = parse_gitignore(temp_path)
    files = []
    total_lines = 0
    total_classes = 0
    total_functions = 0
    total_comments = 0
    total_loc = 0

    for root, _, filenames in os.walk(temp_path):
        for fname in filenames:
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, temp_path)
            if is_ignored(rel_path, ignore_patterns):
                continue

            if fname.endswith(valid_extensions):
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        lines = content.splitlines()
                        classes = len(re.findall(r'\bclass\s+\w+', content))
                        functions = len(re.findall(r'\b(def|function|void|public\s+\w+\s+\w+)\b', content))
                        comments = len([l for l in lines if l.strip().startswith(("#", "//", "/*", "*"))])
                        loc = len([l for l in lines if l.strip() and not l.strip().startswith(("#", "//", "/*", "*"))])
                        is_test = bool(re.search(r'test_|\.spec\.', fname.lower())) or "test" in rel_path.lower()

                        files.append(FileStat(
                            path=rel_path,
                            size_kb=round(os.path.getsize(full_path) / 1024, 2),
                            classes=classes,
                            functions=functions,
                            extension=os.path.splitext(fname)[1],
                            comments=comments,
                            loc=loc,
                            is_test=is_test
                        ))

                        total_lines += len(lines)
                        total_classes += classes
                        total_functions += functions
                        total_comments += comments
                        total_loc += loc
                except Exception as e:
                    logger.warning(f"No se pudo analizar {full_path}: {e}")

    return RepoAnalysisResponse(
        total_files=len(files),
        code_files=len(files),
        total_lines=total_lines,
        total_classes=total_classes,
        total_functions=total_functions,
        total_comments=total_comments,
        total_loc=total_loc,
        files=files
    )

def generate_directory_structure(base_path: str, max_depth: int = None) -> str:
    """Genera una representación optimizada de la estructura de directorios"""
    structure_lines = []
    ignore_patterns = parse_gitignore(base_path)
    
    # Optimización: usar max_depth por defecto si no se especifica
    if max_depth is None:
        max_depth = 4  # Limitar a 4 niveles por defecto para mejorar rendimiento
    
    # Contador para limitar archivos procesados (optimización de rendimiento)
    max_files = 500  # Máximo 500 archivos para evitar timeouts
    files_processed = 0
    
    try:
        for root, dirs, files in os.walk(base_path):
            # Verificar límite de archivos procesados
            if files_processed >= max_files:
                break
                
            # Calcular profundidad actual
            level = root.replace(base_path, '').count(os.sep)
            if level > max_depth:
                # Podar directorios que exceden la profundidad máxima
                dirs[:] = []
                continue
                
            rel_path = os.path.relpath(root, base_path)
            if rel_path == '.':
                rel_path = ''
                
            # Filtrar directorios ignorados y comunes que no aportan valor
            if rel_path and (is_ignored(rel_path, ignore_patterns) or 
                           any(skip_dir in rel_path.lower() for skip_dir in 
                               ['node_modules', '.git', '__pycache__', 'bin', 'obj', 'dist', 'build'])):
                dirs[:] = []  # No procesar subdirectorios
                continue
                
            # Agregar directorio actual (solo si es relevante)
            if rel_path and not any(skip_dir in rel_path.lower() for skip_dir in ['test', 'tests', 'spec']):
                structure_lines.append(f"{rel_path}/")
                
            # Filtrar y agregar solo archivos relevantes
            relevant_files = []
            for file in files:
                if files_processed >= max_files:
                    break
                    
                file_path = os.path.join(rel_path, file) if rel_path else file
                if is_ignored(file_path, ignore_patterns):
                    continue
                    
                # Solo incluir archivos de código fuente principales
                if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cs', '.php', '.go', '.rs', '.cpp', '.h')):
                    relevant_files.append(file_path)
                    files_processed += 1
                    
            structure_lines.extend(relevant_files)
            
    except Exception as e:
        logger.warning(f"Error durante la generación de estructura: {e}")
        # Continuar con lo que se ha procesado hasta ahora
    
    return '\n'.join(structure_lines)

def analyze_project_dependencies(base_path: str) -> str:
    """Analiza dependencias del proyecto de forma optimizada"""
    config_content = []
    
    # Archivos de configuración común (limitados para mejor rendimiento)
    config_files = [
        'package.json', 'requirements.txt', 'pom.xml', 'Cargo.toml', 'go.mod'
    ]
    
    # Límite de tamaño de archivo para evitar leer archivos gigantes
    max_file_size = 50 * 1024  # 50KB máximo
    
    for config_file in config_files:
        config_path = os.path.join(base_path, config_file)
        if os.path.exists(config_path):
            try:
                # Verificar tamaño del archivo
                if os.path.getsize(config_path) > max_file_size:
                    config_content.append(f"---CONFIG-{config_file}--- (archivo muy grande, omitido)")
                    continue
                    
                with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Limitar contenido si es muy largo
                    if len(content) > 2000:
                        content = content[:2000] + "...(truncado)"
                    config_content.append(f"---CONFIG-{config_file}---")
                    config_content.append(content)
            except Exception as e:
                logger.warning(f"Error al leer {config_file}: {e}")
    
    return '\n'.join(config_content) if config_content else ""

def collect_files_with_imports(base_path: str, max_files: int = 50) -> str:
    """Recolecta archivos con sus imports para análisis de dependencias"""
    files_content = []
    ignore_patterns = parse_gitignore(base_path)
    file_count = 0
    
    for root, _, files in os.walk(base_path):
        if file_count >= max_files:
            break
            
        for file in files:
            if file_count >= max_files:
                break
                
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, base_path)
            
            if is_ignored(rel_path, ignore_patterns):
                continue
                
            if file.endswith(('.py', '.js', '.ts', '.java', '.cs', '.php', '.go', '.rs')):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Solo incluir las primeras líneas que usualmente contienen imports
                        lines = content.split('\n')
                        import_lines = []
                        
                        for line in lines[:50]:  # Primeras 50 líneas
                            if any(keyword in line for keyword in [
                                'import ', 'from ', 'include ', 'require', 'using ', 'package '
                            ]):
                                import_lines.append(line)
                        
                        if import_lines:
                            files_content.append(f"---FILE---{rel_path}")
                            files_content.append('\n'.join(import_lines))
                            file_count += 1
                            
                except Exception as e:
                    logger.warning(f"Error al leer {file}: {e}")
    
    return '\n'.join(files_content)

def detect_primary_language(base_path: str) -> str:
    """
    Detecta automáticamente el lenguaje principal del repositorio
    basándose en la cantidad de archivos de cada tipo.
    """
    # Mapeo de extensiones a lenguajes
    extension_to_language = {
        '.cs': 'csharp',
        '.java': 'java', 
        '.php': 'php',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.py': 'python'
    }
    
    # Contador de archivos por lenguaje
    language_counts = {
        'csharp': 0,
        'java': 0,
        'php': 0,
        'javascript': 0,
        'typescript': 0, 
        'python': 0
    }
    
    ignore_patterns = parse_gitignore(base_path)
    
    # Recorrer todos los archivos y contar por extensión
    for root, _, files in os.walk(base_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, base_path)
            
            # Saltar archivos ignorados
            if is_ignored(rel_path, ignore_patterns):
                continue
            
            # Obtener extensión del archivo
            _, ext = os.path.splitext(file)
            ext = ext.lower()
            
            # Contar archivo si la extensión está en nuestro mapeo
            if ext in extension_to_language:
                language = extension_to_language[ext]
                language_counts[language] += 1
    
    # Encontrar el lenguaje con más archivos
    if sum(language_counts.values()) == 0:
        # Si no hay archivos de código, usar 'any' como genérico
        return 'any'
    
    # Obtener el lenguaje predominante
    primary_language = max(language_counts, key=language_counts.get)
    
    # Si hay empate o muy pocos archivos, considerar combinaciones comunes
    total_files = sum(language_counts.values())
    max_count = language_counts[primary_language]
    
    # Si JavaScript y TypeScript están juntos, considerarlo como JavaScript
    if language_counts['javascript'] > 0 and language_counts['typescript'] > 0:
        combined_js = language_counts['javascript'] + language_counts['typescript']
        if combined_js > max_count:
            return 'javascript'  # Usar JavaScript como representante
    
    # Si hay muy pocos archivos (menos de 3), usar genérico
    if total_files < 3:
        return 'any'
    
    # Si el lenguaje predominante representa menos del 40% del total, usar genérico
    if max_count / total_files < 0.4:
        return 'any'
    
    logger.info(f"Lenguaje detectado: {primary_language} ({max_count}/{total_files} archivos)")
    return primary_language

def get_language_stats(base_path: str) -> Dict[str, int]:
    """
    Obtiene estadísticas detalladas de archivos por lenguaje.
    Útil para debugging y logging.
    """
    extension_to_language = {
        '.cs': 'C#',
        '.java': 'Java', 
        '.php': 'PHP',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.py': 'Python'
    }
    
    language_counts = {}
    ignore_patterns = parse_gitignore(base_path)
    
    for root, _, files in os.walk(base_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, base_path)
            
            if is_ignored(rel_path, ignore_patterns):
                continue
            
            _, ext = os.path.splitext(file)
            ext = ext.lower()
            
            if ext in extension_to_language:
                language = extension_to_language[ext]
                language_counts[language] = language_counts.get(language, 0) + 1
    
    return language_counts

@router.post("/fetch-repo", response_model=RepositoryResponse)
async def fetch_repository(request: RepositoryRequest):
    try:
        repo_info = clone_github_repository(request.github_url)
        cloned_repositories[repo_info["repo_id"]] = repo_info

        return RepositoryResponse(
            repo_id=repo_info["repo_id"],
            message="Repositorio clonado exitosamente",
            temp_path=repo_info["temp_path"]
        )
    except Exception as e:
        logger.error(f"Error al clonar repositorio: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al clonar repositorio: {str(e)}")

@router.post("/analyze-repo", response_model=RepoAnalysisResponse)
async def analyze_repo(repo_id: str):
    if repo_id not in cloned_repositories:
        raise HTTPException(status_code=404, detail="Repositorio no encontrado")

    temp_path = cloned_repositories[repo_id]["temp_path"]

    try:
        return analyze_repository(temp_path)
    except Exception as e:
        logger.error(f"Error al analizar repositorio: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al analizar el repositorio: {str(e)}")

@router.post("/generate-diagram", response_model=DiagramResponse)
async def generate_diagram(request: DiagramRequest):
    if request.repo_id not in cloned_repositories:
        raise HTTPException(status_code=404, detail="Repositorio no encontrado")

    repo_info = cloned_repositories[request.repo_id]
    base_path = repo_info["temp_path"]
    
    # Detectar lenguaje automáticamente si no se especifica o se pasa 'auto'
    language = request.language
    if language.lower() in ['auto', 'detect', '']:
        language = detect_primary_language(base_path)
        logger.info(f"Lenguaje detectado automáticamente: {language}")
    
    # Obtener estadísticas para logging
    stats = get_language_stats(base_path)
    logger.info(f"Estadísticas del repositorio: {stats}")
    
    combined_code = ""
    
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith((".cs", ".js", ".ts", ".py", ".java", ".php")):
                try:
                    with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
                        combined_code += f.read() + "\n"
                except Exception as e:
                    logger.warning(f"Error al leer archivo {file}: {e}")

    try:
        converter = DiagramFactory.create_converter(language, request.diagram_type)
        diagram = converter.convert(combined_code)
        return DiagramResponse(diagram=diagram)
    except Exception as e:
        logger.error(f"Error al generar diagrama: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al generar diagrama: {str(e)}")

@router.post("/generate-component-diagram", response_model=DiagramResponse)
async def generate_component_diagram(request: ComponentDiagramRequest):
    """
    Genera un diagrama UML de componentes optimizado basado en la estructura del repositorio.
    Analiza la arquitectura del proyecto, componentes, interfaces y dependencias.
    """
    if request.repo_id not in cloned_repositories:
        raise HTTPException(status_code=404, detail="Repositorio no encontrado")

    repo_info = cloned_repositories[request.repo_id]
    base_path = repo_info["temp_path"]
    
    try:
        logger.info(f"Generando diagrama de componentes para repo: {request.repo_id}")
        
        # Aplicar límites por defecto más conservadores para mejor rendimiento
        max_depth = min(request.max_depth or 3, 4)  # Máximo 4 niveles
        
        # Generar estructura de directorios (optimizada)
        directory_structure = generate_directory_structure(base_path, max_depth)
        
        # Limitar el análisis de dependencias solo si es realmente necesario
        project_deps = ""
        if request.include_external_deps:
            try:
                project_deps = analyze_project_dependencies(base_path)
            except Exception as e:
                logger.warning(f"Error al analizar dependencias, continuando sin ellas: {e}")
                project_deps = ""
        
        # Combinar información para el análisis (con límite de tamaño)
        analysis_input = directory_structure
        if project_deps:
            # Limitar el tamaño total del input
            total_length = len(analysis_input) + len(project_deps)
            if total_length > 50000:  # 50KB máximo
                project_deps = project_deps[:25000] + "...(truncado para mejor rendimiento)"
            analysis_input += f"\n\n{project_deps}"
        
        # Verificar que tenemos datos para procesar
        if not analysis_input.strip():
            raise HTTPException(status_code=400, detail="No se encontraron archivos relevantes en el repositorio")
        
        # Crear converter genérico para componentes
        converter = DiagramFactory.create_converter('any', 'component')
        diagram = converter.convert(analysis_input)
        
        logger.info(f"Diagrama de componentes generado exitosamente para repo: {request.repo_id}")
        return DiagramResponse(diagram=diagram)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al generar diagrama de componentes: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al generar diagrama de componentes: {str(e)}")

@router.post("/generate-package-diagram", response_model=DiagramResponse)
async def generate_package_diagram(request: PackageDiagramRequest):
    """
    Genera un diagrama UML de paquetes basado en la estructura y dependencias del repositorio.
    Analiza la organización modular, jerarquías de paquetes y dependencias entre módulos.
    """
    if request.repo_id not in cloned_repositories:
        raise HTTPException(status_code=404, detail="Repositorio no encontrado")

    repo_info = cloned_repositories[request.repo_id]
    base_path = repo_info["temp_path"]
    
    try:
        # Recolectar archivos con imports para análisis de dependencias
        files_with_imports = collect_files_with_imports(base_path)
        
        # Analizar dependencias externas del proyecto si se solicita
        external_deps = ""
        if request.include_external_deps:
            external_deps = analyze_project_dependencies(base_path)
        
        # Combinar información para el análisis
        analysis_input = files_with_imports
        if external_deps:
            analysis_input += f"\n\n{external_deps}"
        
        # Si no hay suficiente información de imports, usar estructura de directorios
        if not files_with_imports.strip():
            directory_structure = generate_directory_structure(base_path)
            analysis_input = directory_structure
            if external_deps:
                analysis_input += f"\n\n{external_deps}"
        
        # Crear converter genérico para paquetes
        converter = DiagramFactory.create_converter('any', 'package')
        diagram = converter.convert(analysis_input)
        
        return DiagramResponse(diagram=diagram)
        
    except Exception as e:
        logger.error(f"Error al generar diagrama de paquetes: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al generar diagrama de paquetes: {str(e)}")

@router.post("/generate-auto-diagram", response_model=DiagramResponse)
async def generate_auto_diagram(request: AutoDiagramRequest):
    """
    🚀 Endpoint INTELIGENTE que detecta automáticamente el lenguaje principal del repositorio
    y genera el diagrama UML correspondiente sin necesidad de especificar el lenguaje manualmente.
    
    - Analiza todos los archivos (.cs, .java, .php, .js, .ts, .py)
    - Detecta el lenguaje predominante automáticamente
    - Genera el diagrama con el convertidor apropiado
    - Incluye estadísticas detalladas en los logs
    """
    if request.repo_id not in cloned_repositories:
        raise HTTPException(status_code=404, detail="Repositorio no encontrado")

    repo_info = cloned_repositories[request.repo_id]
    base_path = repo_info["temp_path"]
    
    try:
        # 🎯 DETECCIÓN AUTOMÁTICA DE LENGUAJE
        if request.auto_detect_language:
            detected_language = detect_primary_language(base_path)
            logger.info(f"🔍 Lenguaje detectado automáticamente: {detected_language}")
        else:
            detected_language = 'any'  # Usar genérico si no se quiere detección
        
        # 📊 Obtener estadísticas detalladas
        stats = get_language_stats(base_path)
        logger.info(f"📊 Estadísticas del repositorio: {stats}")
        
        # 📁 Leer código fuente
        combined_code = ""
        file_count = 0
        
        for root, _, files in os.walk(base_path):
            for file in files:
                if file.endswith((".cs", ".js", ".ts", ".py", ".java", ".php")):
                    try:
                        with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
                            combined_code += f.read() + "\n"
                            file_count += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Error al leer archivo {file}: {e}")
        
        logger.info(f"📖 Archivos procesados: {file_count}")
        
        # 🔧 Crear convertidor con lenguaje detectado
        try:
            converter = DiagramFactory.create_converter(detected_language, request.diagram_type)
            logger.info(f"✅ Convertidor creado: {detected_language} + {request.diagram_type}")
        except ValueError as ve:
            # Si falla con el lenguaje detectado, usar genérico
            logger.warning(f"⚠️ Fallo con {detected_language}, usando genérico: {ve}")
            converter = DiagramFactory.create_converter('any', request.diagram_type)
        
        # 🎨 Generar diagrama
        diagram = converter.convert(combined_code)
        
        logger.info(f"🎉 Diagrama generado exitosamente ({len(diagram)} caracteres)")
        return DiagramResponse(diagram=diagram)
        
    except Exception as e:
        logger.error(f"❌ Error al generar diagrama automático: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al generar diagrama automático: {str(e)}")

@router.get("/repo-language-stats/{repo_id}")
async def get_repo_language_stats(repo_id: str):
    """
    📊 Endpoint para obtener estadísticas detalladas de lenguajes en el repositorio.
    Útil para debugging y verificar la detección automática.
    """
    if repo_id not in cloned_repositories:
        raise HTTPException(status_code=404, detail="Repositorio no encontrado")

    repo_info = cloned_repositories[repo_id]
    base_path = repo_info["temp_path"]
    
    try:
        # Obtener estadísticas
        stats = get_language_stats(base_path)
        detected_language = detect_primary_language(base_path)
        
        return {
            "repo_id": repo_id,
            "detected_primary_language": detected_language,
            "language_stats": stats,
            "total_code_files": sum(stats.values()),
            "github_url": repo_info.get("github_url", ""),
            "supported_languages": ["C#", "Java", "PHP", "JavaScript", "TypeScript", "Python"]
        }
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al obtener estadísticas: {str(e)}")
    
    