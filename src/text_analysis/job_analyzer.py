# -*- coding: utf-8 -*-
import re
import unicodedata

def normalize_text(text):
    """Normaliza el texto para manejar errores de OCR y caracteres especiales"""
    if not text:
        return ""
    # Normalizar a forma NFKD y luego reemplazar caracteres no ASCII
    normalized = unicodedata.normalize('NFKD', text)
    # Corregir errores comunes de OCR
    corrections = {
        'cl': 'd', 'rn': 'm', 'li': 'h', 'ii': 'n',
        'pracbca': 'práctica', 'requhitos': 'requisitos',
        'conodmientos': 'conocimientos', 'expenenda': 'experiencia'
    }
    for error, fix in corrections.items():
        normalized = normalized.replace(error, fix)
    return normalized

def is_job_post(text, description):
    """Determina si un post es una oferta laboral"""
    
    # Normalizar textos
    text = normalize_text(text)
    description = normalize_text(description)
    
    # Palabras clave positivas con ponderación
    job_indicators = {
        "práctica profesional": 10,
        "práctica laboral": 10,
        "vacante": 10,
        "oferta laboral": 10,
        "empresa": 5,
        "entidad": 5,
        "requisitos": 5,
        "conocimientos": 5,
        "funciones": 5,
        "ofrecen": 5,
        "contacto": 3,
        "interesados": 3,
        "hoja de vida": 3,
        "cv": 3,
        "reclutamiento": 2  # Añadido
    }
    
    # Palabras clave negativas
    non_job_indicators = {
        "matrícula": -10,
        "calendario académico": -10,
        "horario de clases": -10,
        "seminario": -5,
        "conferencia": -5,
        "vicerrectoría": -5,
        "ha finalizado": -8,  # Añadido
        "finalizado el período": -8  # Añadido
    }
    
    combined_text = (text + " " + description).lower()
    
    # Calcular puntuación
    score = 0
    for term, weight in job_indicators.items():
        if term in combined_text:
            score += weight
    
    for term, weight in non_job_indicators.items():
        if term in combined_text:
            score += weight
    
    # Verificar estado de la oferta (activa/finalizada)
    is_expired = False
    if "finalizado" in description.lower() or "cerrado" in description.lower():
        is_expired = True
        score -= 5  # Penalizar ofertas finalizadas
    
    # Añadir más patrones para detectar ofertas finalizadas
    expired_patterns = [
        r"(?:ha|período)\s+finalizado",
        r"convocatoria\s+cerrada",
        r"ya\s+no\s+(?:está|se encuentra)\s+disponible",
        r"se\s+han\s+cubierto\s+(?:todas)?\s+las\s+plazas",
    ]

    # Buscar estos patrones en la descripción del post
    for pattern in expired_patterns:
        if re.search(pattern, description.lower()):
            is_expired = True
            score -= 5
            break
    
    # Primero determinar si es una oferta laboral
    is_job = score >= 15  # Umbral ajustable
    
    # Definir patrones para tipos de oferta
    job_type_patterns = {
        "Práctica Profesional": [r"[Pp]r[aá]ctica\s+[Pp]rofesional", r"[Pp]r[aá]ctica\s+[Pp]rof\."],
        "Práctica Laboral": [r"[Pp]r[aá]ctica\s+[Ll]aboral"],
        "Vacante": [r"[Vv]acante", r"[Pp]uesto\s+[Vv]acante"]
    }
    
    # Identificar tipo de oferta con búsqueda más robusta
    job_type = None
    if is_job:  # Solo asignar tipo si es una oferta
        for jt, patterns in job_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined_text):
                    job_type = jt
                    break
            if job_type:
                break
    
    # Añadir detección de patrones específicos para mejorar precisión
    job_specific_patterns = [
        r"(?:enviar|envía|remitir)(?:\s+(?:tu|su|el))?(?:\s+(?:cv|curriculum|hoja de vida))",
        r"interesados(?:\s+(?:enviar|contactar|escribir))",
        r"estamos\s+(?:buscando|contratando|seleccionando)",
        r"(?:se\s+)?requiere\s+personal",
        r"se\s+solicita",
        r"(?:enviar|mandar)\s+(?:postulación|aplicación)"
    ]
    
    for pattern in job_specific_patterns:
        if re.search(pattern, combined_text):
            score += 5  # Incrementar puntuación si hay patrones específicos
    
    # Devolver también si está activa o finalizada
    return is_job, job_type, score, is_expired

