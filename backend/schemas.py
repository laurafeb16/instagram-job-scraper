# -*- coding: utf-8 -*-
"""
Esquemas Pydantic para validación y serialización de datos.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field, validator, HttpUrl


# Esquemas base
class ProfileBase(BaseModel):
    """Esquema base para perfiles de Instagram."""
    username: str


class PostBase(BaseModel):
    """Esquema base para posts de Instagram."""
    shortcode: str
    caption: Optional[str] = None
    timestamp: datetime
    image_path: Optional[str] = None
    ocr_text: Optional[str] = None
    is_job_post: bool = False


class JobPostBase(BaseModel):
    """Esquema base para ofertas laborales."""
    company: Optional[str] = None
    title: Optional[str] = None
    area: str = "general"
    skills: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    deadline: Optional[str] = None
    is_open: bool = True


# Esquemas para creación
class ProfileCreate(ProfileBase):
    """Esquema para crear perfiles."""
    full_name: Optional[str] = None


class PostCreate(PostBase):
    """Esquema para crear posts."""
    profile_id: int


class JobPostCreate(JobPostBase):
    """Esquema para crear ofertas laborales."""
    post_id: int


# Esquemas para actualización
class ProfileUpdate(BaseModel):
    """Esquema para actualizar perfiles."""
    username: Optional[str] = None
    full_name: Optional[str] = None
    last_scraped: Optional[datetime] = None


class PostUpdate(BaseModel):
    """Esquema para actualizar posts."""
    caption: Optional[str] = None
    image_path: Optional[str] = None
    ocr_text: Optional[str] = None
    is_job_post: Optional[bool] = None


class JobPostUpdate(BaseModel):
    """Esquema para actualizar ofertas laborales."""
    company: Optional[str] = None
    title: Optional[str] = None
    area: Optional[str] = None
    skills: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    deadline: Optional[str] = None
    is_open: Optional[bool] = None


# Esquemas para respuesta
class JobPost(JobPostBase):
    """Esquema de respuesta para ofertas laborales."""
    id: int
    post_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Configuración del esquema."""
        orm_mode = True


class Post(PostBase):
    """Esquema de respuesta para posts."""
    id: int
    profile_id: int
    created_at: datetime
    updated_at: datetime
    job: Optional[JobPost] = None

    class Config:
        """Configuración del esquema."""
        orm_mode = True


class Profile(ProfileBase):
    """Esquema de respuesta para perfiles."""
    id: int
    full_name: Optional[str] = None
    last_scraped: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    posts: List[Post] = []

    class Config:
        """Configuración del esquema."""
        orm_mode = True


# Esquemas para listados y estadísticas
class JobPostSummary(BaseModel):
    """Resumen de una oferta laboral."""
    id: int
    company: Optional[str] = None
    title: Optional[str] = None
    area: str
    created_at: datetime
    is_open: bool

    class Config:
        """Configuración del esquema."""
        orm_mode = True


class AreaStatistics(BaseModel):
    """Estadísticas por área tecnológica."""
    area: str
    count: int
    percentage: float


class CompanyStatistics(BaseModel):
    """Estadísticas por empresa."""
    company: str
    count: int
    percentage: float


class JobStatistics(BaseModel):
    """Estadísticas generales de ofertas laborales."""
    total_jobs: int
    open_jobs: int
    areas: List[AreaStatistics]
    companies: List[CompanyStatistics]
    skills_frequency: Dict[str, int]