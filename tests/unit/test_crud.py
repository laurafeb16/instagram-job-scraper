# -*- coding: utf-8 -*-
"""
Tests para operaciones CRUD.
"""
import pytest
from datetime import datetime

from backend import crud
from backend import models

def test_create_profile(db_session):
    """Prueba la creacion de un perfil."""
    username = "test_create_profile"
    
    # Crear perfil
    profile = crud.profile.create(db_session, obj_in={
        "username": username
    })
    
    # Verificar resultado
    assert profile.id is not None
    assert profile.username == username
    assert profile.created_at is not None
    
    # Verificar que se puede recuperar
    db_profile = crud.profile.get(db_session, profile.id)
    assert db_profile is not None
    assert db_profile.username == username

def test_get_or_create_profile(db_session):
    """Prueba obtener o crear un perfil."""
    username = "test_get_or_create"
    
    # Primera llamada debe crear un perfil
    profile1 = crud.profile.get_or_create(db_session, username)
    assert profile1.id is not None
    assert profile1.username == username
    
    # Segunda llamada debe obtener el mismo perfil
    profile2 = crud.profile.get_or_create(db_session, username)
    assert profile2.id == profile1.id
    assert profile2.username == username

def test_update_profile(db_session, sample_profile):
    """Prueba la actualizacion de un perfil."""
    # Actualizar perfil
    new_full_name = "Updated Name"
    updated_profile = crud.profile.update(
        db_session, 
        db_obj=sample_profile, 
        obj_in={"full_name": new_full_name}
    )
    
    # Verificar cambios
    assert updated_profile.full_name == new_full_name
    
    # Verificar que los cambios se guardaron en BD
    db_profile = crud.profile.get(db_session, sample_profile.id)
    assert db_profile.full_name == new_full_name

def test_create_post(db_session, sample_profile):
    """Prueba la creacion de un post."""
    shortcode = "DEF456"
    
    # Crear post
    post = crud.post.create(db_session, obj_in={
        "profile_id": sample_profile.id,
        "shortcode": shortcode,
        "caption": "Test caption",
        "timestamp": datetime.utcnow(),
        "is_job_post": False
    })
    
    # Verificar resultado
    assert post.id is not None
    assert post.shortcode == shortcode
    assert post.profile_id == sample_profile.id
    
    # Verificar que se puede recuperar
    db_post = crud.post.get(db_session, post.id)
    assert db_post is not None
    assert db_post.shortcode == shortcode

def test_get_posts_by_profile(db_session, sample_profile):
    """Prueba obtener posts de un perfil."""
    # Crear varios posts
    for i in range(3):
        crud.post.create(db_session, obj_in={
            "profile_id": sample_profile.id,
            "shortcode": f"TEST{i}",
            "caption": f"Test caption {i}",
            "timestamp": datetime.utcnow(),
            "is_job_post": False
        })
    
    # Obtener posts del perfil
    posts = crud.post.get_by_profile(db_session, sample_profile.id)
    
    # Verificar resultados
    assert len(posts) >= 3
    assert all(p.profile_id == sample_profile.id for p in posts)
