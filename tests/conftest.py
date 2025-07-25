# -*- coding: utf-8 -*-
"""
Configuración y fixtures para tests.
"""
import os
import pytest
from typing import Generator, List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.database import Base
from backend import models
from backend.logging_config import setup_logging

# Configuración de entorno de pruebas
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
setup_logging()

# Base de datos en memoria para tests
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def db_engine():
    """Crea un motor de base de datos para las pruebas."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Crea una sesión de base de datos para las pruebas."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def sample_profile(db_session):
    """Crea un perfil de prueba."""
    profile = models.InstagramProfile(
        username="test_profile"
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile

@pytest.fixture
def sample_post(db_session, sample_profile):
    """Crea un post de prueba."""
    post = models.Post(
        profile_id=sample_profile.id,
        shortcode="ABC123",
        caption="Test post",
        timestamp="2023-01-01T12:00:00",
        is_job_post=False
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post

@pytest.fixture
def sample_job_post(db_session, sample_post):
    """Crea una oferta laboral de prueba."""
    job_post = models.JobPost(
        post_id=sample_post.id,
        company="Test Company",
        title="Test Position",
        area="web-dev",
        skills=["Python", "Django"],
        benefits=["Remote"],
        is_open=True
    )
    db_session.add(job_post)
    db_session.commit()
    db_session.refresh(job_post)
    
    # Actualizar el post relacionado
    sample_post.is_job_post = True
    db_session.add(sample_post)
    db_session.commit()
    
    return job_post