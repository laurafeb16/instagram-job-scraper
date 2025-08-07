# -*- coding: utf-8 -*-
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime

Base = declarative_base()

class JobPost(Base):
    __tablename__ = 'job_posts'
    
    id = Column(Integer, primary_key=True)
    post_url = Column(String(255), unique=True)
    image_url = Column(String(255))
    description = Column(Text)
    post_date = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.datetime.utcnow)
    local_image_path = Column(String(255), nullable=True)
    is_carousel = Column(Boolean, default=False)
    
    # Campos adicionales para análisis
    classification_score = Column(Integer, nullable=True)  # Puntuación de clasificación
    is_job_offer = Column(Boolean, default=False)  # Si es oferta laboral
    
    # Relaciones
    extracted_data = relationship("JobData", back_populates="post", cascade="all, delete-orphan")
    carousel_images = relationship("CarouselImage", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<JobPost(id={self.id}, post_date={self.post_date}, is_job={self.is_job_offer})>"

class JobData(Base):
    __tablename__ = 'job_data'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('job_posts.id'))
    
    # Información de la empresa
    company_name = Column(String(255), nullable=True)
    company_industry = Column(String(100), nullable=True)  # Nuevo campo
    
    # Información del puesto
    job_type = Column(String(50), nullable=True)  # vacante, práctica laboral, práctica profesional
    position_title = Column(String(255), nullable=True)
    work_modality = Column(String(50), nullable=True)  # Presencial, remoto, híbrido
    duration = Column(String(100), nullable=True)  # Duración del trabajo/práctica
    
    # Información de contacto (estructurada)
    contact_name = Column(String(255), nullable=True)
    contact_position = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    
    # Requisitos y conocimientos (como JSON para mayor flexibilidad)
    requirements = Column(JSON, nullable=True)  # Lista de requisitos
    knowledge_required = Column(JSON, nullable=True)  # Lista de conocimientos
    functions = Column(JSON, nullable=True)  # Lista de funciones
    benefits = Column(JSON, nullable=True)  # Lista de beneficios
    
    # Requisitos específicos
    experience_required = Column(String(100), nullable=True)
    education_required = Column(String(255), nullable=True)
    
    # Estado y ubicación
    is_active = Column(Boolean, default=True)
    location = Column(String(255), nullable=True)
    
    # Campos de auditoría
    extracted_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relaciones
    post = relationship("JobPost", back_populates="extracted_data")
    image_id = Column(Integer, ForeignKey('carousel_images.id'), nullable=True)
    image = relationship("CarouselImage", back_populates="extracted_data")
    
    def __repr__(self):
        return f"<JobData(id={self.id}, company={self.company_name}, job_type={self.job_type}, active={self.is_active})>"

class CarouselImage(Base):
    __tablename__ = 'carousel_images'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('job_posts.id'))
    image_url = Column(String(255))
    local_image_path = Column(String(255), nullable=True)
    image_order = Column(Integer)
    
    # Campo para texto extraído de cada imagen
    extracted_text = Column(Text, nullable=True)
    
    # Relaciones
    post = relationship("JobPost", back_populates="carousel_images")
    extracted_data = relationship("JobData", back_populates="image", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CarouselImage(id={self.id}, post_id={self.post_id}, order={self.image_order})>"

# Tabla adicional para análisis y métricas
class AnalysisMetrics(Base):
    __tablename__ = 'analysis_metrics'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('job_posts.id'))
    
    # Métricas de análisis
    ocr_confidence = Column(Integer, nullable=True)  # Confianza del OCR (0-100)
    text_length = Column(Integer, nullable=True)  # Longitud del texto extraído
    classification_confidence = Column(Integer, nullable=True)  # Confianza de clasificación
    
    # Indicadores de calidad
    has_contact_info = Column(Boolean, default=False)
    has_requirements = Column(Boolean, default=False)
    has_benefits = Column(Boolean, default=False)
    
    # Análisis temporal
    processed_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relación
    post_id = Column(Integer, ForeignKey('job_posts.id'))
    
    def __repr__(self):
        return f"<AnalysisMetrics(id={self.id}, post_id={self.post_id})>"

def init_db(db_path='sqlite:///data/database.db'):
    """Inicializa la base de datos y crea las tablas si no existen"""
    engine = create_engine(db_path)
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    
    # Opcional: limpiar datos existentes para pruebas
    # db_session.query(AnalysisMetrics).delete()
    # db_session.query(JobData).delete()
    # db_session.query(CarouselImage).delete()
    # db_session.query(JobPost).delete()
    # db_session.commit()
    
    return db_session

def get_job_statistics(db_session):
    """Obtiene estadísticas de las ofertas laborales - CORREGIDO"""
    from sqlalchemy import func
    
    stats = {}
    
    # Total de posts
    stats['total_posts'] = db_session.query(JobPost).count()
    
    # Posts que son ofertas laborales
    stats['job_offers'] = db_session.query(JobPost).filter(JobPost.is_job_offer == True).count()
    
    # Ofertas activas
    stats['active_offers'] = db_session.query(JobData).filter(JobData.is_active == True).count()
    
    # Por tipo de trabajo - CORREGIDO
    job_type_counts = db_session.query(
        JobData.job_type, 
        func.count(JobData.id)
    ).filter(
        JobData.job_type.isnot(None)
    ).group_by(JobData.job_type).all()
    
    stats['by_job_type'] = {job_type: count for job_type, count in job_type_counts}
    
    # Por industria - CORREGIDO
    industry_counts = db_session.query(
        JobData.company_industry,
        func.count(JobData.id)
    ).filter(
        JobData.company_industry.isnot(None)
    ).group_by(JobData.company_industry).all()
    
    stats['by_industry'] = {industry: count for industry, count in industry_counts}
    
    return stats