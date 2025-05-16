# # app/main.py
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.infrastructure.database.session import engine, Base
# from app.infrastructure.api.routes import auth
# from app.infrastructure.api.routes import generar_diagrama_desde_codigo
# from app.infrastructure.api.routes import proyecto  # Importar las rutas de proyecto
# import os

# # Crear todas las tablas en la base de datos (solo para desarrollo)
# # Base.metadata.create_all(bind=engine)

# app = FastAPI(
#     title="API de Autenticación",
#     description="Sistema de registro y login con Clean Architecture",
#     version="1.0.0"
# )

# # Configurar CORS (para desarrollo)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Incluir routers
# app.include_router(auth.router, prefix="/api")
# app.include_router(generar_diagrama_desde_codigo.router, prefix="/api")
# app.include_router(proyecto.router, prefix="/api")  # Registrar las rutas de proyecto

# @app.get("/")
# def read_root():
#     return {
#         "message": "Bienvenido a la API",
#         "docs": "http://localhost:8000/docs",
#         "openapi": "http://localhost:8000/openapi.json"
#     }

# # Solo para ejecución directa (opcional)
# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.environ.get("PORT", 8000))
#     uvicorn.run(app, host="0.0.0.0", port=port)


import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.infrastructure.api.routes import auth, generar_diagrama_desde_codigo, proyecto

app = FastAPI(
    title="API de Autenticación",
    description="Sistema de registro y login con Clean Architecture",
    version="1.0.0"
)

# Configuración de CORS
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
app.include_router(proyecto.router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "message": "Bienvenido a la API",
        "docs": "http://localhost:8000/docs",
        "openapi": "http://localhost:8000/openapi.json"
    }

# Escuchar en el puerto proporcionado por la variable de entorno 'PORT' y en 0.0.0.0
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Usa el puerto desde la variable de entorno, o 8000 por defecto
    uvicorn.run(app, host="0.0.0.0", port=port)  # Escucha en 0.0.0.0 para que sea accesible

