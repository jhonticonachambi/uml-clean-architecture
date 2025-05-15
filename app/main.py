# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.infrastructure.database.session import engine, Base
from app.infrastructure.api.routes import auth
from app.infrastructure.api.routes import generar_diagrama_desde_codigo
from app.infrastructure.api.routes import proyecto  # Importar las rutas de proyecto

# Crear todas las tablas en la base de datos (solo para desarrollo)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Autenticación",
    description="Sistema de registro y login con Clean Architecture",
    version="1.0.0"
)

# Configurar CORS (para desarrollo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/api")
app.include_router(generar_diagrama_desde_codigo.router, prefix="/api")
app.include_router(proyecto.router, prefix="/api")  # Registrar las rutas de proyecto

@app.get("/")
def read_root():
    return {
        "message": "Bienvenido a la API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

# Solo para ejecución directa (opcional)
if __name__ == "__main__":
    import uvicorn
    import os
    # Tomar puerto y host de variables de entorno o usar valores predeterminados
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    # Iniciar servidor escuchando en todas las interfaces
    print(f"Starting server at {host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, log_level="info")