def extract_job_data(image_text, post_description):
    """Extrae información estructurada de la oferta laboral"""
    
    # Normalizar textos
    image_text = normalize_text(image_text)
    post_description = normalize_text(post_description)
    
    combined_text = image_text + "\n\n" + post_description
    
    # Inicializar diccionario con más campos
    job_data = {
        "company_name": None,
        "contact_name": None,
        "contact_position": None,
        "contact_email": None,
        "contact_phone": None,
        "position_title": None,  # Añadido
        "requirements": [],
        "knowledge": [],
        "functions": [],
        "benefits": [],
        "is_active": True,  # Añadido
        "experience_required": None,
        "education_required": None
    }
    
    # Verificar si la oferta está activa o finalizada
    if "finalizado" in post_description.lower() or "cerrado" in post_description.lower():
        job_data["is_active"] = False
    
    # Patrones mejorados
    company_patterns = [
        r"Empresa:\s*([^\n]+)",
        r"Entidad:\s*([^\n]+)",
        r"(?:Empresa|Entidad):\s*([A-Za-z0-9\s\.,]+)(?:\n|$)"
    ]
    
    # Buscar título del puesto (nuevo)
    position_patterns = [
        r"(?:para|como)\s+([A-Za-z\s]+de\s+[A-Za-z\s]+)",
        r"(?:busca|solicita)\s+([A-Za-z\s]+)"
    ]
    
    # Patrones más específicos para títulos de puestos
    new_position_patterns = [
        r"(?:como|puesto de|cargo de)\s+([A-Za-z\s]+(?:de|en)\s+[A-Za-z\s]+)",
        r"(?:analista|ingeniero|desarrollador|programador)\s+(?:de|en)\s+([A-Za-z\s]+)",
        r"(?:ofrecen|buscan|solicitan)\s+(?:un|una)\s+([A-Za-z\s]+)"
    ]
    
    for pattern in position_patterns + new_position_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            job_data["position_title"] = match.group(1).strip()
            break
    
    # Extraer empresa
    for pattern in company_patterns:
        match = re.search(pattern, combined_text)
        if match:
            job_data["company_name"] = match.group(1).strip()
            break
    
    # Extraer contacto (nombre y posición)
    contact_pattern = r"Contacto:\s*([^|]+)\|\s*([^\n]+)"
    contact_match = re.search(contact_pattern, combined_text)
    if contact_match:
        job_data["contact_name"] = contact_match.group(1).strip()
        job_data["contact_position"] = contact_match.group(2).strip()
    
    # Extraer email
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    email_match = re.search(email_pattern, combined_text)
    if email_match:
        job_data["contact_email"] = email_match.group(0)
    
    # Extraer teléfono
    phone_pattern = r"(?:\+\d{1,3})?[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}"
    phone_match = re.search(phone_pattern, combined_text)
    if phone_match:
        job_data["contact_phone"] = phone_match.group(0)
    
    # Extraer secciones con listas
    section_patterns = {
        "requirements": r"Requisitos:\s*\n(.*?)(?:\n\n|\n[A-Z])",
        "knowledge": r"Conocimientos[^:]*:\s*\n(.*?)(?:\n\n|\n[A-Z])",
        "functions": r"(?:Funciones|Algunas de las funciones)[^:]*:\s*\n(.*?)(?:\n\n|\n[A-Z])",
        "benefits": r"Ofrecen:\s*\n(.*?)(?:\n\n|\n[A-Z])"
    }
    
    for section, pattern in section_patterns.items():
        match = re.search(pattern, combined_text, re.DOTALL)
        if match:
            section_text = match.group(1)
            # Extraer elementos de lista (con viñetas o números)
            items = re.findall(r'[•⚫⦁⭐✓✔·][^\n•⚫⦁⭐✓✔·]*|(?:\d+\.\s*)[^\n]*', section_text)
            if items:
                job_data[section] = [item.strip().lstrip('•⚫⦁⭐✓✔·').strip() for item in items if item.strip()]
            else:
                # Si no hay viñetas, dividir por saltos de línea
                job_data[section] = [line.strip() for line in section_text.split('\n') if line.strip()]
    
    # Extraer nivel de experiencia y formación requerida
    experience_patterns = [
        r"(?:experiencia|exp\.)\s+(?:de|mínima|requerida)?\s+(\d+[- ]+\d+|\d+)\s+(?:años|meses)",
        r"(\d+[- ]+\d+|\d+)\s+(?:años|meses)\s+de\s+experiencia"
    ]
    
    education_patterns = [
        r"(?:título|formación|estudios)\s+(?:en|de)\s+([A-Za-z\s]+)",
        r"(?:ingenier[oa]|licenciad[oa]|técnic[oa])\s+(?:en|de)\s+([A-Za-z\s]+)",
        r"(?:estudiante|egresado)\s+de\s+([A-Za-z\s]+)"
    ]
    
    # Buscar experiencia requerida
    for pattern in experience_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            job_data["experience_required"] = match.group(1)
            break
    
    # Buscar formación requerida
    for pattern in education_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            job_data["education_required"] = match.group(1).strip()
            break
    
    return job_data
