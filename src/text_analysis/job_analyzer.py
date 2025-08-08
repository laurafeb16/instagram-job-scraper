# -*- coding: utf-8 -*-
import re
import unicodedata
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """
    Sistema de normalización escalable para errores de OCR comunes.
    Aplica correcciones generales que funcionan para cualquier texto.
    """
    if not text:
        return ""
        
    # Normalizar caracteres Unicode
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    
    # === CORRECCIONES GENERALES DE OCR ===
    
    # 1. Patrón "IA" mal interpretado (muy común en OCR)
    normalized = re.sub(r'\bIA\b', 'ia', normalized)
    normalized = re.sub(r'IA([a-z])', r'ia\1', normalized)
    normalized = re.sub(r'([A-Z])IA([a-z])', r'\1ia\2', normalized)
    
    # 2. Correcciones de acentos perdidos (patrones comunes)
    accent_patterns = {
        r'\bultimo\b': 'último',
        r'\bultima\b': 'última',  
        r'\bpractica\b': 'práctica',
        r'\bPractica\b': 'Práctica',
        r'\bacademico\b': 'académico',
        r'\bacademica\b': 'académica',
        r'\btecnico\b': 'técnico',
        r'\btecnica\b': 'técnica',
        r'\bbasico\b': 'básico',
        r'\bbasica\b': 'básica',
        r'\bLogica\b': 'Lógica',
        r'\blogica\b': 'lógica',
        r'\bmatematicas\b': 'matemáticas',
        r'\bMatematicas\b': 'Matemáticas',
        r'\bExperiencIA\b': 'Experiencia',
        r'\bIngenierIA\b': 'Ingeniería',
    }
    
    for pattern, replacement in accent_patterns.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    
    # 3. Errores de consonantes comunes (OCR confunde estas letras)
    consonant_patterns = {
        r'\b([A-Za-z]*?)rn([A-Za-z]*?)\b': r'\1m\2',  # 'rn' → 'm'
        r'\b([A-Za-z]*?)cl([A-Za-z]*?)\b': r'\1d\2',   # 'cl' → 'd' 
        r'\b([A-Za-z]*?)li([A-Za-z]*?)\b': r'\1h\2',   # 'li' → 'h'
        r'\bii\b': 'n',  # 'ii' → 'n'
    }
    
    for pattern, replacement in consonant_patterns.items():
        matches = re.finditer(pattern, normalized)
        for match in matches:
            original_word = match.group(0)
            corrected = re.sub(pattern, replacement, original_word)
            if len(corrected) >= 3:
                normalized = normalized.replace(original_word, corrected)
    
    # 4. Correcciones de sufijos comunes
    suffix_patterns = {
        r'([a-zA-Z]+?)cion\b': r'\1ción',
        r'([a-zA-Z]+?)sion\b': r'\1sión',
    }
    
    for pattern, replacement in suffix_patterns.items():
        normalized = re.sub(pattern, replacement, normalized)
    
    # 5. Correcciones de palabras técnicas comunes
    tech_patterns = {
        r'\bs3L\b': 'SQL',
        r'\bMys3L\b': 'MySQL',
        r'\bPostgres3L\b': 'PostgreSQL',
        r'\bJavascript\b': 'JavaScript',
        r'\bpythOn\b': 'Python',
    }
    
    for pattern, replacement in tech_patterns.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    
    # 6. Limpiar espacios múltiples y caracteres extraños
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r'[^\w\s\.,;:()\-+@áéíóúñü]', ' ', normalized)
    normalized = normalized.strip()
    
    return normalized

def clean_contact_name(name: str) -> str:
    """Limpia nombres de contacto con correcciones generales de OCR"""
    if not name:
        return name
    
    # Correcciones generales de nombres (no específicas)
    general_corrections = {
        # Títulos mal interpretados
        r'\bLcda\b': 'Lcda.',
        r'\bDra\b': 'Dra.',
        r'\bIng\b': 'Ing.',
        r'\bLic\b': 'Lic.',
        # Palabras comunes mal interpretadas
        r'\bJr\b': 'Jr.',
        r'\bSr\b': 'Sr.',
        r'\bde\s+la\b': 'de la',
        r'\bde\s+los\b': 'de los',
    }
    
    cleaned = name
    for pattern, replacement in general_corrections.items():
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    
    return re.sub(r'\s+', ' ', cleaned).strip()

