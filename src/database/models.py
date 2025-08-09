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
    company_industry = Column(String(100), nullable=True)
    
    # Información del puesto
    job_type = Column(String(50), nullable=True)  # vacante, práctica laboral, práctica profesional
    position_title = Column(String(255), nullable=True)
    work_modality = Column(String(50), nullable=True)  # Presencial, remoto, híbrido
    duration = Column(String(100), nullable=True)  # Duración del trabajo/práctica
    
    # === NUEVOS CAMPOS MEJORADOS ===
    # Información detallada del puesto
    schedule = Column(String(255), nullable=True)  # Horario de trabajo
    education_level = Column(String(255), nullable=True)  # Nivel educativo específico
    salary_range = Column(String(100), nullable=True)  # Rango salarial
    application_deadline = Column(DateTime, nullable=True)  # Fecha límite de aplicación
    
    # Información de contacto mejorada
    contact_name = Column(String(255), nullable=True)
    contact_position = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_title = Column(String(100), nullable=True)  # Dr., Lcda., Ing.
    contact_department = Column(String(255), nullable=True)  # Departamento específico
    
    # === TECNOLOGÍAS CATEGORIZADAS (JSON) ===
    programming_languages = Column(JSON, nullable=True)  # ["Python", "JavaScript"]
    databases = Column(JSON, nullable=True)  # ["MySQL", "PostgreSQL"]
    cloud_platforms = Column(JSON, nullable=True)  # ["AWS", "Azure"]
    frameworks_tools = Column(JSON, nullable=True)  # ["React", "Docker"]
    office_tools = Column(JSON, nullable=True)  # ["Excel", "PowerPoint"]
    specialized_software = Column(JSON, nullable=True)  # ["MATLAB", "AutoCAD"]
    
    # === HABILIDADES ===
    soft_skills = Column(JSON, nullable=True)  # Lista de habilidades blandas
    technical_skills = Column(JSON, nullable=True)  # Habilidades técnicas generales
    
    # Requisitos y conocimientos (manteniendo compatibilidad)
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
    skills = relationship("JobSkills", back_populates="job_data", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<JobData(id={self.id}, company={self.company_name}, job_type={self.job_type}, active={self.is_active})>"

class JobSkills(Base):
    """Nueva tabla para habilidades detalladas"""
    __tablename__ = 'job_skills'
    
    id = Column(Integer, primary_key=True)
    job_data_id = Column(Integer, ForeignKey('job_data.id'))
    
    skill_category = Column(String(50))  # 'programming', 'database', 'soft_skill', etc.
    skill_name = Column(String(100))
    skill_level = Column(String(50), nullable=True)  # 'básico', 'intermedio', 'avanzado'
    is_required = Column(Boolean, default=True)  # requerido vs deseable
    frequency_score = Column(Integer, default=1)  # qué tan frecuente aparece esta skill
    
    # Campos de auditoría
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relación
    job_data = relationship("JobData", back_populates="skills")
    
    def __repr__(self):
        return f"<JobSkills(skill_name={self.skill_name}, category={self.skill_category}, required={self.is_required})>"

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

class AnalysisMetrics(Base):
    """Tabla mejorada para análisis y métricas"""
    __tablename__ = 'analysis_metrics'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('job_posts.id'))
    
    # Métricas de análisis OCR
    ocr_confidence = Column(Integer, nullable=True)  # Confianza del OCR (0-100)
    text_length = Column(Integer, nullable=True)  # Longitud del texto extraído
    classification_confidence = Column(Integer, nullable=True)  # Confianza de clasificación
    
    # Indicadores de calidad mejorados
    has_contact_info = Column(Boolean, default=False)
    has_requirements = Column(Boolean, default=False)
    has_benefits = Column(Boolean, default=False)
    has_technologies = Column(Boolean, default=False)  # Nuevo
    has_soft_skills = Column(Boolean, default=False)  # Nuevo
    has_schedule = Column(Boolean, default=False)  # Nuevo
    
    # Métricas de extracción
    total_technologies_found = Column(Integer, default=0)
    total_soft_skills_found = Column(Integer, default=0)
    extraction_completeness_score = Column(Integer, nullable=True)  # Puntuación de completitud
    
    # Análisis temporal
    processed_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relación
    post_id = Column(Integer, ForeignKey('job_posts.id'))
    
    def __repr__(self):
        return f"<AnalysisMetrics(id={self.id}, post_id={self.post_id}, completeness={self.extraction_completeness_score})>"

class TechnologyTrends(Base):
    """Nueva tabla para tracking de tendencias tecnológicas"""
    __tablename__ = 'technology_trends'
    
    id = Column(Integer, primary_key=True)
    technology_name = Column(String(100))
    category = Column(String(50))  # programming, database, cloud, etc.
    month_year = Column(String(7))  # formato YYYY-MM
    total_mentions = Column(Integer, default=0)
    active_jobs_count = Column(Integer, default=0)
    industry_breakdown = Column(JSON, nullable=True)  # {"tecnología": 5, "finanzas": 3}
    
    # Campos de auditoría
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<TechnologyTrends(technology={self.technology_name}, month={self.month_year}, mentions={self.total_mentions})>"

