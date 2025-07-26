# -*- coding: utf-8 -*-
"""
Script para generar informes automáticos de ofertas laborales.
"""
import os
import sys
import argparse
import json
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Any, Optional

# Añadir directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.topic_modeling import TopicModeler, SkillExtractor
from backend.database import get_db
from backend import crud, models
from backend.logging_config import setup_logging, get_logger

# Configurar logging
setup_logging()
logger = get_logger(__name__)

def generate_job_report(days: int = 7, output_dir: str = "reports") -> str:
    """Genera un informe de ofertas laborales de los últimos días.
    
    Args:
        days: Número de días hacia atrás para incluir en el informe
        output_dir: Directorio donde guardar el informe
        
    Returns:
        Ruta al archivo de informe generado
    """
    # Asegurar que el directorio existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Calcular fecha límite
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Obtener sesión de DB
    db = next(get_db())
    
    # Obtener ofertas recientes
    recent_posts = db.query(models.Post).filter(
        models.Post.timestamp >= cutoff_date,
        models.Post.is_job_post == True
    ).all()
    
    logger.info(f"Generando informe con {len(recent_posts)} ofertas de los últimos {days} días")
    
    # Si no hay ofertas, crear informe vacío
    if not recent_posts:
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "period_days": days,
            "total_jobs": 0,
            "jobs": [],
            "summary": {
                "companies": [],
                "skills": [],
                "areas": []
            }
        }
    else:
        # Extraer datos de ofertas
        jobs_data = []
        all_skills = []
        companies = {}
        areas = {}
        
        for post in recent_posts:
            # Obtener datos de la oferta
            job = post.job
            if not job:
                continue
                
            # Contar empresa
            company = job.company or "Desconocida"
            companies[company] = companies.get(company, 0) + 1
            
            # Contar área
            area = job.area or "general"
            areas[area] = areas.get(area, 0) + 1
            
            # Acumular skills
            all_skills.extend(job.skills or [])
            
            # Datos básicos de la oferta
            job_data = {
                "id": job.id,
                "company": company,
                "title": job.title,
                "area": area,
                "skills": job.skills,
                "post_date": post.timestamp.isoformat(),
                "is_open": job.is_open,
                "instagram_shortcode": post.shortcode
            }
            
            jobs_data.append(job_data)
        
        # Contar skills
        skill_counter = {}
        for skill in all_skills:
            skill_counter[skill] = skill_counter.get(skill, 0) + 1
        
        # Ordenar por frecuencia
        top_skills = sorted(skill_counter.items(), key=lambda x: x[1], reverse=True)[:10]
        top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5]
        area_distribution = sorted(areas.items(), key=lambda x: x[1], reverse=True)
        
        # Crear informe
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "period_days": days,
            "total_jobs": len(jobs_data),
            "jobs": jobs_data,
            "summary": {
                "companies": [{"name": c, "count": n} for c, n in top_companies],
                "skills": [{"name": s, "count": n} for s, n in top_skills],
                "areas": [{"name": a, "count": n} for a, n in area_distribution]
            }
        }
    
    # Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"job_report_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Guardar informe
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Informe guardado en {filepath}")
    
    # También generar versión Excel para usuarios no técnicos
    if report["total_jobs"] > 0:
        excel_path = os.path.join(output_dir, f"job_report_{timestamp}.xlsx")
        
        # Crear DataFrame para la tabla principal
        df_jobs = pd.DataFrame(report["jobs"])
        
        # Crear DataFrames para las tablas de resumen
        df_companies = pd.DataFrame(report["summary"]["companies"])
        df_skills = pd.DataFrame(report["summary"]["skills"])
        df_areas = pd.DataFrame(report["summary"]["areas"])
        
        # Guardar en Excel con múltiples hojas
        with pd.ExcelWriter(excel_path) as writer:
            df_jobs.to_excel(writer, sheet_name="Ofertas", index=False)
            df_companies.to_excel(writer, sheet_name="Empresas", index=False)
            df_skills.to_excel(writer, sheet_name="Habilidades", index=False)
            df_areas.to_excel(writer, sheet_name="Áreas", index=False)
        
        logger.info(f"Informe Excel guardado en {excel_path}")
    
    return filepath

def main() -> None:
    """Función principal."""
    parser = argparse.ArgumentParser(description="Generar informes de ofertas laborales")
    parser.add_argument("--days", "-d", type=int, default=7,
                        help="Número de días hacia atrás (default: 7)")
    parser.add_argument("--output", "-o", default="reports",
                        help="Directorio de salida (default: reports)")
    
    args = parser.parse_args()
    
    try:
        report_path = generate_job_report(args.days, args.output)
        print(f"Informe generado exitosamente: {report_path}")
    except Exception as e:
        logger.error(f"Error al generar informe: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
