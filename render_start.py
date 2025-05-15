# Este archivo es específicamente para el despliegue en Render
import uvicorn
import os
import sys

if __name__ == "__main__":
    # Usar la variable de entorno PORT proporcionada por Render
    port = os.environ.get("PORT")
    
    # Verificar si PORT está definido
    if port is None:
        print("ADVERTENCIA: La variable de entorno PORT no está definida. Usando puerto 10000 por defecto.")
        port = 10000
    else:
        try:
            port = int(port)
            print(f"Usando puerto {port} de la variable de entorno PORT")
        except ValueError:
            print(f"ADVERTENCIA: El valor de PORT '{port}' no es un número válido. Usando puerto 10000 por defecto.")
            port = 10000
    
    # Mostrar información de diagnóstico
    print(f"Sistema: {sys.platform}")
    print(f"Versión de Python: {sys.version}")
    print(f"Variables de entorno relevantes:")
    print(f"  - PORT: {os.environ.get('PORT', 'No definido')}")
    print(f"  - PYTHONPATH: {os.environ.get('PYTHONPATH', 'No definido')}")
    print(f"  - PATH: {os.environ.get('PATH', 'No definido')}")
    
    # Ejecutar la aplicación en todas las interfaces (0.0.0.0)
    # y en el puerto asignado por Render
    print(f"Iniciando servidor Uvicorn en 0.0.0.0:{port}")
    
    try:
        uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="debug")
    except Exception as e:
        print(f"ERROR al iniciar Uvicorn: {e}")
        # Intentar con una configuración alternativa
        print("Intentando configuración alternativa...")
        try:
            from app.main import app
            uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")
        except Exception as e2:
            print(f"ERROR en la configuración alternativa: {e2}")
            sys.exit(1)