def init_db(db_path='sqlite:///data/database.db'):
    """Inicializa la base de datos y crea las tablas si no existen"""
    engine = create_engine(db_path)
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    db_session = Session()
    
    return db_session

def migrate_existing_data(db_session):
    """Migra datos existentes para compatibilidad con nuevos campos"""
    
    print("🔄 Iniciando migración de datos existentes...")
    
    try:
        # Obtener todos los JobData sin los nuevos campos
        jobs = db_session.query(JobData).all()
        
        migrated_count = 0
        for job in jobs:
            # Inicializar nuevos campos con valores por defecto si son None
            if job.programming_languages is None:
                job.programming_languages = []
            if job.databases is None:
                job.databases = []
            if job.cloud_platforms is None:
                job.cloud_platforms = []
            if job.frameworks_tools is None:
                job.frameworks_tools = []
            if job.office_tools is None:
                job.office_tools = []
            if job.specialized_software is None:
                job.specialized_software = []
            if job.soft_skills is None:
                job.soft_skills = []
            if job.technical_skills is None:
                job.technical_skills = []
            
            migrated_count += 1
        
        db_session.commit()
        print(f"✅ Migración completada: {migrated_count} registros actualizados")
        
    except Exception as e:
        print(f"❌ Error en migración: {str(e)}")
        db_session.rollback()

def get_job_statistics(db_session):
    """Obtiene estadísticas de las ofertas laborales - MEJORADO"""
    from sqlalchemy import func
    
    stats = {}
    
    # Estadísticas básicas
    stats['total_posts'] = db_session.query(JobPost).count()
    stats['job_offers'] = db_session.query(JobPost).filter(JobPost.is_job_offer == True).count()
    stats['active_offers'] = db_session.query(JobData).filter(JobData.is_active == True).count()
    
    # Por tipo de trabajo
    job_type_counts = db_session.query(
        JobData.job_type, 
        func.count(JobData.id)
    ).filter(
        JobData.job_type.isnot(None)
    ).group_by(JobData.job_type).all()
    
    stats['by_job_type'] = {job_type: count for job_type, count in job_type_counts}
    
    # Por industria
    industry_counts = db_session.query(
        JobData.company_industry,
        func.count(JobData.id)
    ).filter(
        JobData.company_industry.isnot(None)
    ).group_by(JobData.company_industry).all()
    
    stats['by_industry'] = {industry: count for industry, count in industry_counts}
    
    # === NUEVAS ESTADÍSTICAS MEJORADAS ===
    
    # Ofertas con información completa
    complete_jobs = db_session.query(JobData).filter(
        JobData.is_active == True,
        JobData.contact_email.isnot(None),
        JobData.company_name.isnot(None),
        JobData.requirements.isnot(None)
    ).count()
    stats['complete_offers'] = complete_jobs
    
    # Ofertas con tecnologías especificadas
    tech_jobs = db_session.query(JobData).filter(
        JobData.is_active == True,
        JobData.programming_languages.isnot(None)
    ).count()
    stats['offers_with_tech'] = tech_jobs
    
    # Ofertas con habilidades blandas
    soft_skills_jobs = db_session.query(JobData).filter(
        JobData.is_active == True,
        JobData.soft_skills.isnot(None)
    ).count()
    stats['offers_with_soft_skills'] = soft_skills_jobs
    
    # Por modalidad de trabajo
    modality_counts = db_session.query(
        JobData.work_modality,
        func.count(JobData.id)
    ).filter(
        JobData.work_modality.isnot(None),
        JobData.is_active == True
    ).group_by(JobData.work_modality).all()
    
    stats['by_modality'] = {modality: count for modality, count in modality_counts}
    
    return stats

def get_technology_trends(db_session, months=6):
    """Obtiene tendencias de tecnologías en los últimos meses"""
    
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # Calcular fecha de corte
    cutoff_date = datetime.now() - timedelta(days=months * 30)
    
    # Obtener todas las ofertas activas recientes
    recent_jobs = db_session.query(JobData).join(JobPost).filter(
        JobPost.post_date >= cutoff_date,
        JobData.is_active == True
    ).all()
    
    # Contar tecnologías por categoría
    tech_trends = {
        'programming_languages': {},
        'databases': {},
        'cloud_platforms': {},
        'frameworks_tools': {},
        'total_jobs': len(recent_jobs)
    }
    
    for job in recent_jobs:
        # Contar cada categoría de tecnología
        for category in ['programming_languages', 'databases', 'cloud_platforms', 'frameworks_tools']:
            technologies = getattr(job, category) or []
            for tech in technologies:
                if tech:  # Verificar que no sea None o string vacío
                    tech_trends[category][tech] = tech_trends[category].get(tech, 0) + 1
    
    # Ordenar por popularidad y obtener top 10 de cada categoría
    for category in tech_trends:
        if category != 'total_jobs':
            tech_trends[category] = dict(
                sorted(tech_trends[category].items(), key=lambda x: x[1], reverse=True)[:10]
            )
    
    return tech_trends