def separate_name_and_position(full_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Separa nombre y cargo usando patrones generales escalables"""
    if not full_text:
        return None, None
    
    # Patrones generales para separar nombre y cargo
    separation_patterns = [
        # Patrón con separador explícito: "Nombre | Cargo"
        r'^([A-Za-z\.]+(?:\s+[A-Za-z\.]+){1,4})\s*[\|\-]\s*(.+)$',
        
        # Patrón con títulos profesionales: "Título Nombre | Cargo"
        r'^((?:Lcda?\.|Lic\.|Dr[a]?\.|Ing\.|Prof\.|Sr\.|Sra\.)\s+[A-Za-z]+(?:\s+[A-Za-z]+){1,3})\s*[\|\-]?\s*(.*)$',
        
        # Patrón con cargos conocidos: "Nombre Cargo_Conocido"
        r'^([A-Za-z\.]+(?:\s+[A-Za-z\.]+){1,3})\s+((?:Analista|Gerente|Director|Coordinador|Oficial|Especialista|Manager|Ejecutivo|Supervisor|Asistente|Jefe).*?)$',
        
        # Patrón con departamentos: "Nombre Departamento"
        r'^([A-Za-z\.]+(?:\s+[A-Za-z\.]+){1,3})\s+((?:Recursos\s+Humanos|Talent|Development|Human\s+Resources|IT|Systems|Marketing|Ventas|Finanzas).*?)$',
    ]
    
    for pattern in separation_patterns:
        match = re.search(pattern, full_text.strip(), re.IGNORECASE)
        if match:
            name = clean_contact_name(match.group(1).strip())
            position = match.group(2).strip() if len(match.groups()) >= 2 else None
            
            # Validar que el nombre sea válido
            if (len(name.split()) >= 2 and 
                len(name) >= 5 and 
                re.match(r'^[A-Za-z\.\s]+$', name)):
                return name, position
    
    # Si no se puede separar, extraer solo el nombre (primeras palabras)
    words = full_text.split()
    if len(words) >= 2:
        # Buscar punto de separación natural
        for i in range(2, min(5, len(words) + 1)):
            potential_name = ' '.join(words[:i])
            if re.match(r'^[A-Za-z\.\s]+$', potential_name):
                remaining = ' '.join(words[i:]) if i < len(words) else None
                return clean_contact_name(potential_name), remaining
    
    return clean_contact_name(full_text), None

def extract_contact_info(text: str) -> Dict[str, Optional[str]]:
    """Extrae información de contacto con patrones GENERALES y ESCALABLES"""
    
    contact_info = {
        "name": None,
        "position": None,
        "email": None,
        "phone": None,
        "mobile": None
    }
    
    normalized_text = normalize_text(text)
    
    # === PATRONES GENERALES PARA CONTACTO ===
    contact_patterns = [
        # Patrón universal: "Contacto:" seguido de cualquier cosa
        r"Contacto:\s*([^\n\r]{5,100}?)(?=\s*(?:Móvil|Teléfono|Email|\+\d|Correo|$|\n|\.\.\.|\|))",
        
        # Patrón de respaldo: capturar hasta pipe o salto
        r"Contacto:\s*([^|\n]{8,60})",
        
        # Patrón simple: solo después de dos puntos
        r"Contacto:\s*([A-Za-z][A-Za-z\s\.]{8,50})",
        
        # Patrón para responsables: "Responsable:" seguido de texto
        r"Responsable:\s*([^\n\r]{5,120}?)(?=\s*(?:Móvil|Teléfono|Email|\+\d|Correo|$|\n))",
        
        # Patrón para coordinadores: "Coordinador[a]:" seguido de texto  
        r"Coordinadora?:\s*([^\n\r]{5,120}?)(?=\s*(?:Móvil|Teléfono|Email|\+\d|Correo|$|\n))",
        
        # Patrón para encargados: "Encargado[a]:" seguido de texto
        r"Encargada?:\s*([^\n\r]{5,120}?)(?=\s*(?:Móvil|Teléfono|Email|\+\d|Correo|$|\n))",
        
        # Patrón simple: Solo nombres después de dos puntos
        r":\s*([A-Za-z][A-Za-z\s\.]{8,50})(?=\s*(?:Móvil|Teléfono|Email|\+\d|$|\n))",
    ]
    
    for i, pattern in enumerate(contact_patterns):
        match = re.search(pattern, normalized_text, re.IGNORECASE)
        if match:
            full_contact = match.group(1).strip()
            
            # Limpiar texto extraído
            full_contact = re.sub(r'^[:\|\-\s]+|[:\|\-\s]+$', '', full_contact)
            
            # Validar calidad básica
            if (len(full_contact) >= 5 and 
                ' ' in full_contact and
                re.search(r'[A-Za-z]', full_contact) and
                not full_contact.lower().startswith(('contacto', 'responsable', 'coordinador'))):
                
                # Separar nombre y cargo
                name, position = separate_name_and_position(full_contact)
                
                if name:
                    contact_info["name"] = name
                    contact_info["position"] = position
                    logger.debug(f"✅ Contacto extraído con patrón {i+1}: '{name}' | '{position}'")
                    break
    
    # === EXTRACCIÓN INDEPENDIENTE DE TELÉFONOS ===
    phone_patterns = [
        # Patrones universales para números de teléfono
        r"(?:Móvil|Celular|Teléfono|Tel\.?|Phone):\s*(\+?\d{1,4}[-\(\)\s]*\d{3,4}[-\s]*\d{3,4}[-\s]*\d{3,4})",
        r"(\+\d{1,4}[-\(\)\s]*\d{3,4}[-\s]*\d{3,4}[-\s]*\d{3,4})",
        r"(?<!\d)(\d{4}[-\s]\d{4})(?!\d)",
        r"(?<!\d)(\d{3}[-\s]\d{4})(?!\d)",
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, normalized_text)
        if match:
            phone = re.sub(r'\s+', ' ', match.group(1).strip())
            contact_info["phone"] = phone
            logger.debug(f"✅ Teléfono encontrado: '{phone}'")
            break
    
    # === EXTRACCIÓN UNIVERSAL DE EMAILS ===
    email_patterns = [
        r"(?:Email|E-mail|Correo|Mail):\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b",
    ]
    
    for pattern in email_patterns:
        match = re.search(pattern, normalized_text)
        if match:
            email = match.group(1).strip().lower()
            contact_info["email"] = email
            logger.debug(f"✅ Email encontrado: '{email}'")
            break
    
    return contact_info

def extract_company_info(text: str) -> Dict[str, Optional[str]]:
    """Extrae información de empresas con patrones UNIVERSALES"""
    
    company_info = {
        "name": None,
        "industry": None,
        "description": None
    }
    
    normalized_text = normalize_text(text)
    
    # === PATRONES UNIVERSALES PARA EMPRESAS ===
    company_patterns = [
        # Patrones con etiquetas explícitas
        r"(?:Empresa|Entidad|Compañía|Organización):\s*([^\n\r:]{5,100}?)(?=\s*(?:\n|Contacto|Responsable|$))",
        
        # Patrón con paréntesis (nombre comercial)
        r"(?:Empresa|Entidad):\s*[^(]*\(([^)]{5,80})\)",
        
        # Empresas seguidas de verbos de acción
        r"([A-Z][A-Za-z\s,\.&]{5,80}?(?:\s*S\.?\s*A\.?|Inc\.?|Corp\.?|Ltd\.?|Group|Bank|Solutions?)?)\s+(?:está\s+)?(?:ofrece|busca|solicita|requiere|necesita)",
        
        # Nombres propios seguidos de sufijos empresariales
        r"\b([A-Z][A-Za-z\s,\.&]{5,80}?)\s*(?:S\.?\s*A\.?|Inc\.?|Corporation|Corp\.?|Limited|Ltd\.?|Group|Bank|Solutions?|Airlines?|Systems?)\b",
        
        # Grupos empresariales
        r"\b(GRUPO\s+[A-Z][A-Za-z\s]{2,30}(?:\s*,\s*S\.?\s*A\.?)?)\b",
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, normalized_text, re.IGNORECASE)
        if match:
            company_name = match.group(1).strip()
            
            # Limpiar nombre
            company_name = re.sub(r'^\W+|\W+$', '', company_name)
            company_name = re.sub(r'\s+', ' ', company_name)
            
            # Aplicar correcciones generales de OCR para empresas
            company_corrections = {
                r'\bIntemational\b': 'International',
                r'\bAirhnes\b': 'Airlines',
                r'\bSystems?\b': 'Systems',
                r'\bSolutions?\b': 'Solutions',
                r'\bGroup\b': 'Group',
                r'\bBank\b': 'Bank',
            }
            
            for error_pattern, correction in company_corrections.items():
                company_name = re.sub(error_pattern, correction, company_name, flags=re.IGNORECASE)
            
            # Validación universal
            if (10 <= len(company_name) <= 80 and
                not re.match(r'^[\d\s\.,\-\(\)]+$', company_name) and
                not any(word in company_name.lower() for word in ['contacto', 'telefono', 'email', 'movil', 'whatsapp', 'elaborar', 'riesg', 'infor', 'jeceutivos', 'p.', 'm.', 'de lune']) and
                len(company_name.split()) >= 2 and len(company_name.split()) <= 8 and
                not re.search(r'\b[a-z]{1,2}\.\s+[a-z]{1,2}\.\s+de\s+[a-z]+\b', company_name.lower()) and  # Evitar "p. m. de lune"
                not re.search(r'^[a-z\s\.]{1,15}$', company_name.lower())):
                
                company_info["name"] = company_name
                logger.debug(f"✅ Empresa encontrada: '{company_name}'")
                break
    
    # === DETECCIÓN UNIVERSAL DE INDUSTRIA ===
    if company_info["name"]:
        full_text = (company_info["name"] + " " + normalized_text).lower()
        
        # Clasificación de industrias escalable
        industry_patterns = {
            "financiero": [
                r'\b(?:banco|bank|financ|credit|investment|seguros|insurance|tower)\b',
                r'\b(?:capital|fund|lending|mortgage|financial services)\b'
            ],
            "aviación": [
                r'\b(?:aviación|aviation|airline|aero|vuelo|flight|airport)\b',
                r'\b(?:copa|latam|american airlines|delta|united)\b'
            ],
            "consultoría": [
                r'\b(?:consult|advisory|audit|pwc|deloitte|kpmg|accenture)\b',
                r'\b(?:business intelligence|strategy|management)\b'
            ],
            "educación": [
                r'\b(?:universidad|university|educación|education|academy|college|instituto)\b',
                r'\b(?:training|capacitación|learning|enseñanza)\b'
            ],
            "salud": [
                r'\b(?:hospital|clinic|medical|health|pharma|farmacia|medicina)\b',
                r'\b(?:healthcare|wellness|biotech|biotechnology)\b'
            ],
            "manufactura": [
                r'\b(?:manufactur|industrial|fabrica|factory|production|automotive)\b',
                r'\b(?:engineering|ingeniería|construction|construcción)\b'
            ],
            "retail": [
                r'\b(?:retail|store|shop|commercial|ventas|sales|marketing)\b',
                r'\b(?:ecommerce|marketplace|shopping|tienda)\b'
            ],
            "gobierno": [
                r'\b(?:gobierno|government|ministerio|ministry|municipal|state)\b',
                r'\b(?:public|público|sector público|administration)\b'
            ],
            "servicios": [
                r'\b(?:servicios|services|logistics|logística|transport|delivery)\b',
                r'\b(?:cleaning|security|maintenance|support)\b'
            ],
            "tecnología": [
                r'\b(?:tech|system|software|digital|solutions|desarrollo|programación|IT|informática|tecnología)\b',
                r'\b(?:microsoft|google|amazon|oracle|SAP|IBM|cisco)\b',
                r'\b(?:web|app|mobile|cloud|AI|machine learning|data)\b'
            ]
        }
        
        for industry, patterns in industry_patterns.items():
            if any(re.search(pattern, full_text, re.IGNORECASE) for pattern in patterns):
                company_info["industry"] = industry
                logger.debug(f"✅ Industria detectada: '{industry}'")
                break
    
    return company_info

def extract_requirements_and_knowledge(text: str) -> Dict[str, List[str]]:
    """Extrae secciones usando patrones UNIVERSALES y ESCALABLES"""
    
    result = {
        "requirements": [],
        "knowledge": [],
        "functions": [],
        "benefits": []
    }
    
    normalized_text = normalize_text(text)
    
    # === PATRONES UNIVERSALES PARA SECCIONES ===
    universal_section_patterns = {
        "requirements": [
            # Patrones en español
            r"(?:Requisitos?|Perfil|Requerimientos?|Condiciones?):\s*(.*?)(?=(?:Conocimientos?|Funciones?|Ofrecemos?|Beneficios?|Responsabilidades?|$))",
            # Patrones en inglés
            r"(?:Requirements?|Profile|Qualifications?):\s*(.*?)(?=(?:Knowledge|Functions?|We offer|Benefits?|Responsibilities?|$))",
            # Patrones mixtos
            r"(?:Buscamos|Se requiere|Necesitamos):\s*(.*?)(?=(?:Conocimientos?|Funciones?|Ofrecemos?|$))",
        ],
        "knowledge": [
            # Conocimientos y habilidades
            r"(?:Conocimientos?|Habilidades?|Skills?|Competencias?)(?:\s+(?:en|requeridos?|necesarios?))?\s*:?\s*(.*?)(?=(?:Funciones?|Ofrecemos?|Beneficios?|$))",
            # Experiencia
            r"(?:Experiencia|Experience)(?:\s+(?:en|in|con|with))?\s*:?\s*(.*?)(?=(?:Funciones?|Ofrecemos?|Beneficios?|$))",
        ],
        "functions": [
            # Funciones y responsabilidades
            r"(?:Algunas?\s+de\s+las?\s+)?(?:Funciones?|Responsabilidades?|Actividades?|Tareas?)(?:\s+(?:principales?|a\s+realizar))?\s*:?\s*(.*?)(?=(?:Ofrecemos?|Beneficios?|Requisitos?|$))",
            # En inglés
            r"(?:Functions?|Responsibilities?|Tasks?|Activities?):\s*(.*?)(?=(?:We offer|Benefits?|Requirements?|$))",
        ],
        "benefits": [
            # Beneficios ofrecidos
            r"(?:Ofrecemos?|Beneficios?|Ofrecen|Qué\s+ofrecemos|Lo\s+que\s+ofrecemos)\s*:?\s*(.*?)(?=(?:Nota|Dudas?|Interesados?|Requisitos?|$))",
            # En inglés
            r"(?:We offer|Benefits?|What we offer):\s*(.*?)(?=(?:Note|Questions?|Interested?|Requirements?|$))",
        ]
    }
    
    # === PROCESAMIENTO UNIVERSAL ===
    for section_name, patterns in universal_section_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, normalized_text, re.DOTALL | re.IGNORECASE)
            if match:
                section_text = match.group(1).strip()
                
                # Extraer elementos con calidad
                items = extract_universal_list_items(section_text)
                
                if items:
                    result[section_name] = items
                    logger.debug(f"✅ Sección '{section_name}' extraída: {len(items)} elementos")
                    break
    
    return result

def extract_universal_list_items(text: str) -> List[str]:
    """Extrae elementos de lista usando patrones UNIVERSALES"""
    
    items = []
    
    # Patrones universales para listas
    universal_bullet_patterns = [
        # Viñetas tradicionales
        r'^[•⚫⭐✓✔·\-→+*◦▪▫]\s+(.+)$',
        r'\n[•⚫⭐✓✔·\-→+*◦▪▫]\s+(.+)',
        # Números y letras
        r'^[0-9]+\.?\s+(.+)$',
        r'\n[0-9]+\.?\s+(.+)',
        r'^[a-zA-Z]\)?\.\s+(.+)$',
        # Guiones y espacios
        r'^\s*[-*+]\s+(.+)$',
        r'\n\s*[-*+]\s+(.+)',
        # Patrones en español
        r'^\s*(?:•|-)?\s*(?:Conocimiento|Experiencia|Manejo|Dominio)\s+(?:de|en)\s+(.+)$',
        r'^\s*(?:•|-)?\s*(.{15,150})$',  # Líneas de longitud media
    ]
    
    # Probar cada patrón
    for pattern in universal_bullet_patterns:
        matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
        if matches:
            clean_items = []
            for item in matches:
                # Limpiar elemento
                item = item.strip()
                item = re.sub(r'\s+', ' ', item)
                item = re.sub(r'^[^\w]*|[^\w]*$', '', item)
                
                # Validación universal de calidad
                if (10 <= len(item) <= 200 and
                    len(item.split()) >= 3 and len(item.split()) <= 30 and
                    not re.match(r'^[\d\s\.,\-\(\)]+$', item) and
                    not item.lower() in ['requisitos', 'conocimientos', 'funciones', 'beneficios', 'requirements', 'knowledge', 'functions', 'benefits']):
                    clean_items.append(item)
            
            if clean_items:
                items = clean_items[:15]  # Máximo 15 elementos
                break
    
    # Si no hay viñetas, dividir por líneas con calidad
    if not items:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines:
            line = re.sub(r'\s+', ' ', line)
            line = re.sub(r'^[^\w]*|[^\w]*$', '', line)
            
            if (15 <= len(line) <= 200 and
                len(line.split()) >= 4 and len(line.split()) <= 25 and
                not re.match(r'^[\d\s\.,\-\(\)]+$', line) and
                not line.lower() in ['requisitos', 'conocimientos', 'funciones', 'beneficios']):
                items.append(line)
        
        items = items[:10]  # Máximo 10 elementos sin viñetas
    
    return list(dict.fromkeys(items))  # Eliminar duplicados

def is_job_post(text: str, description: str) -> Tuple[bool, Optional[str], int, bool]:
    """Clasificación UNIVERSAL de ofertas laborales"""
    
    text = normalize_text(text)
    description = normalize_text(description)
    combined_text = f"{text} {description}".lower()
    
    # Indicadores positivos UNIVERSALES
    universal_job_indicators = {
        # Términos principales
        "práctica profesional": 30,
        "práctica laboral": 30,
        "práctica pre-profesional": 25,
        "pasantía": 25,
        "internship": 25,
        "vacante": 20,
        "vacancy": 20,
        "empleo": 15,
        "job": 15,
        "trabajo": 12,
        "work": 12,
        "puesto": 12,
        "position": 12,
        
        # Estructuras comunes
        "empresa:": 15,
        "company:": 15,
        "entidad:": 15,
        "contacto:": 12,
        "contact:": 12,
        "requisitos:": 12,
        "requirements:": 12,
        "conocimientos": 10,
        "knowledge": 10,
        "funciones": 10,
        "functions": 10,
        "ofrecemos": 12,
        "we offer": 12,
        
        # Verbos de acción
        "está ofreciendo": 15,
        "is offering": 15,
        "está buscando": 15,
        "is looking for": 15,
        "se solicita": 12,
        "seeking": 12,
        "necesitamos": 10,
        "we need": 10,
        "enviar hoja de vida": 15,
        "send resume": 15,
        "enviar cv": 15,
        "interesados enviar": 12,
        "interested send": 12,
    }
    
    # Indicadores negativos UNIVERSALES
    universal_non_job_indicators = {
        # Eventos y actividades
        "talleres": -20,
        "workshop": -20,
        "seminario": -20,
        "seminar": -20,
        "conferencia": -20,
        "conference": -20,
        "evento": -15,
        "event": -15,
        "capacitación": -15,
        "training": -15,
        
        # Estados finalizados
        "matrícula": -25,
        "enrollment": -25,
        "ha finalizado": -30,
        "has ended": -30,
        "cupos agotados": -25,
        "spots filled": -25,
        "convocatoria cerrada": -25,
        "application closed": -25,
        "inscripciones cerradas": -25,
        "registration closed": -25,
    }
    
    score = 0
    
    # Calcular puntuación
    for term, weight in universal_job_indicators.items():
        if term in combined_text:
            score += weight
    
    for term, weight in universal_non_job_indicators.items():
        if term in combined_text:
            score += weight
    
    # Verificar si está expirada
    expiration_patterns = [
        "ha finalizado", "has ended", "se acabó", "cupos agotados", 
        "spots filled", "convocatoria cerrada", "application closed",
        "inscripciones cerradas", "registration closed"
    ]
    is_expired = any(pattern in combined_text for pattern in expiration_patterns)
    
    is_job = score >= 25  # Umbral ajustado
    
    # Determinar tipo UNIVERSAL
    job_type = "No identificado"
    if is_job:
        type_patterns = {
            "Práctica Profesional": ["práctica profesional", "professional internship"],
            "Práctica Laboral": ["práctica laboral", "work internship"],
            "Práctica Pre-profesional": ["práctica pre-profesional", "pre-professional"],
            "Pasantía": ["pasantía", "internship"],
            "Vacante": ["vacante", "vacancy"],
            "Empleo": ["empleo", "job", "trabajo", "work", "position"],
        }
        
        for job_type_name, patterns in type_patterns.items():
            if any(pattern in combined_text for pattern in patterns):
                job_type = job_type_name
                break
        
        if job_type == "No identificado":
            job_type = "Oferta Laboral"
    
    return is_job, job_type, score, is_expired

def extract_job_data(image_text: str, post_description: str) -> Dict:
    """Extrae información usando TODOS los patrones universales"""
    
    primary_text = normalize_text(post_description) if post_description else ""
    secondary_text = normalize_text(image_text) if image_text else ""
    
    # Estrategia inteligente de combinación
    if len(primary_text) < 100 and len(secondary_text) > 50:
        combined_text = primary_text + "\n\n" + secondary_text
        logger.debug("Usando combinación: descripción + OCR")
    elif len(primary_text) > 50:
        combined_text = primary_text
        logger.debug("Usando solo descripción del post")
    else:
        combined_text = secondary_text
        logger.debug("Usando solo texto OCR")
    
    # Extraer información usando funciones universales
    company_info = extract_company_info(combined_text)
    contact_info = extract_contact_info(combined_text)
    sections_info = extract_requirements_and_knowledge(combined_text)
    
    # Búsqueda redundante en ambas fuentes
    if not contact_info.get('name') and secondary_text:
        logger.debug("Buscando contacto en OCR como respaldo")
        ocr_contact = extract_contact_info(secondary_text)
        contact_info.update({k: v for k, v in ocr_contact.items() if v})
    
    if not company_info.get('name') and secondary_text:
        logger.debug("Buscando empresa en OCR como respaldo")
        ocr_company = extract_company_info(secondary_text)
        if ocr_company.get('name'):
            company_info.update(ocr_company)
    
    return {
        "company_name": company_info["name"],
        "company_industry": company_info["industry"],
        "contact_name": contact_info.get("name"),
        "contact_position": contact_info.get("position"),
        "contact_email": contact_info.get("email"),
        "contact_phone": contact_info.get("phone"),
        "position_title": extract_position_title(combined_text),
        "requirements": sections_info["requirements"],
        "knowledge_required": sections_info["knowledge"],
        "functions": sections_info["functions"],
        "benefits": sections_info["benefits"],
        "is_active": not is_job_post(primary_text, secondary_text)[3],
        "work_modality": extract_work_modality(combined_text),
        "duration": extract_duration(combined_text),
    }

def extract_position_title(text: str) -> Optional[str]:
    """Extrae títulos de puesto con patrones UNIVERSALES"""
    
    normalized_text = normalize_text(text).lower()
    
    # Patrones universales para títulos
    universal_title_patterns = [
        # Patrones en español
        r"práctica\s+(?:profesional|laboral)\s+(?:como|en|de)\s+([^\n,.]+)",
        r"(?:puesto|cargo|vacante|posición)\s+(?:de|para|como)\s+([^\n,.]+)",
        r"se\s+(?:busca|requiere|solicita|necesita)\s+(?:un|una)?\s*([^\n,.]+)",
        r"(?:analista|ingeniero|desarrollador|especialista|gerente|coordinador|supervisor|asistente|técnico)\s+(?:de|en)\s+([^\n,.]+)",
        
        # Patrones en inglés
        r"(?:position|job|role)\s+(?:as|for|of)\s+([^\n,.]+)",
        r"looking\s+for\s+(?:a|an)?\s*([^\n,.]+)",
        r"seeking\s+(?:a|an)?\s*([^\n,.]+)",
        r"(?:analyst|engineer|developer|specialist|manager|coordinator|supervisor|assistant|technician)\s+(?:of|in)\s+([^\n,.]+)",
    ]
    
    for pattern in universal_title_patterns:
        match = re.search(pattern, normalized_text)
        if match:
            title = match.group(1).strip()
            title = re.sub(r'^(?:un|una|a|an)\s+', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s+', ' ', title)
            
            if 3 <= len(title) <= 100:
                return title.strip().title()
    
    return None

def extract_work_modality(text: str) -> Optional[str]:
    """Extrae modalidad con patrones UNIVERSALES"""
    
    normalized_text = normalize_text(text).lower()
    
    modality_patterns = {
        "Presencial": [r"presencial", r"in-person", r"on-site", r"oficina", r"office"],
        "Remoto": [r"remoto", r"remote", r"virtual", r"desde casa", r"work from home", r"home office"],
        "Híbrido": [r"híbrido", r"hybrid", r"mixto", r"mixed", r"semi-presencial"],
    }
    
    for modality, patterns in modality_patterns.items():
        if any(re.search(pattern, normalized_text) for pattern in patterns):
            return modality
    
    return None

def extract_duration(text: str) -> Optional[str]:
    """Extrae duración con patrones UNIVERSALES"""
    
    normalized_text = normalize_text(text).lower()
    
    # Patrones universales para duración
    duration_patterns = [
        r"(?:duración|duration):\s*([^\n]+)",
        r"(?:período|period):\s*([^\n]+)",
        r"(\d+)\s*(?:meses?|months?)",
        r"(\d+)\s*(?:años?|years?)",
        r"(\d+)\s*(?:semanas?|weeks?)",
        r"(?:por|for)\s+(\d+\s*(?:meses?|años?|semanas?|months?|years?|weeks?))",
    ]
    
    for pattern in duration_patterns:
        match = re.search(pattern, normalized_text)
        if match:
            duration = match.group(1).strip()
            return duration
    
    return None

def extract_experience_education(text: str) -> Dict[str, Optional[str]]:
    """Extrae experiencia y educación con patrones UNIVERSALES"""
    
    normalized_text = normalize_text(text)
    
    result = {"experience": None, "education": None}
    
    # Patrones universales para experiencia
    experience_patterns = [
        r"(?:experiencia|experience)(?:\s+(?:mínima|minimum|de|of))?\s*:?\s*(\d+(?:-\d+)?|\d+\+)\s*(?:años?|meses?|years?|months?)",
        r"(\d+(?:-\d+)?|\d+\+)\s*(?:años?|meses?|years?|months?)\s*(?:de\s+experiencia|of experience|experience)",
        r"(?:con|with)\s+(?:al menos|at least)?\s*(\d+(?:-\d+)?|\d+\+)\s*(?:años?|meses?|years?|months?)",
    ]
    
    for pattern in experience_patterns:
        match = re.search(pattern, normalized_text, re.IGNORECASE)
        if match:
            exp_text = match.group(0).lower()
            exp_value = match.group(1)
            unit = " años" if any(word in exp_text for word in ["año", "year"]) else " meses"
            result["experience"] = exp_value + unit
            break
    
    # Patrones universales para educación
    education_patterns = [
        r"(?:estudiante|student|egresado|graduate)\s+(?:de|of|en|in)\s+([^\n,.;]+)",
        r"(?:facultad de|faculty of|carrera de|degree in|título en|bachelor)\s+([^\n,.;]+)",
        r"(?:licenciatura|bachelor|master|maestría|engineering|ingeniería)\s+(?:en|in|de|of)\s+([^\n,.;]+)",
        r"(?:cursando|studying|estudiando)\s+([^\n,.;]+)",
    ]
    
    for pattern in education_patterns:
        match = re.search(pattern, normalized_text, re.IGNORECASE)
        if match:
            education = match.group(1).strip()
            education = re.sub(r'[.,;:]+$', '', education)
            result["education"] = education.title()
            break
    
    return result

def extract_skills_and_technologies(text: str) -> Dict[str, List[str]]:
    """Extrae habilidades con patrones UNIVERSALES y escalables"""

    normalized_text = normalize_text(text)
    
    result = {
        "programming_languages": [],
        "technologies": [],
        "soft_skills": []
    }
    
    # Patrones universales para lenguajes de programación
    programming_patterns = [
        r'\b(Python|Java|JavaScript|TypeScript|C\+\+|C#|PHP|Go|Rust|Swift|Kotlin|Ruby|Scala|R|MATLAB)\b',
        r'\b(HTML|CSS|React|Angular|Vue|Node\.?js|Django|Flask|Spring|Laravel|Rails)\b',
        r'\b(SQL|MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch|Oracle|SQLite)\b'
    ]

    for pattern in programming_patterns:
        matches = re.findall(pattern, normalized_text, re.IGNORECASE)
        result["programming_languages"].extend([m.upper() if m.upper() in ['SQL', 'CSS', 'HTML', 'PHP'] else m for m in matches])
    
    # Patrones universales para tecnologías
    tech_patterns = [
        r'\b(AWS|Azure|GCP|Google Cloud|Docker|Kubernetes|Git|GitHub|GitLab|Jenkins)\b',
        r'\b(Linux|Windows|macOS|Ubuntu|Apache|Nginx|Tomcat|IIS)\b',
        r'\b(Tableau|Power BI|Excel|Word|PowerPoint|Visio|AutoCAD|SolidWorks)\b',
        r'\b(Jira|Confluence|Slack|Teams|Zoom|Salesforce|SAP|Oracle)\b'
    ]
    
    for pattern in tech_patterns:
        matches = re.findall(pattern, normalized_text, re.IGNORECASE)
        result["technologies"].extend(matches)

    # Patrones universales para habilidades blandas
    soft_skills_patterns = [
        r'\b(comunicación|communication|trabajo en equipo|teamwork|liderazgo|leadership)\b',
        r'\b(adaptabilidad|adaptability|resolución de problemas|problem solving|creatividad|creativity)\b',
        r'\b(empatía|empathy|pensamiento crítico|critical thinking|gestión del tiempo|time management)\b',
        r'\b(negociación|negotiation|presentación|presentation|análisis|analysis|organización|organization)\b'
    ]

    for pattern in soft_skills_patterns:
        matches = re.findall(pattern, normalized_text, re.IGNORECASE)
        result["soft_skills"].extend(matches)

    # Limpiar duplicados y normalizar
    for skill_type in result:
        result[skill_type] = list(dict.fromkeys(result[skill_type]))  # Eliminar duplicados
        result[skill_type] = result[skill_type][:10]  # Máximo 10 elementos por categoría

    return result
