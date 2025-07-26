# -*- coding: utf-8 -*-
"""
Configuracion de la base de datos y utilidades ORM.
"""
from typing import Iterator, Optional, List, Dict, Any, TypeVar, Generic, Type
from datetime import datetime

from sqlalchemy import create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from backend.config import DATABASE_URL
from backend.logging_config import get_logger

# Configurar logger
logger = get_logger(__name__)

# Crear motor de base de datos
engine = create_engine(DATABASE_URL)

# Crear factory de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear clase base para modelos declarativos
Base = declarative_base()

# Tipo generico para modelos
ModelType = TypeVar("ModelType", bound=Base)

def get_db() -> Iterator[Session]:
    """Obtiene una sesion de base de datos.
    
    Yields:
        Sesion de base de datos
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CRUDBase(Generic[ModelType]):
    """Clase base para operaciones CRUD genericas."""
    
    def __init__(self, model: Type[ModelType]):
        """Inicializa el repositorio con un modelo especifico.
        
        Args:
            model: Clase del modelo SQLAlchemy
        """
        self.model = model
    
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Obtiene un registro por su ID.
        
        Args:
            db: Sesion de base de datos
            id: ID del registro
            
        Returns:
            Registro encontrado o None
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Obtiene multiples registros con paginacion.
        
        Args:
            db: Sesion de base de datos
            skip: Numero de registros a omitir
            limit: Numero maximo de registros a devolver
            
        Returns:
            Lista de registros
        """
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: Dict[str, Any]) -> ModelType:
        """Crea un nuevo registro.
        
        Args:
            db: Sesion de base de datos
            obj_in: Datos para crear el registro
            
        Returns:
            Registro creado
        """
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Dict[str, Any]
    ) -> ModelType:
        """Actualiza un registro existente.
        
        Args:
            db: Sesion de base de datos
            db_obj: Registro a actualizar
            obj_in: Datos para actualizar
            
        Returns:
            Registro actualizado
        """
        # Actualizar campos del objeto
        for key, value in obj_in.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        
        # Actualizar timestamp
        if hasattr(db_obj, "updated_at"):
            setattr(db_obj, "updated_at", datetime.utcnow())
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Elimina un registro por su ID.
        
        Args:
            db: Sesion de base de datos
            id: ID del registro
            
        Returns:
            Registro eliminado o None
        """
        obj = db.query(self.model).get(id)
        if obj is not None:
            db.delete(obj)
            db.commit()
        return obj