def get_soft_skills_analysis(db_session):
    """Análisis de habilidades blandas más demandadas"""
    
    active_jobs = db_session.query(JobData).filter(
        JobData.is_active == True,
        JobData.soft_skills.isnot(None)
    ).all()
    
    skills_count = {}
    industry_skills = {}
    
    for job in active_jobs:
        industry = job.company_industry or "No especificada"
        
        # Inicializar industria si no existe
        if industry not in industry_skills:
            industry_skills[industry] = {}
        
        # Contar habilidades
        soft_skills = job.soft_skills or []
        for skill in soft_skills:
            if skill:  # Verificar que no sea None o vacío
                # Conteo global
                skills_count[skill] = skills_count.get(skill, 0) + 1
                
                # Conteo por industria
                industry_skills[industry][skill] = industry_skills[industry].get(skill, 0) + 1
    
    # Ordenar por popularidad
    top_skills = dict(sorted(skills_count.items(), key=lambda x: x[1], reverse=True)[:15])
    
    # Calcular porcentaje
    total_jobs_with_skills = len(active_jobs)
    skills_percentage = {
        skill: round((count / total_jobs_with_skills) * 100, 1) 
        for skill, count in top_skills.items()
    }
    
    return {
        'top_skills': top_skills,
        'skills_percentage': skills_percentage,
        'by_industry': industry_skills,
        'total_analyzed': total_jobs_with_skills
    }

def create_sample_enhanced_data(db_session):
    """Crea datos de muestra para probar las nuevas funcionalidades"""
    
    print("🎯 Creando datos de muestra con nuevos campos...")
    
    # Verificar si ya existen datos
    existing_jobs = db_session.query(JobData).count()
    if existing_jobs > 0:
        print(f"⚠️  Ya existen {existing_jobs} registros. Saltando creación de datos de muestra.")
        return
    
    # Crear datos de muestra
    sample_data = [
        {
            'company_name': 'Copa Airlines',
            'company_industry': 'aviación',
            'job_type': 'Práctica Profesional',
            'position_title': 'Desarrollador de Software',
            'work_modality': 'Híbrido',
            'schedule': 'Lunes a Viernes de 8:00 AM a 5:00 PM',
            'programming_languages': ['Python', 'JavaScript', 'SQL'],
            'databases': ['PostgreSQL', 'MongoDB'],
            'cloud_platforms': ['AWS', 'Azure'],
            'frameworks_tools': ['React', 'Django', 'Docker'],
            'soft_skills': ['Trabajo en equipo', 'Comunicación', 'Resolución de problemas'],
            'contact_name': 'María González',
            'contact_email': 'maria.gonzalez@copa.com',
            'is_active': True
        },
        {
            'company_name': 'GRUPO MANZ',
            'company_industry': 'tecnología',
            'job_type': 'Práctica Laboral',
            'position_title': 'Analista de Datos',
            'work_modality': 'Presencial',
            'schedule': 'Lunes a Viernes de 7:30 AM a 4:30 PM',
            'programming_languages': ['Python', 'R'],
            'databases': ['MySQL', 'SQLite'],
            'office_tools': ['Excel', 'PowerPoint', 'Power BI'],
            'soft_skills': ['Análisis crítico', 'Atención al detalle', 'Comunicación'],
            'contact_name': 'Carlos Mendoza',
            'contact_email': 'carlos.mendoza@grupomanz.com',
            'is_active': True
        },
        {
            'company_name': 'Towerbank International',
            'company_industry': 'financiero',
            'job_type': 'Vacante',
            'position_title': 'Especialista en Ciberseguridad',
            'work_modality': 'Remoto',
            'programming_languages': ['Python', 'C++'],
            'specialized_software': ['Wireshark', 'Metasploit'],
            'soft_skills': ['Pensamiento crítico', 'Trabajo bajo presión', 'Liderazgo'],
            'contact_name': 'Ana Rodriguez',
            'contact_email': 'ana.rodriguez@towerbank.com',
            'is_active': True
        }
    ]
    
    try:
        for data in sample_data:
            # Crear JobPost primero
            job_post = JobPost(
                post_url=f"https://instagram.com/sample/{data['company_name'].lower().replace(' ', '_')}",
                post_date=datetime.datetime.now(),
                is_job_offer=True,
                classification_score=95
            )
            db_session.add(job_post)
            db_session.flush()  # Para obtener el ID
            
            # Crear JobData con nuevos campos
            job_data = JobData(
                post_id=job_post.id,
                **data
            )
            db_session.add(job_data)
        
        db_session.commit()
        print(f"✅ {len(sample_data)} registros de muestra creados exitosamente")
        
    except Exception as e:
        print(f"❌ Error creando datos de muestra: {str(e)}")
        db_session.rollback()

if __name__ == "__main__":
    # Inicializar y migrar datos
    db_session = init_db()
    migrate_existing_data(db_session)
    
    # Crear datos de muestra si es necesario
    create_sample_enhanced_data(db_session)
    
    # Mostrar estadísticas
    stats = get_job_statistics(db_session)
    print("\n📊 ESTADÍSTICAS ACTUALIZADAS:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    db_session.close()