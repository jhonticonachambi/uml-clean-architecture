# app/infrastructure/api/routes/zip_upload.py
from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import Dict, List, Optional
from uuid import uuid4
from tempfile import mkdtemp
import logging
import os
import re
import zipfile
import shutil
from pathlib import Path
from app.application.services.diagram_factory import DiagramFactory

router = APIRouter()
logger = logging.getLogger(__name__)

uploaded_projects: Dict[str, Dict] = {}

class ZipUploadResponse(BaseModel):
    project_id: str
    message: str
    temp_path: str
    original_filename: str
    extracted_files: int

class FileStat(BaseModel):
    path: str
    size_kb: float
    classes: int
    functions: int
    extension: str
    comments: int
    loc: int
    is_test: bool

class ProjectAnalysisResponse(BaseModel):
    total_files: int
    code_files: int
    total_lines: int
    total_classes: int
    total_functions: int
    total_comments: int
    total_loc: int
    files: List[FileStat]

class ZipDiagramRequest(BaseModel):
    project_id: str
    diagram_type: str
    language: str

class DiagramResponse(BaseModel):
    diagram: str

class ZipComponentDiagramRequest(BaseModel):
    project_id: str
    include_external_deps: bool = True
    max_depth: int = None

class ZipPackageDiagramRequest(BaseModel):
    project_id: str
    include_external_deps: bool = True
    group_by_layer: bool = True

class ZipAutoDiagramRequest(BaseModel):
    project_id: str
    diagram_type: str = "class"
    auto_detect_language: bool = True

def extract_zip_file(uploaded_file: UploadFile) -> Dict:
    """Extrae un archivo ZIP subido a un directorio temporal"""
    try:
        # Crear directorio temporal
        temp_path = mkdtemp(prefix="zip_project_")
        project_id = str(uuid4())
        
        # Guardar archivo ZIP temporalmente
        zip_temp_path = os.path.join(temp_path, uploaded_file.filename)
        
        with open(zip_temp_path, "wb") as buffer:
            shutil.copyfileobj(uploaded_file.file, buffer)
        
        # Extraer ZIP
        extracted_files = 0
        with zipfile.ZipFile(zip_temp_path, 'r') as zip_ref:
            # Filtrar archivos peligrosos
            safe_members = []
            for member in zip_ref.infolist():
                # Evitar path traversal attacks
                if not member.filename.startswith('/') and '..' not in member.filename:
                    safe_members.append(member)
            
            # Extraer archivos seguros
            for member in safe_members:
                try:
                    zip_ref.extract(member, temp_path)
                    extracted_files += 1
                except Exception as e:
                    logger.warning(f"No se pudo extraer {member.filename}: {e}")
        
        # Eliminar archivo ZIP temporal
        os.remove(zip_temp_path)
        
        return {
            "project_id": project_id,
            "temp_path": temp_path,
            "original_filename": uploaded_file.filename,
            "extracted_files": extracted_files
        }
        
    except zipfile.BadZipFile:
        raise RuntimeError("El archivo no es un ZIP válido")
    except Exception as e:
        raise RuntimeError(f"Error al extraer el archivo ZIP: {e}")

