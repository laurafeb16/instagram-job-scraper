# -*- coding: utf-8 -*-
"""
Tests para el extractor de ofertas laborales.
"""
import pytest
from typing import Tuple, Optional

from backend.job_extractor import JobExtractor

def test_is_job_post():
    """Prueba la deteccion de posts de ofertas laborales."""
    extractor = JobExtractor()
    
    # Texto simple sin caracteres especiales
    test_text = "Vacante ofrecida por Microsoft"
    
    is_job, company = extractor.is_job_post(test_text)
    
    assert is_job == True
    assert "Microsoft" in company

def test_extract_skills():
    """Prueba la extraccion de habilidades."""
    extractor = JobExtractor()
    
    test_text = "Requisitos: Python, JavaScript, React"
    
    skills = extractor.extract_skills(test_text)
    
    assert "Python" in skills
    assert "Javascript" in skills or "JavaScript" in skills
    assert "React" in skills

def test_extract_company():
    """Prueba la extraccion de empresa."""
    extractor = JobExtractor()
    
    test_text = "Empresa: Google\nOtros detalles..."
    
    company = extractor.extract_company(test_text)
    
    assert company == "Google"

def test_classify_area():
    """Prueba la clasificacion por area tecnologica."""
    extractor = JobExtractor()
    
    # Texto de data science
    ds_text = "experiencia en Python, pandas y machine learning"
    area1 = extractor.classify_area(ds_text)
    assert area1 == "data-science"
    
    # Texto de desarrollo web
    web_text = "conocimientos en JavaScript, React y Node.js"
    area2 = extractor.classify_area(web_text)
    assert area2 == "web-dev"

def test_extract_job_info_complete():
    """Prueba la extraccion completa de informacion de una oferta."""
    extractor = JobExtractor()
    
    test_text = """
    Empresa: Acme Corp
    Puesto: Desarrollador Full Stack
    Requisitos: JavaScript, React, Node.js, MongoDB
    Beneficios: Trabajo remoto, Seguro medico
    """
    
    job_info = extractor.extract_job_info(test_text)
    
    assert job_info["company"] == "Acme Corp"
    assert job_info["title"] == "Desarrollador Full Stack"
    assert "Javascript" in job_info["skills"] or "JavaScript" in job_info["skills"]
    assert "React" in job_info["skills"]
    assert "Trabajo Remoto" in job_info["benefits"] or "Trabajo remoto" in job_info["benefits"]
    assert job_info["is_open"] == True
