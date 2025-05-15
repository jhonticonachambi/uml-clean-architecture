#!/bin/bash
# Script para el proceso de construcción en Render

# Instalar dependencias
pip install -r requirements.txt

# Dar permisos de ejecución a los scripts
chmod +x render.sh

# Crear un archivo .env con la configuración necesaria
echo "HOST=0.0.0.0" > .env
echo "PORT=$PORT" >> .env

echo "Build script completed successfully!"
