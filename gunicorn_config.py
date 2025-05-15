import os

# Configuración para Gunicorn en producción
bind = f"0.0.0.0:{int(os.getenv('PORT', 8000))}"
workers = int(os.getenv('WORKERS', 4))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
