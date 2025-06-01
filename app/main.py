# /app/main.py
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.infrastructure.api.routes import auth, diagram, proyecto, user, version_diagrama

app = FastAPI(
    title="Diagrama UML Api Rest",
    description="Sistema de gestión de diagramas UML",
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
app.include_router(user.router, prefix="/api")  # ✅ Volver al original
app.include_router(diagram.router, prefix="/api")
app.include_router(version_diagrama.router, prefix="/api")
app.include_router(proyecto.router, prefix="/api")

# Escuchar en el puerto proporcionado por la variable de entorno 'PORT' y en 0.0.0.0
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  
    uvicorn.run(app, host="0.0.0.0", port=port)  

