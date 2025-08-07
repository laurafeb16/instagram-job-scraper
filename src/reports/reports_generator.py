# -*- coding: utf-8 -*-
import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import func

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import init_db, JobPost, JobData, AnalysisMetrics

class JobAnalysisReporter:
    """Generador de reportes y análisis de ofertas laborales"""
    
    def __init__(self, db_path='sqlite:///data/database.db'):
        self.db_session = init_db(db_path)
    
    def generate_summary_report(self):
        """Genera un reporte resumen de todas las ofertas"""
        
        print("=" * 60)
        print("REPORTE RESUMEN DE OFERTAS LABORALES")
        print("=" * 60)
        
        # Estadísticas generales
        total_posts = self.db_session.query(JobPost).count()
        job_offers = self.db_session.query(JobPost).filter(JobPost.is_job_offer == True).count()
        active_offers = self.db_session.query(JobData).filter(JobData.is_active == True).count()
        
        print(f":bar_chart: ESTADÍSTICAS GENERALES")
        print(f"   Total de posts analizados: {total_posts}")
        print(f"   Ofertas laborales identificadas: {job_offers}")
        print(f"   Ofertas activas: {active_offers}")
        print(f"   Tasa de detección: {(job_offers/total_posts*100):.1f}%" if total_posts > 0 else "   Tasa de detección: 0%")
        print()
        
        # Por tipo de trabajo
        job_types = self.db_session.query(
            JobData.job_type, 
            func.count(JobData.job_type)
        ).filter(
            JobData.job_type.isnot(None),
            JobData.job_type != "No es oferta laboral"
        ).group_by(JobData.job_type).all()
        
        if job_types:
            print(":chart_with_upwards_trend: POR TIPO DE TRABAJO:")
            for job_type, count in job_types:
                print(f"   {job_type}: {count}")
            print()
        
        # Por industria
        industries = self.db_session.query(
            JobData.company_industry, 
            func.count(JobData.company_industry)
        ).filter(
            JobData.company_industry.isnot(None)
        ).group_by(JobData.company_industry).all()
        
        if industries:
            print(":office: POR INDUSTRIA:")
            for industry, count in industries:
                print(f"   {industry}: {count}")
            print()
        
        # Empresas más activas
        companies = self.db_session.query(
            JobData.company_name, 
            func.count(JobData.company_name)
        ).filter(
            JobData.company_name.isnot(None),
            JobData.company_name != "N/A",
            JobData.company_name != "Por determinar"
        ).group_by(JobData.company_name).order_by(
            func.count(JobData.company_name).desc()
        ).limit(5).all()
        
        if companies:
            print(":trophy: EMPRESAS MÁS ACTIVAS:")
            for company, count in companies:
                print(f"   {company}: {count} ofertas")
            print()
    
    def generate_active_offers_report(self):
        """Genera reporte de ofertas activas"""
        
        print("=" * 60)
        print("OFERTAS LABORALES ACTIVAS")
        print("=" * 60)
        
        active_offers = self.db_session.query(JobData).join(JobPost).filter(
            JobData.is_active == True,
            JobPost.is_job_offer == True
        ).order_by(JobPost.post_date.desc()).all()
        
        if not active_offers:
            print("No hay ofertas activas en la base de datos.")
            return
        
        for i, offer in enumerate(active_offers, 1):
            print(f"\n:clipboard: OFERTA #{i}")
            print(f"   Empresa: {offer.company_name or 'No especificada'}")
            print(f"   Tipo: {offer.job_type or 'No especificado'}")
            print(f"   Puesto: {offer.position_title or 'No especificado'}")
            print(f"   Industria: {offer.company_industry or 'No especificada'}")
            
            if offer.contact_email:
                print(f"   :e_mail: Email: {offer.contact_email}")
            if offer.contact_phone:
                print(f"   :telephone_receiver: Teléfono: {offer.contact_phone}")
            if offer.contact_name:
                print(f"   :bust_in_silhouette: Contacto: {offer.contact_name}")
                if offer.contact_position:
                    print(f"        Posición: {offer.contact_position}")
            
            if offer.work_modality:
                print(f"   :office: Modalidad: {offer.work_modality}")
            if offer.duration:
                print(f"   :stopwatch: Duración: {offer.duration}")
            
            if offer.requirements:
                print(f"   :pencil: Requisitos principales:")
                for req in offer.requirements[:3]:  # Mostrar solo los primeros 3
                    print(f"      • {req}")
            
            if offer.benefits:
                print(f"   :gift: Beneficios:")
                for benefit in offer.benefits[:3]:  # Mostrar solo los primeros 3
                    print(f"      • {benefit}")
            
            print(f"   :link: Post: {offer.post.post_url}")
            print(f"   :date: Publicado: {offer.post.post_date.strftime('%d/%m/%Y')}")
    
    def export_to_excel(self, filename=None):
        """Exporta los datos a un archivo Excel"""
        
        if filename is None:
            filename = f"ofertas_laborales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Consultar datos
        query = self.db_session.query(
            JobPost.post_url,
            JobPost.post_date,
            JobPost.is_job_offer,
            JobPost.classification_score,
            JobData.company_name,
            JobData.company_industry,
            JobData.job_type,
            JobData.position_title,
            JobData.work_modality,
            JobData.duration,
            JobData.contact_name,
            JobData.contact_position,
            JobData.contact_email,
            JobData.contact_phone,
            JobData.experience_required,
            JobData.education_required,
            JobData.is_active,
            JobData.extracted_at
        ).join(JobData).filter(JobPost.is_job_offer == True)
        
        # Convertir a DataFrame
        df = pd.DataFrame(query.all(), columns=[
            'URL_Post', 'Fecha_Post', 'Es_Oferta', 'Puntuacion_Clasificacion',
            'Empresa', 'Industria', 'Tipo_Trabajo', 'Titulo_Puesto',
            'Modalidad_Trabajo', 'Duracion', 'Nombre_Contacto', 'Posicion_Contacto',
            'Email_Contacto', 'Telefono_Contacto', 'Experiencia_Requerida',
            'Educacion_Requerida', 'Activa', 'Fecha_Extraccion'
        ])
        
        # Crear archivo Excel con múltiples hojas
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Hoja principal con todas las ofertas
            df.to_excel(writer, sheet_name='Todas_las_Ofertas', index=False)
            
            # Hoja solo con ofertas activas
            active_df = df[df['Activa'] == True]
            active_df.to_excel(writer, sheet_name='Ofertas_Activas', index=False)
            
            # Hoja de estadísticas por empresa
            company_stats = df.groupby('Empresa').agg({
                'URL_Post': 'count',
                'Activa': 'sum',
                'Fecha_Post': 'max'
            }).rename(columns={
                'URL_Post': 'Total_Ofertas',
                'Activa': 'Ofertas_Activas',
                'Fecha_Post': 'Ultima_Oferta'
            }).reset_index()
            company_stats.to_excel(writer, sheet_name='Estadisticas_Empresas', index=False)
            
            # Hoja de estadísticas por tipo de trabajo
            job_type_stats = df.groupby('Tipo_Trabajo').agg({
                'URL_Post': 'count',
                'Activa': 'sum'
            }).rename(columns={
                'URL_Post': 'Total_Ofertas',
                'Activa': 'Ofertas_Activas'
            }).reset_index()
            job_type_stats.to_excel(writer, sheet_name='Estadisticas_Tipo_Trabajo', index=False)
        
        print(f":white_check_mark: Datos exportados exitosamente a: {filename}")
        return filename
    
    def export_contacts_csv(self, filename=None):
        """Exporta solo la información de contactos a CSV"""
        
        if filename is None:
            filename = f"contactos_ofertas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        query = self.db_session.query(
            JobData.company_name,
            JobData.contact_name,
            JobData.contact_position,
            JobData.contact_email,
            JobData.contact_phone,
            JobData.job_type,
            JobData.position_title,
            JobPost.post_url
        ).join(JobPost).filter(
            JobPost.is_job_offer == True,
            JobData.is_active == True,
            JobData.contact_email.isnot(None)
        )
        
        df = pd.DataFrame(query.all(), columns=[
            'Empresa', 'Nombre_Contacto', 'Posicion_Contacto', 'Email',
            'Telefono', 'Tipo_Trabajo', 'Titulo_Puesto', 'URL_Post'
        ])
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f":white_check_mark: Contactos exportados exitosamente a: {filename}")
        return filename
    
    def generate_trends_analysis(self, days=30):
        """Analiza tendencias de ofertas en los últimos días"""
        
        print("=" * 60)
        print(f"ANÁLISIS DE TENDENCIAS - ÚLTIMOS {days} DÍAS")
        print("=" * 60)
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_offers = self.db_session.query(JobData).join(JobPost).filter(
            JobPost.post_date >= cutoff_date,
            JobPost.is_job_offer == True
        ).all()
        
        if not recent_offers:
            print(f"No hay ofertas en los últimos {days} días.")
            return
        
        print(f":chart_with_upwards_trend: RESUMEN DE TENDENCIAS:")
        print(f"   Ofertas publicadas: {len(recent_offers)}")
        print(f"   Promedio por día: {len(recent_offers)/days:.1f}")
        
        # Tendencias por tipo
        type_trends = {}
        for offer in recent_offers:
            job_type = offer.job_type or "No especificado"
            type_trends[job_type] = type_trends.get(job_type, 0) + 1
        
        print(f"\n:bar_chart: POR TIPO DE TRABAJO:")
        for job_type, count in sorted(type_trends.items(), key=lambda x: x[1], reverse=True):
            print(f"   {job_type}: {count}")
        
        # Empresas más activas recientemente
        company_trends = {}
        for offer in recent_offers:
            company = offer.company_name or "No especificada"
            if company not in ["N/A", "Por determinar"]:
                company_trends[company] = company_trends.get(company, 0) + 1
        
        if company_trends:
            print(f"\n:office: EMPRESAS MÁS ACTIVAS:")
            for company, count in sorted(company_trends.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   {company}: {count} ofertas")
    
    def close(self):
        """Cierra la sesión de base de datos"""
        self.db_session.close()

def main():
    """Función principal para generar reportes"""
    
    print(":mag: GENERADOR DE REPORTES DE OFERTAS LABORALES")
    print("=" * 60)
    
    reporter = JobAnalysisReporter()
    
    try:
        # Generar reportes
        reporter.generate_summary_report()
        print("\n")
        reporter.generate_active_offers_report()
        print("\n")
        reporter.generate_trends_analysis(30)
        
        # Exportar datos
        print("\n" + "=" * 60)
        print("EXPORTANDO DATOS...")
        print("=" * 60)
        
        excel_file = reporter.export_to_excel()
        csv_file = reporter.export_contacts_csv()
        
        print(f"\n:white_check_mark: Reportes generados exitosamente:")
        print(f"   :bar_chart: Excel completo: {excel_file}")
        print(f"   :clipboard: Contactos CSV: {csv_file}")
        
    except Exception as e:
        print(f":x: Error generando reportes: {str(e)}")
    finally:
        reporter.close()

if __name__ == "__main__":
    main()
