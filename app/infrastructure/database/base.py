# app/infrastructure/database/base.py
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()  # Single source of truth