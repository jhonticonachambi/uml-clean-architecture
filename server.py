# Archivo alternativo para iniciar el servidor
import uvicorn
import os
import sys

if __name__ == "__main__":
    # Intentar obtener el puerto de los argumentos de línea de comando
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"El argumento {sys.argv[1]} no es un puerto válido. Usando el puerto 8000 por defecto.")
    
    # También intentar obtener el puerto de las variables de entorno (Render lo establece)
    port = int(os.environ.get("PORT", port))
    
    print(f"Iniciando servidor en 0.0.0.0:{port}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
