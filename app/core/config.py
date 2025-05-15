# app/core/config.py
import logging

# Habilitar logs detallados para SQLAlchemy
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.DEBUG)

class Settings:
    SECRET_KEY = "tu_clave_secreta"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

settings = Settings()