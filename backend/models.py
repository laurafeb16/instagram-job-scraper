# -*- coding: utf-8 -*-
"""
Modelos ORM para la base de datos de Instagram Job Scraper.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped

from backend.database import Base

class InstagramProfile(Base):
    """Modelo para perfiles de Instagram monitoreados."""
    
    __tablename__ = "instagram_profiles"
    
    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String, unique=True, index=True)
    full_name: Optional[str] = Column(String, nullable=True)
    last_scraped: Optional[datetime] = Column(DateTime, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="profile", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        """Representacion de texto del perfil."""
        return f"<InstagramProfile {self.username}>"

class Post(Base):
    """Modelo para posts extraidos de Instagram."""
    
    __tablename__ = "posts"
    
    id: int = Column(Integer, primary_key=True, index=True)
    shortcode: str = Column(String, unique=True, index=True)
    profile_id: int = Column(Integer, ForeignKey("instagram_profiles.id"))
    caption: Optional[str] = Column(Text, nullable=True)
    timestamp: datetime = Column(DateTime, index=True)
    image_path: Optional[str] = Column(String, nullable=True)
    ocr_text: Optional[str] = Column(Text, nullable=True)
    is_job_post: bool = Column(Boolean, default=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    profile: Mapped["InstagramProfile"] = relationship("InstagramProfile", back_populates="posts")
    job: Mapped[Optional["JobPost"]] = relationship("JobPost", back_populates="post", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        """Representacion de texto del post."""
        return f"<Post {self.shortcode}>"

class JobPost(Base):
    """Modelo para ofertas de trabajo extraidas."""
    
    __tablename__ = "job_posts"
    
    id: int = Column(Integer, primary_key=True, index=True)
    post_id: int = Column(Integer, ForeignKey("posts.id"), unique=True)
    company: Optional[str] = Column(String, index=True, nullable=True)
    title: Optional[str] = Column(String, index=True, nullable=True)
    area: str = Column(String, index=True, default="general")
    skills: List[str] = Column(JSON, default=list)
    benefits: List[str] = Column(JSON, default=list)
    deadline: Optional[str] = Column(String, nullable=True)
    is_open: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    post: Mapped["Post"] = relationship("Post", back_populates="job")
    
    def __repr__(self) -> str:
        """Representacion de texto de la oferta laboral."""
        return f"<JobPost {self.id} - {self.title or 'Sin titulo'} at {self.company or 'Desconocida'}>"
