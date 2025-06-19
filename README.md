# Instrucciones para correr el proyecto FastAPI

1. Instala las dependencias:

```
pip install -r requirements.txt
```

2. Ejecuta el servidor de desarrollo con recarga automática:

```
uvicorn app.main:app --reload
```

- Asegúrate de que el archivo `main.py` esté dentro de la carpeta `app` y que contenga la instancia de FastAPI llamada `app`.
- El parámetro `--reload` permite que el servidor se reinicie automáticamente al detectar cambios en el código.

3. Accede a la documentación interactiva en:

- [http://localhost:8000/docs](http://localhost:8000/docs)
- [http://localhost:8000/redoc](http://localhost:8000/redoc)

