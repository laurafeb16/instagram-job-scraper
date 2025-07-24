# -*- coding: utf-8 -*-
import pytest
from backend.job_extractor import JobExtractor

def test_is_job_post():
    extractor = JobExtractor()
    
    # Texto simple sin caracteres especiales
    test_text = "Vacante ofrecida por Microsoft"
    
    is_job, company = extractor.is_job_post(test_text)
    
    assert is_job == True
    assert company == "Microsoft"

def test_extract_skills():
    extractor = JobExtractor()
    
    test_text = "Requisitos: Python, JavaScript, React"
    
    skills = extractor.extract_skills(test_text)
    
    assert "Python" in skills
def test_extract_company():
    extractor = JobExtractor()
    
    test_text = "Empresa: Google\nOtros detalles..."
    
    company = extractor.extract_company(test_text)
    
    assert company == "Google"

def test_classify_area():
    extractor = JobExtractor()
    
    # Texto de data science
    ds_text = "experiencia en Python, pandas y machine learning"
    area1 = extractor.classify_area(ds_text)
    assert area1 == "data-science"
    
    # Texto de desarrollo web
    web_text = "conocimientos en JavaScript, React y Node.js"
    area2 = extractor.classify_area(web_text)
    assert area2 == "web-dev"