def parse_gitignore(path: str) -> List[str]:
    """Parsea archivo .gitignore si existe"""
    ignore_path = os.path.join(path, ".gitignore")
    patterns = []
    if os.path.exists(ignore_path):
        try:
            with open(ignore_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except Exception as e:
            logger.warning(f"Error al leer .gitignore: {e}")
    
    # Agregar patrones por defecto para proyectos
    default_patterns = [
        "node_modules", "__pycache__", "*.pyc", ".git", 
        "bin", "obj", "target", "build", "dist", ".DS_Store"
    ]
    patterns.extend(default_patterns)
    
    return patterns

def is_ignored(path: str, patterns: List[str]) -> bool:
    """Verifica si un path debe ser ignorado"""
    for pattern in patterns:
        if Path(path).match(pattern) or pattern in path:
            return True
    return False

def analyze_zip_project(temp_path: str) -> ProjectAnalysisResponse:
    """Analiza el proyecto extraído del ZIP"""
    valid_extensions = (".ts", ".tsx", ".js", ".py", ".java", ".cs", ".php", ".go", ".rs", ".cpp", ".h")
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
                        
                        # Contar clases y funciones
                        classes = len(re.findall(r'\b(class|interface|struct)\s+\w+', content, re.IGNORECASE))
                        functions = len(re.findall(r'\b(def|function|public\s+\w+\s+\w+|private\s+\w+\s+\w+|protected\s+\w+\s+\w+)\b', content))
                        
                        # Contar comentarios
                        comments = len([l for l in lines if l.strip().startswith(("#", "//", "/*", "*", "<!--"))])
                        
                        # Líneas de código (sin comentarios ni líneas vacías)
                        loc = len([l for l in lines if l.strip() and not l.strip().startswith(("#", "//", "/*", "*", "<!--"))])
                        
                        # Detectar archivos de test
                        is_test = bool(re.search(r'(test_|\.spec\.|\.test\.|_test\.|Test\.)', fname.lower())) or "test" in rel_path.lower()

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

    return ProjectAnalysisResponse(
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
    """Genera representación de la estructura de directorios"""
    structure_lines = []
    ignore_patterns = parse_gitignore(base_path)
    
    for root, dirs, files in os.walk(base_path):
        level = root.replace(base_path, '').count(os.sep)
        if max_depth and level > max_depth:
            continue
            
        rel_path = os.path.relpath(root, base_path)
        if rel_path == '.':
            rel_path = ''
            
        if rel_path and is_ignored(rel_path, ignore_patterns):
            continue
            
        if rel_path:
            structure_lines.append(f"{rel_path}/")
            
        for file in files:
            file_path = os.path.join(rel_path, file) if rel_path else file
            if is_ignored(file_path, ignore_patterns):
                continue
                
            if file.endswith(('.py', '.js', '.ts', '.java', '.cs', '.php', '.go', '.rs', '.cpp', '.h',
                           '.json', '.xml', '.yml', '.yaml', '.toml', '.cfg', '.ini')):
                structure_lines.append(file_path)
    
    return '\n'.join(structure_lines)

def analyze_project_dependencies(base_path: str) -> str:
    """Analiza dependencias del proyecto"""
    config_content = []
    config_files = [
        'package.json', 'requirements.txt', 'pom.xml', 'build.gradle', 
        'composer.json', 'Cargo.toml', 'go.mod', 'setup.py', 'pyproject.toml',
        '*.csproj', '*.sln'
    ]
    
    for config_file in config_files:
        if '*' in config_file:
            # Manejar patrones con wildcard
            pattern = config_file.replace('*', '')
            for root, _, files in os.walk(base_path):
                for file in files:
                    if file.endswith(pattern):
                        config_path = os.path.join(root, file)
                        try:
                            with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                config_content.append(f"---CONFIG-{file}---")
                                config_content.append(content)
                        except Exception as e:
                            logger.warning(f"Error al leer {file}: {e}")
        else:
            config_path = os.path.join(base_path, config_file)
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        config_content.append(f"---CONFIG-{config_file}---")
                        config_content.append(content)
                except Exception as e:
                    logger.warning(f"Error al leer {config_file}: {e}")
    
    return '\n'.join(config_content) if config_content else ""

def collect_files_with_imports(base_path: str, max_files: int = 50) -> str:
    """Recolecta archivos con sus imports"""
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
                        lines = content.split('\n')
                        import_lines = []
                        
                        for line in lines[:50]:
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
    """Detecta automáticamente el lenguaje principal"""
    extension_to_language = {
        '.cs': 'csharp',
        '.java': 'java', 
        '.php': 'php',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.py': 'python',
        '.go': 'go',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.c': 'c'
    }
    
    language_counts = {
        'csharp': 0, 'java': 0, 'php': 0, 'javascript': 0, 
        'typescript': 0, 'python': 0, 'go': 0, 'rust': 0, 'cpp': 0, 'c': 0
    }
    
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
                language_counts[language] += 1
    
    if sum(language_counts.values()) == 0:
        return 'any'
    
    primary_language = max(language_counts, key=language_counts.get)
    total_files = sum(language_counts.values())
    max_count = language_counts[primary_language]
    
    # Combinar JS y TS
    if language_counts['javascript'] > 0 and language_counts['typescript'] > 0:
        combined_js = language_counts['javascript'] + language_counts['typescript']
        if combined_js > max_count:
            return 'javascript'
    
    if total_files < 3 or max_count / total_files < 0.4:
        return 'any'
    
    logger.info(f"Lenguaje detectado: {primary_language} ({max_count}/{total_files} archivos)")
    return primary_language

def get_language_stats(base_path: str) -> Dict[str, int]:
    """Obtiene estadísticas de lenguajes"""
    extension_to_language = {
        '.cs': 'C#', '.java': 'Java', '.php': 'PHP',
        '.js': 'JavaScript', '.ts': 'TypeScript', '.py': 'Python',
        '.go': 'Go', '.rs': 'Rust', '.cpp': 'C++', '.c': 'C'
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

# ENDPOINTS

@router.post("/upload-zip", response_model=ZipUploadResponse)
async def upload_zip_project(file: UploadFile = File(...)):
    """
    📁 Sube y extrae un proyecto desde un archivo ZIP
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos ZIP")
    
    if file.size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=400, detail="El archivo es demasiado grande (máximo 50MB)")
    
    try:
        project_info = extract_zip_file(file)
        uploaded_projects[project_info["project_id"]] = project_info

        return ZipUploadResponse(
            project_id=project_info["project_id"],
            message="Proyecto extraído exitosamente",
            temp_path=project_info["temp_path"],
            original_filename=project_info["original_filename"],
            extracted_files=project_info["extracted_files"]
        )
    except Exception as e:
        logger.error(f"Error al subir proyecto ZIP: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al procesar archivo ZIP: {str(e)}")

class ZipAnalysisRequest(BaseModel):
    project_id: str

@router.post("/analyze-zip", response_model=ProjectAnalysisResponse)
async def analyze_zip_project_endpoint(request: ZipAnalysisRequest):
    """
    📊 Analiza un proyecto extraído de ZIP
    """
    if request.project_id not in uploaded_projects:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    temp_path = uploaded_projects[request.project_id]["temp_path"]

    try:
        return analyze_zip_project(temp_path)
    except Exception as e:
        logger.error(f"Error al analizar proyecto: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al analizar el proyecto: {str(e)}")

@router.post("/generate-zip-diagram", response_model=DiagramResponse)
async def generate_zip_diagram(request: ZipDiagramRequest):
    """
    🎨 Genera diagrama UML desde proyecto ZIP
    """
    if request.project_id not in uploaded_projects:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    project_info = uploaded_projects[request.project_id]
    base_path = project_info["temp_path"]
    
    # Detección automática de lenguaje
    language = request.language
    if language.lower() in ['auto', 'detect', '']:
        language = detect_primary_language(base_path)
        logger.info(f"Lenguaje detectado automáticamente: {language}")
    
    stats = get_language_stats(base_path)
    logger.info(f"Estadísticas del proyecto: {stats}")
    
    combined_code = ""
    
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith((".cs", ".js", ".ts", ".py", ".java", ".php", ".go", ".rs")):
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

@router.post("/generate-zip-component-diagram", response_model=DiagramResponse)
async def generate_zip_component_diagram(request: ZipComponentDiagramRequest):
    """
    🏗️ Genera diagrama de componentes desde proyecto ZIP
    """
    if request.project_id not in uploaded_projects:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    project_info = uploaded_projects[request.project_id]
    base_path = project_info["temp_path"]
    
    try:
        directory_structure = generate_directory_structure(base_path, request.max_depth)
        
        project_deps = ""
        if request.include_external_deps:
            project_deps = analyze_project_dependencies(base_path)
        
        analysis_input = directory_structure
        if project_deps:
            analysis_input += f"\n\n{project_deps}"
        
        converter = DiagramFactory.create_converter('any', 'component')
        diagram = converter.convert(analysis_input)
        
        return DiagramResponse(diagram=diagram)
        
    except Exception as e:
        logger.error(f"Error al generar diagrama de componentes: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al generar diagrama de componentes: {str(e)}")

@router.post("/generate-zip-package-diagram", response_model=DiagramResponse)
async def generate_zip_package_diagram(request: ZipPackageDiagramRequest):
    """
    📦 Genera diagrama de paquetes desde proyecto ZIP
    """
    if request.project_id not in uploaded_projects:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    project_info = uploaded_projects[request.project_id]
    base_path = project_info["temp_path"]
    
    try:
        files_with_imports = collect_files_with_imports(base_path)
        
        external_deps = ""
        if request.include_external_deps:
            external_deps = analyze_project_dependencies(base_path)
        
        analysis_input = files_with_imports
        if external_deps:
            analysis_input += f"\n\n{external_deps}"
        
        if not files_with_imports.strip():
            directory_structure = generate_directory_structure(base_path)
            analysis_input = directory_structure
            if external_deps:
                analysis_input += f"\n\n{external_deps}"
        
        converter = DiagramFactory.create_converter('any', 'package')
        diagram = converter.convert(analysis_input)
        
        return DiagramResponse(diagram=diagram)
        
    except Exception as e:
        logger.error(f"Error al generar diagrama de paquetes: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al generar diagrama de paquetes: {str(e)}")

@router.post("/generate-zip-auto-diagram", response_model=DiagramResponse)
async def generate_zip_auto_diagram(request: ZipAutoDiagramRequest):
    """
    🚀 Genera diagrama automático desde proyecto ZIP con detección de lenguaje
    """
    if request.project_id not in uploaded_projects:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    project_info = uploaded_projects[request.project_id]
    base_path = project_info["temp_path"]
    
    try:
        if request.auto_detect_language:
            detected_language = detect_primary_language(base_path)
            logger.info(f"🔍 Lenguaje detectado automáticamente: {detected_language}")
        else:
            detected_language = 'any'
        
        stats = get_language_stats(base_path)
        logger.info(f"📊 Estadísticas del proyecto: {stats}")
        
        combined_code = ""
        file_count = 0
        
        for root, _, files in os.walk(base_path):
            for file in files:
                if file.endswith((".cs", ".js", ".ts", ".py", ".java", ".php", ".go", ".rs")):
                    try:
                        with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
                            combined_code += f.read() + "\n"
                            file_count += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Error al leer archivo {file}: {e}")
        
        logger.info(f"📖 Archivos procesados: {file_count}")
        
        try:
            converter = DiagramFactory.create_converter(detected_language, request.diagram_type)
            logger.info(f"✅ Convertidor creado: {detected_language} + {request.diagram_type}")
        except ValueError as ve:
            logger.warning(f"⚠️ Fallo con {detected_language}, usando genérico: {ve}")
            converter = DiagramFactory.create_converter('any', request.diagram_type)
        
        diagram = converter.convert(combined_code)
        
        logger.info(f"🎉 Diagrama generado exitosamente ({len(diagram)} caracteres)")
        return DiagramResponse(diagram=diagram)
        
    except Exception as e:
        logger.error(f"❌ Error al generar diagrama automático: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al generar diagrama automático: {str(e)}")

@router.get("/zip-language-stats/{project_id}")
async def get_zip_language_stats(project_id: str):
    """
    📊 Obtiene estadísticas de lenguajes del proyecto ZIP
    """
    if project_id not in uploaded_projects:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    project_info = uploaded_projects[project_id]
    base_path = project_info["temp_path"]
    
    try:
        stats = get_language_stats(base_path)
        detected_language = detect_primary_language(base_path)
        
        return {
            "project_id": project_id,
            "detected_primary_language": detected_language,
            "language_stats": stats,
            "total_code_files": sum(stats.values()),
            "original_filename": project_info.get("original_filename", ""),
            "extracted_files": project_info.get("extracted_files", 0),
            "supported_languages": ["C#", "Java", "PHP", "JavaScript", "TypeScript", "Python", "Go", "Rust", "C++", "C"]
        }
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al obtener estadísticas: {str(e)}")

@router.delete("/cleanup-zip/{project_id}")
async def cleanup_zip_project(project_id: str):
    """
    🗑️ Limpia archivos temporales de un proyecto ZIP
    """
    if project_id not in uploaded_projects:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    try:
        project_info = uploaded_projects[project_id]
        temp_path = project_info["temp_path"]
        
        # Eliminar directorio temporal
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
        
        # Remover del diccionario
        del uploaded_projects[project_id]
        
        return {"message": "Proyecto limpiado exitosamente", "project_id": project_id}
        
    except Exception as e:
        logger.error(f"Error al limpiar proyecto: {e}")
        raise HTTPException(status_code=500, detail=f"Fallo al limpiar proyecto: {str(e)}")
