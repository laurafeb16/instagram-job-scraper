# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, JobPost, JobData, CarouselImage

app = Flask(__name__)

def get_db_session():
    engine = create_engine('sqlite:///data/database.db')
    Session = sessionmaker(bind=engine)
    return Session()

@app.route('/')
def index():
    session = get_db_session()
    
    # Filtros desde parámetros de URL
    job_type = request.args.get('type')
    company = request.args.get('company')
    is_active = request.args.get('active', 'true')
    
    # Consulta base - IMPORTANTE: Filtra ofertas reales
    query = session.query(JobPost, JobData).join(JobData)
    query = query.filter(JobData.job_type != 'N/A')  # Excluir no-ofertas
    
    # Aplicar filtros
    if job_type:
        query = query.filter(JobData.job_type == job_type)
    if company:
        query = query.filter(JobData.company_name.like(f"%{company}%"))
    if is_active == 'true':
        query = query.filter(JobData.is_active == True)
    elif is_active == 'false':
        query = query.filter(JobData.is_active == False)
    
    # Ordenar por fecha (más reciente primero)
    query = query.order_by(desc(JobPost.post_date))
    
    # Ejecutar la consulta
    job_posts = query.all()
    
    # Obtener valores únicos para filtros (solo de ofertas reales)
    companies = session.query(JobData.company_name).filter(JobData.job_type != 'N/A').distinct().all()
    job_types = session.query(JobData.job_type).filter(JobData.job_type != 'N/A').distinct().all()
    
    return render_template('index.html', 
                         job_posts=job_posts,
                         companies=[c[0] for c in companies if c[0] not in ('N/A', None)],
                         job_types=[t[0] for t in job_types if t[0] not in ('N/A', None)])

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    session = get_db_session()
    job_data = session.query(JobData).filter(JobData.id == job_id).first()
    
    if not job_data:
        return redirect(url_for('index'))
    
    job_post = session.query(JobPost).filter(JobPost.id == job_data.post_id).first()
    
    # Si es un carrusel, obtener todas las imágenes
    carousel_images = []
    if job_post.is_carousel:
        carousel_images = session.query(CarouselImage).filter(
            CarouselImage.post_id == job_post.id).order_by(CarouselImage.image_order).all()
    
    return render_template('job_detail.html', job_data=job_data, job_post=job_post, 
                          carousel_images=carousel_images)

if __name__ == '__main__':
    app.run(debug=True)
