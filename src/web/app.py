# -*- coding: utf-8 -*-
import os
import sys
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
from sqlalchemy import desc, and_, or_
import json

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import init_db, JobPost, JobData, CarouselImage, AnalysisMetrics

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Inicializar base de datos
db_session = init_db()

@app.template_filter('tojsonfilter')
def tojsonfilter(obj):
    return json.dumps(obj)

@app.route('/')
def index():
    """Página principal con lista de ofertas y filtros mejorados"""
    
    # Obtener parámetros de filtro
    job_type = request.args.get('type', '')
    company = request.args.get('company', '')
    industry = request.args.get('industry', '')
    active_filter = request.args.get('active', 'true')
    work_modality = request.args.get('modality', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search_query = request.args.get('search', '')
    
    # Construir consulta base
    query = db_session.query(JobPost, JobData).join(JobData).filter(
        JobPost.is_job_offer == True
    )
    
    # Aplicar filtros
    if job_type:
        query = query.filter(JobData.job_type == job_type)
    
    if company and company != 'all':
        query = query.filter(JobData.company_name == company)
    
    if industry:
        query = query.filter(JobData.company_industry == industry)
    
    if active_filter == 'true':
        query = query.filter(JobData.is_active == True)
    elif active_filter == 'false':
        query = query.filter(JobData.is_active == False)
    
    if work_modality:
        query = query.filter(JobData.work_modality == work_modality)
    
    # Filtros de fecha
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(JobPost.post_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(JobPost.post_date <= date_to_obj)
        except ValueError:
            pass
    
    # Búsqueda por texto
    if search_query:
        search_filter = or_(
            JobData.company_name.contains(search_query),
            JobData.position_title.contains(search_query),
            JobData.job_type.contains(search_query)
        )
        query = query.filter(search_filter)
    
    # Ordenar por fecha descendente
    job_posts = query.order_by(desc(JobPost.post_date)).all()
    
    # Obtener datos para filtros
    job_types = db_session.query(JobData.job_type).filter(
        JobData.job_type.isnot(None),
        JobData.job_type != "No es oferta laboral"
    ).distinct().all()
    job_types = [jt[0] for jt in job_types if jt[0]]
    
    companies = db_session.query(JobData.company_name).filter(
        JobData.company_name.isnot(None),
        JobData.company_name.notin_(["N/A", "Por determinar"])
    ).distinct().all()
    companies = [c[0] for c in companies if c[0]]
    
    industries = db_session.query(JobData.company_industry).filter(
        JobData.company_industry.isnot(None)
    ).distinct().all()
    industries = [i[0] for i in industries if i[0]]
    
    work_modalities = db_session.query(JobData.work_modality).filter(
        JobData.work_modality.isnot(None)
    ).distinct().all()
    work_modalities = [w[0] for w in work_modalities if w[0]]
    
    # Estadísticas para el dashboard
    stats = get_dashboard_stats()
    
    return render_template('index.html', 
                         job_posts=job_posts,
                         job_types=job_types,
                         companies=companies,
                         industries=industries,
                         work_modalities=work_modalities,
                         stats=stats,
                         request=request)

@app.route('/job/<int:job_id>')
def job_detail(job_id):
    """Página de detalles de una oferta específica"""
    
    job_data = db_session.query(JobData).filter(JobData.id == job_id).first()
    if not job_data:
        return redirect(url_for('index'))
    
    job_post = job_data.post
    
    # Obtener imágenes del carrusel si existen
    carousel_images = []
    if job_post.is_carousel:
        carousel_images = db_session.query(CarouselImage).filter(
            CarouselImage.post_id == job_post.id
        ).order_by(CarouselImage.image_order).all()
    
    # Obtener métricas de análisis
    metrics = db_session.query(AnalysisMetrics).filter(
        AnalysisMetrics.post_id == job_post.id
    ).first()
    
    job_data = prepare_job_data_for_template(job_data)
    
    return render_template('job_detail.html',
                         job_data=job_data,
                         job_post=job_post,
                         carousel_images=carousel_images,
                         metrics=metrics)

@app.route('/api/stats')
def api_stats():
    """API endpoint para estadísticas en tiempo real"""
    stats = get_dashboard_stats()
    return jsonify(stats)

@app.route('/dashboard')
def dashboard():
    """Dashboard con gráficos y estadísticas avanzadas"""
    
    # Estadísticas generales
    stats = get_dashboard_stats()
    
    # Tendencias por fecha (últimos 30 días)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    trends_data = get_trends_data(thirty_days_ago)
    
    # Top empresas
    top_companies = get_top_companies(limit=10)
    
    # Distribución por industria
    industry_distribution = get_industry_distribution()
    
    return render_template('dashboard.html',
                         stats=stats,
                         trends_data=trends_data,
                         top_companies=top_companies,
                         industry_distribution=industry_distribution)

@app.route('/export/excel')
def export_excel():
    """Exportar datos filtrados a Excel"""
    from src.reports.reports_generator import JobAnalysisReporter
    
    reporter = JobAnalysisReporter()
    filename = reporter.export_to_excel()
    reporter.close()
    
    return jsonify({
        'success': True,
        'filename': filename,
        'message': f'Datos exportados exitosamente a {filename}'
    })

@app.route('/export/contacts')
def export_contacts():
    """Exportar contactos a CSV"""
    from src.reports.reports_generator import JobAnalysisReporter
    
    reporter = JobAnalysisReporter()
    filename = reporter.export_contacts_csv()
    reporter.close()
    
    return jsonify({
        'success': True,
        'filename': filename,
        'message': f'Contactos exportados exitosamente a {filename}'
    })

def prepare_job_data_for_template(job_data):
    """Prepara los datos para la plantilla de manera más robusta"""
    # Lista de campos que podrían ser listas serializadas
    list_fields = ['requirements', 'knowledge_required', 'functions', 'benefits']
    
    for field in list_fields:
        if hasattr(job_data, field):
            field_value = getattr(job_data, field)
            
            # Manejar valores nulos
            if field_value is None:
                setattr(job_data, field, [])
                continue
                
            # Si es string, convertirlo a lista
            if isinstance(field_value, str):
                try:
                    # Intentar como JSON primero
                    if field_value.startswith('[') and field_value.endswith(']'):
                        value = json.loads(field_value)
                    else:
                        # Dividir por líneas
                        value = [line.strip() for line in field_value.split('\n') if line.strip()]
                    
                    setattr(job_data, field, value)
                except Exception:
                    # En caso de error, usar método simple
                    lines = [line.strip() for line in field_value.split('\n') if line.strip()]
                    setattr(job_data, field, lines)
    
    return job_data

def get_dashboard_stats():
    """Obtiene estadísticas para el dashboard - CORREGIDO"""
    
    stats = {}
    
    # Estadísticas generales
    stats['total_posts'] = db_session.query(JobPost).count()
    stats['total_job_offers'] = db_session.query(JobPost).filter(JobPost.is_job_offer == True).count()
    
    # CORRECCIÓN: Solo contar ofertas laborales reales
    stats['active_offers'] = db_session.query(JobData).join(JobPost).filter(
        JobPost.is_job_offer == True,
        JobData.is_active == True
    ).count()
    
    # CORRECCIÓN: Solo contar ofertas laborales finalizadas, no posts que no son ofertas
    stats['expired_offers'] = db_session.query(JobData).join(JobPost).filter(
        JobPost.is_job_offer == True,
        JobData.is_active == False
    ).count()
    
    # Estadísticas de esta semana
    week_ago = datetime.now() - timedelta(days=7)
    stats['this_week'] = db_session.query(JobPost).filter(
        JobPost.post_date >= week_ago,
        JobPost.is_job_offer == True
    ).count()
    
    # Tasa de detección
    if stats['total_posts'] > 0:
        stats['detection_rate'] = round((stats['total_job_offers'] / stats['total_posts']) * 100, 1)
    else:
        stats['detection_rate'] = 0
    
    # Ofertas con información de contacto completa
    stats['with_contact'] = db_session.query(JobData).join(JobPost).filter(
        JobPost.is_job_offer == True,
        JobData.contact_email.isnot(None),
        JobData.is_active == True
    ).count()
    
    return stats

def get_trends_data(since_date):
    """Obtiene datos de tendencias por fecha"""
    
    trends = db_session.query(
        JobPost.post_date,
        JobData.job_type
    ).join(JobData).filter(
        JobPost.post_date >= since_date,
        JobPost.is_job_offer == True
    ).all()
    
    # Agrupar por fecha y tipo
    trends_dict = {}
    for post_date, job_type in trends:
        date_key = post_date.strftime('%Y-%m-%d')
        if date_key not in trends_dict:
            trends_dict[date_key] = {}
        
        job_type = job_type or "No especificado"
        trends_dict[date_key][job_type] = trends_dict[date_key].get(job_type, 0) + 1
    
    return trends_dict

def get_top_companies(limit=10):
    """Obtiene las empresas con más ofertas"""
    
    from sqlalchemy import func, Integer
    
    result = db_session.query(
        JobData.company_name,
        func.count(JobData.id).label('total_count'),
        func.sum(JobData.is_active.cast(Integer)).label('active_count')
    ).filter(
        JobData.company_name.isnot(None),
        JobData.company_name != "N/A",
        JobData.company_name != "Por determinar"
    ).group_by(
        JobData.company_name
    ).order_by(
        func.count(JobData.id).desc()
    ).limit(limit).all()
    
    # Convertir a lista de listas para hacerlo serializable a JSON
    serializable_result = [[item[0], item[1], item[2]] for item in result]
    
    return serializable_result

def get_industry_distribution():
    """Obtiene distribución por industria"""
    
    from sqlalchemy import func
    
    distribution = db_session.query(
        JobData.company_industry,
        func.count(JobData.company_industry).label('count')
    ).filter(
        JobData.company_industry.isnot(None)
    ).group_by(JobData.company_industry).all()
    
    # Convertir a lista de diccionarios para serialización JSON
    serializable_distribution = [{"industry": item[0], "count": item[1]} for item in distribution]
    
    return serializable_distribution

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)