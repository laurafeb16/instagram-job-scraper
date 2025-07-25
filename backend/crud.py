# -*- coding: utf-8 -*-
"""
Operaciones CRUD específicas para los modelos de la aplicación.
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from sqlalchemy.orm import Session

from backend.database import CRUDBase
from backend import models
from backend.logging_config import get_logger

# Configurar logger
logger = get_logger(__name__)

class CRUDProfile(CRUDBase[models.InstagramProfile]):
    """Operaciones CRUD para perfiles de Instagram."""
    
    def get_by_username(self, db: Session, username: str) -> Optional[models.InstagramProfile]:
        """Obtiene un perfil por su nombre de usuario.
        
        Args:
            db: Sesión de base de datos
            username: Nombre de usuario
            
        Returns:
            Perfil encontrado o None
        """
        return db.query(models.InstagramProfile).filter(
            models.InstagramProfile.username == username
        ).first()
    
    def get_or_create(self, db: Session, username: str) -> models.InstagramProfile:
        """Obtiene un perfil existente o crea uno nuevo.
        
        Args:
            db: Sesión de base de datos
            username: Nombre de usuario
            
        Returns:
            Perfil existente o nuevo
        """
        profile = self.get_by_username(db, username)
        if not profile:
            profile = self.create(db, obj_in={
                "username": username,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            logger.info(f"Nuevo perfil creado", username=username)
        
        return profile
    
    def update_last_scraped(self, db: Session, profile_id: int) -> Optional[models.InstagramProfile]:
        """Actualiza la fecha de último scraping.
        
        Args:
            db: Sesión de base de datos
            profile_id: ID del perfil
            
        Returns:
            Perfil actualizado o None
        """
        profile = self.get(db, profile_id)
        if profile:
            return self.update(db, db_obj=profile, obj_in={
                "last_scraped": datetime.utcnow()
            })
        return None

class CRUDPost(CRUDBase[models.Post]):
    """Operaciones CRUD para posts."""
    
    def get_by_shortcode(self, db: Session, shortcode: str) -> Optional[models.Post]:
        """Obtiene un post por su shortcode.
        
        Args:
            db: Sesión de base de datos
            shortcode: Código corto único del post
            
        Returns:
            Post encontrado o None
        """
        return db.query(models.Post).filter(
            models.Post.shortcode == shortcode
        ).first()
    
    def get_by_profile(
        self, db: Session, profile_id: int, skip: int = 0, limit: int = 100
    ) -> List[models.Post]:
        """Obtiene posts de un perfil específico.
        
        Args:
            db: Sesión de base de datos
            profile_id: ID del perfil
            skip: Número de registros a omitir
            limit: Número máximo de registros a devolver
            
        Returns:
            Lista de posts
        """
        return db.query(models.Post).filter(
            models.Post.profile_id == profile_id
        ).offset(skip).limit(limit).all()
    
    def get_job_posts(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[models.Post]:
        """Obtiene posts marcados como ofertas laborales.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a omitir
            limit: Número máximo de registros a devolver
            
        Returns:
            Lista de posts
        """
        return db.query(models.Post).filter(
            models.Post.is_job_post == True
        ).offset(skip).limit(limit).all()
    
    def create_from_scraper(
        self, db: Session, profile_id: int, post_data: Dict[str, Any]
    ) -> models.Post:
        """Crea un post a partir de datos del scraper.
        
        Args:
            db: Sesión de base de datos
            profile_id: ID del perfil
            post_data: Datos extraídos por el scraper
            
        Returns:
            Post creado
        """
        # Extraer campos relevantes
        obj_in = {
            "profile_id": profile_id,
            "shortcode": post_data.get("shortcode"),
            "caption": post_data.get("caption"),
            "timestamp": post_data.get("timestamp"),
            "image_path": post_data.get("local_image_path"),
            "is_job_post": post_data.get("is_job_post", False),
            "ocr_text": post_data.get("ocr_text")
        }
        
        # Crear post
        return self.create(db, obj_in=obj_in)

class CRUDJobPost(CRUDBase[models.JobPost]):
    """Operaciones CRUD para ofertas laborales."""
    
    def create_from_extractor(
        self, db: Session, post_id: int, job_info: Dict[str, Any]
    ) -> models.JobPost:
        """Crea una oferta laboral a partir de datos del extractor.
        
        Args:
            db: Sesión de base de datos
            post_id: ID del post relacionado
            job_info: Información extraída de la oferta
            
        Returns:
            Oferta laboral creada
        """
        # Extraer campos relevantes
        obj_in = {
            "post_id": post_id,
            "company": job_info.get("company"),
            "title": job_info.get("title"),
            "area": job_info.get("area", "general"),
            "skills": job_info.get("skills", []),
            "benefits": job_info.get("benefits", []),
            "deadline": job_info.get("deadline"),
            "is_open": job_info.get("is_open", True)
        }
        
        # Crear oferta
        return self.create(db, obj_in=obj_in)
    
    def get_by_company(
        self, db: Session, company: str, skip: int = 0, limit: int = 100
    ) -> List[models.JobPost]:
        """Obtiene ofertas laborales de una empresa específica.
        
        Args:
            db: Sesión de base de datos
            company: Nombre de la empresa
            skip: Número de registros a omitir
            limit: Número máximo de registros a devolver
            
        Returns:
            Lista de ofertas laborales
        """
        return db.query(models.JobPost).filter(
            models.JobPost.company.ilike(f"%{company}%")
        ).offset(skip).limit(limit).all()
    
    def get_by_area(
        self, db: Session, area: str, skip: int = 0, limit: int = 100
    ) -> List[models.JobPost]:
        """Obtiene ofertas laborales de un área específica.
        
        Args:
            db: Sesión de base de datos
            area: Área tecnológica
            skip: Número de registros a omitir
            limit: Número máximo de registros a devolver
            
        Returns:
            Lista de ofertas laborales
        """
        return db.query(models.JobPost).filter(
            models.JobPost.area == area
        ).offset(skip).limit(limit).all()
    
    def get_open_jobs(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[models.JobPost]:
        """Obtiene ofertas laborales abiertas.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a omitir
            limit: Número máximo de registros a devolver
            
        Returns:
            Lista de ofertas laborales
        """
        return db.query(models.JobPost).filter(
            models.JobPost.is_open == True
        ).offset(skip).limit(limit).all()

# Instancias de CRUD para usar en la aplicación
profile = CRUDProfile(models.InstagramProfile)
post = CRUDPost(models.Post)
job_post = CRUDJobPost(models.JobPost)