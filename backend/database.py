# -*- coding: utf-8 -*-
"""
Configuración de la base de datos y utilidades ORM.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.config import DATABASE_URL

# Crear motor de base de datos
engine = create_engine(DATABASE_URL)

# Crear factory de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear clase base para modelos declarativos
Base = declarative_base()

# Obtener sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
