# -*- coding: utf-8 -*-
"""
Script para extraer habilidades de ofertas laborales.
"""
import argparse
import json
import os
import pandas as pd
from typing import List, Dict, Any, Optional
import sys
from sqlalchemy.orm import Session

# Añadir directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.topic_modeling import SkillExtractor, TopicModeler, analyze_job_text
from backend.database import get_db
from backend import models, crud

def extract_skills_from_db(limit: int = 100) -> None:
    """Extrae habilidades de las ofertas almacenadas en la base de datos.
    
    Args:
        limit: Número máximo de ofertas a procesar
    """
    # Obtener sesión de DB
    db = next(get_db())
    
    # Obtener ofertas laborales
    job_posts = crud.job_post.get_multi(db, limit=limit)
    
    print(f"Procesando {len(job_posts)} ofertas laborales...")
    
    # Inicializar extractor y análisis
    skill_extractor = SkillExtractor()
    
    results = []
    for job in job_posts:
        post = job.post
        
        # Combinar caption y OCR
        text = f"{post.caption or ''}\n{post.ocr_text or ''}"
        
        # Extraer habilidades
        skills = skill_extractor.get_top_skills(text)
        
        # Actualizar en la base de datos si es necesario
        if not job.skills or set(skills) != set(job.skills):
            crud.job_post.update(db, db_obj=job, obj_in={"skills": skills})
        
        # Añadir a resultados
        results.append({
            "id": job.id,
            "company": job.company,
            "title": job.title,
            "skills": skills
        })
    
    # Guardar resultados en CSV
    df = pd.DataFrame(results)
    df.to_csv("data/skills_analysis.csv", index=False)
    
    print(f"Análisis completado y guardado en data/skills_analysis.csv")
    print(f"Se han actualizado las habilidades en la base de datos")

def analyze_topics_from_db(n_topics: int = 5) -> None:
    """Analiza temas en las ofertas almacenadas en la base de datos.
    
    Args:
        n_topics: Número de temas a identificar
    """
    # Obtener sesión de DB
    db = next(get_db())
    
    # Obtener ofertas laborales
    job_posts = crud.job_post.get_multi(db)
    
    print(f"Analizando temas en {len(job_posts)} ofertas laborales...")
    
    # Obtener textos
    texts = []
    for job in job_posts:
        post = job.post
        text = f"{post.caption or ''}\n{post.ocr_text or ''}"
        texts.append(text)
    
    # Inicializar y entrenar modelo de temas
    topic_modeler = TopicModeler(n_topics=n_topics)
    try:
        topic_modeler.fit(texts)
        
        # Obtener temas
        topics = topic_modeler.get_topics()
        
        # Guardar resultados
        output_file = "data/topic_analysis.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(topics, f, indent=2, ensure_ascii=False)
            
        print(f"Análisis de temas completado y guardado en {output_file}")
    except ValueError as e:
        print(f"Error al analizar temas: {e}")

def main() -> None:
    """Función principal."""
    parser = argparse.ArgumentParser(description="Extraer habilidades y analizar temas de ofertas laborales")
    parser.add_argument("--skills", action="store_true", help="Extraer habilidades")
    parser.add_argument("--topics", action="store_true", help="Analizar temas")
    parser.add_argument("--limit", type=int, default=100, help="Límite de ofertas a procesar")
    parser.add_argument("--n-topics", type=int, default=5, help="Número de temas a identificar")
    
    args = parser.parse_args()
    
    if args.skills:
        extract_skills_from_db(limit=args.limit)
    
    if args.topics:
        analyze_topics_from_db(n_topics=args.n_topics)
    
    if not args.skills and not args.topics:
        parser.print_help()

if __name__ == "__main__":
    main()
