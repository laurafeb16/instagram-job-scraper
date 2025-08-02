# -*- coding: utf-8 -*-
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
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
    
    # Relaciones
    extracted_data = relationship("JobData", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<JobPost(id={self.id}, post_date={self.post_date})>"

class JobData(Base):
    __tablename__ = 'job_data'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('job_posts.id'))
    company_name = Column(String(255), nullable=True)
    job_type = Column(String(50), nullable=True)  # vacante, práctica laboral, práctica profesional
    contact_info = Column(Text, nullable=True)
    position_title = Column(String(255), nullable=True)
    requirements = Column(Text, nullable=True)
    benefits = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    extracted_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relación
    post = relationship("JobPost", back_populates="extracted_data")
    
    def __repr__(self):
        return f"<JobData(id={self.id}, company={self.company_name}, job_type={self.job_type})>"

def init_db(db_path='sqlite:///data/database.db'):
    """Inicializa la base de datos y crea las tablas si no existen"""
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()