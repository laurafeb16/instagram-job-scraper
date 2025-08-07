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
    normalized = re.sub(r'\bIA\b', 'ia', normalized)  # IA como palabra completa → ia
    normalized = re.sub(r'IA([a-z])', r'ia\1', normalized)  # IA seguido de minúscula → ia
    normalized = re.sub(r'([A-Z])IA([a-z])', r'\1ia\2', normalized)  # CompanIA → Compania
    
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
    }
    
    for pattern, replacement in accent_patterns.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    
    # 3. Errores de consonantes comunes (OCR confunde estas letras)
    consonant_patterns = {
        r'\b([A-Za-z]*?)rn([A-Za-z]*?)\b': r'\1m\2',  # 'rn' → 'm'
        r'\b([A-Za-z]*?)cl([A-Za-z]*?)\b': r'\1d\2',   # 'cl' → 'd' 
        r'\b([A-Za-z]*?)li([A-Za-z]*?)\b': r'\1h\2',   # 'li' → 'h'
        r'\bii\b': 'n',  # 'ii' → 'n' cuando es palabra completa
    }
    
    for pattern, replacement in consonant_patterns.items():
        # Solo aplicar si la palabra resultante tiene sentido
        matches = re.finditer(pattern, normalized)
        for match in matches:
            original_word = match.group(0)
            corrected = re.sub(pattern, replacement, original_word)
            if len(corrected) >= 3:  # Evitar correcciones muy cortas
                normalized = normalized.replace(original_word, corrected)
    
    # 4. Correcciones de sufijos comunes
    suffix_patterns = {
        r'([a-zA-Z]+?)cion\b': r'\1ción',  # -cion → -ción
        r'([a-zA-Z]+?)ciones\b': r'\1ciones',  # mantener si ya tiene tilde en otro lado
        r'([a-zA-Z]+?)sion\b': r'\1sión',  # -sion → -sión
    }
    
    for pattern, replacement in suffix_patterns.items():
        normalized = re.sub(pattern, replacement, normalized)
    
    # 5. Correcciones de palabras técnicas comunes
    tech_patterns = {
        r'\bs3L\b': 'SQL',
        r'\bMys3L\b': 'MySQL',
        r'\bPostgres3L\b': 'PostgreSQL',
        r'\bSIMUhNK\b': 'SIMULINK',
        r'\bMATLAB/SIMUhNK\b': 'MATLAB/SIMULINK',
        r'\bpythOn\b': 'Python',
        r'\bJavascript\b': 'JavaScript',
        r'\bjavascript\b': 'JavaScript',
    }
    
    for pattern, replacement in tech_patterns.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    
    # 6. Correcciones de 'h' perdida o mal colocada
    h_patterns = {
        r'\b([a-zA-Z]*?)l([a-zA-Z]*?)idad\b': r'\1bilidad',  # habihdad → habilidad
        r'\b([a-zA-Z]*?)l([a-zA-Z]*?)dades\b': r'\1bilidades',
    }
    
    for pattern, replacement in h_patterns.items():
        normalized = re.sub(pattern, replacement, normalized)
    
    # 7. Correcciones de nombres propios comunes
    proper_name_patterns = {
        r'\bPanamena\b': 'Panameña',
        r'\bAvIAcion\b': 'Aviación',
        r'\bIngenierIA\b': 'Ingeniería',
        r'\bComputacionales\b': 'Computacionales',
        r'\bExperiencIA\b': 'Experiencia',
    }
    
    for pattern, replacement in proper_name_patterns.items():
        normalized = re.sub(pattern, replacement, normalized)
    
    # 8. Limpiar espacios múltiples y caracteres extraños
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = re.sub(r'[^\w\s\.,;:()\-+@áéíóúñü]', ' ', normalized)
    normalized = normalized.strip()
    
    return normalized

def extract_contact_info(text: str) -> Dict[str, Optional[str]]:
    """Extrae información de contacto con patrones generales escalables"""
    
    contact_info = {
        "name": None,
        "position": None,
        "email": None,
        "phone": None,
        "mobile": None
    }
    
    normalized_text = normalize_text(text)
    
    # === PATRONES GENERALES PARA NOMBRES ===
    general_contact_patterns = [
        # Patrón principal: "Contacto: Nombre | Cargo"
        r"Contacto:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})(?:\s*[\|\-]\s*([^|\n]+?))?(?=\s*(?:Móvil|Teléfono|Email|\+\d|\d{4}|$))",
        
        # Títulos profesionales + Nombre
        r"((?:Lcda?\.|Dr[a]?\.|Ing\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        
        # Nombre + Cargo conocido
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s*[\|\-]\s*)?(Analista|Gerente|Director|Coordinador|Oficial|Especialista|Manager|Ejecutivo)(?:\s+[a-z].*?)?(?=\s*(?:Móvil|Teléfono|\+\d))",
        
        # Nombre antes de departamentos
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s*[\|\-]\s*)?(?:Talent\s+Development|Human\s+Resources|Recursos\s+Humanos|Development\s+Center)",
    ]
    
    for pattern in general_contact_patterns:
        match = re.search(pattern, normalized_text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            
            # Validación general de nombres
            if (3 <= len(name) <= 50 and
                re.match(r'^[A-Za-z\.\s]+$', name) and
                len(name.split()) <= 4 and  # Máximo 4 palabras
                not any(word.lower() in ['contacto', 'email', 'telefono', 'movil'] for word in name.split())):
                
                contact_info["name"] = name
                
                # Extraer cargo si existe
                if len(match.groups()) >= 2 and match.group(2):
                    position = match.group(2).strip()
                    position = re.sub(r'(Móvil|Teléfono|Email).*$', '', position).strip()
                    if 3 <= len(position) <= 100:
                        contact_info["position"] = position
                break
    
    # === PATRONES GENERALES PARA TELÉFONOS ===
    phone_patterns = [
        r"(?:Móvil|Celular|Teléfono|Tel\.?):\s*(\+\(?\d{3}\)?\s*\d{4}[-\s]?\d{4})",
        r"(\+\(?\d{3}\)?\s*\d{4}[-\s]?\d{4})",
        r"(\d{4}[-\s]\d{4})",
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, normalized_text)
        if match:
            phone = match.group(1).strip()
            contact_info["phone"] = phone
            break
    
    return contact_info

def extract_company_info(text: str) -> Dict[str, Optional[str]]:
    """Extrae información de empresas con patrones escalables"""
    
    company_info = {
        "name": None,
        "industry": None,
        "description": None
    }
    
    normalized_text = normalize_text(text)
    
    # === PATRONES GENERALES PARA EMPRESAS ===
    general_company_patterns = [
        # Patrón principal: "Empresa: Nombre de la Empresa"
        r"(?:Empresa|Entidad):\s*([A-Z][A-Za-z\s,\.&]{8,80}?(?:\s*S\.?\s*A\.?|Inc\.?|Corp\.?|Group|Bank|Solutions?)?)(?=\s|$|\n)",
        
        # Empresas en mayúsculas (común en OCR)
        r"(?:Empresa|Entidad):\s*([A-Z][A-Z\s,\.&]{10,60})",
        
        # Empresa seguida de "está ofreciendo"
        r"([A-Z][A-Za-z\s,\.&]{8,60}?(?:\s*S\.?\s*A\.?)?)\s+está\s+(?:ofreciendo|buscando)",
    ]
    
    for pattern in general_company_patterns:
        match = re.search(pattern, normalized_text)
        if match:
            company_name = match.group(1).strip()
            
            # Limpiar nombre de empresa
            company_name = re.sub(r'^\W+|\W+$', '', company_name)
            company_name = re.sub(r'\s+', ' ', company_name)
            
            # Filtros de calidad generales
            if (8 <= len(company_name) <= 80 and
                not any(word in company_name.lower() for word in ['contacto', 'telefono', 'email'])):
                
                company_info["name"] = company_name
                break
    
    # === DETECCIÓN DE INDUSTRIA GENERAL ===
    if company_info["name"]:
        company_text = (company_info["name"] + " " + normalized_text).lower()
        
        # Patrones de industria escalables
        industry_keywords = {
            "aviación": [r"aviación", r"aviation", r"airline", r"aereo", r"copa"],
            "tecnología": [r"tech", r"system", r"software", r"digital", r"solutions", r"manz", r"grupo"],
            "financiero": [r"banco", r"bank", r"financ", r"tower", r"credit"],
            "consultoría": [r"consult", r"advisory", r"pwc", r"audit"],
            "manufactura": [r"manufactur", r"industrial", r"fabrica"],
            "educación": [r"universidad", r"educación", r"academy", r"utp"],
            "gobierno": [r"gobierno", r"ministerio", r"gob\.pa", r"dgcp"],
        }
        
        for industry, patterns in industry_keywords.items():
            if any(re.search(pattern, company_text) for pattern in patterns):
                company_info["industry"] = industry
                break
    
    return company_info

def extract_requirements_and_knowledge(text: str) -> Dict[str, List[str]]:
    """
    Extrae secciones de manera general y escalable.
    Funciona con diferentes formatos y estructuras.
    """
    
    result = {
        "requirements": [],
        "knowledge": [],
        "functions": [],
        "benefits": []
    }
    
    normalized_text = normalize_text(text)
    
    # === PATRONES GENERALES PARA SECCIONES ===
    section_patterns = {
        "requirements": [
            r"(?:Requisitos?|Perfil|Requerimientos?):\s*(.*?)(?=(?:Conocimientos?|Funciones?|Ofrecemos?|Beneficios?|La\s+práctica|Universidad|$))",
            r"(?:Requisitos?|Perfil|Requerimientos?)\s+(.*?)(?=(?:Conocimientos?|Funciones?|Ofrecemos?|Beneficios?|La\s+práctica|Universidad|$))",
        ],
        "knowledge": [
            r"Conocimientos?\s*(?:en|requeridos?|necesarios?)?\s*:?\s*(.*?)(?=(?:Funciones?|Ofrecemos?|Beneficios?|La\s+práctica|Universidad|$))",
            r"(?:Habilidades?|Skills?|Competencias?)\s*:?\s*(.*?)(?=(?:Funciones?|Ofrecemos?|Beneficios?|La\s+práctica|Universidad|$))",
        ],
        "functions": [
            r"(?:Algunas?\s+de\s+las?\s+)?Funciones?\s*(?:de\s+colaboración)?\s*(?:en\s+el\s+área)?\s*:?\s*(.*?)(?=(?:Ofrecemos?|Beneficios?|La\s+práctica|Universidad|$))",
            r"(?:Responsabilidades?|Actividades?|Tareas?)\s*:?\s*(.*?)(?=(?:Ofrecemos?|Beneficios?|La\s+práctica|Universidad|$))",
        ],
        "benefits": [
            r"(?:Ofrecemos?|Beneficios?|Ofrecen)\s*:?\s*(.*?)(?=(?:Nota|Dudas?|Interesados?|Universidad|Publicado|$))",
            r"(?:Qué\s+ofrecemos|Lo\s+que\s+ofrecemos)\s*:?\s*(.*?)(?=(?:Nota|Dudas?|Interesados?|Universidad|Publicado|$))",
        ]
    }
    
    # === PROCESAMIENTO GENERAL DE SECCIONES ===
    for section_name, patterns in section_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, normalized_text, re.DOTALL | re.IGNORECASE)
            if match:
                section_text = match.group(1).strip()
                
                # Detectar diferentes formatos de listas
                items = extract_list_items(section_text)
                
                if items:
                    result[section_name] = items
                    break
    
    return result

def extract_list_items(text: str) -> List[str]:
    """
    Extrae elementos de lista de manera general.
    Detecta diferentes formatos: viñetas, números, guiones, etc.
    """
    
    items = []
    
    # Patrones de viñetas generales
    bullet_patterns = [
        r'^[•⚫⭐✓✔·\-→+*]\s+(.+)$',      # Viñetas al inicio de línea
        r'\n[•⚫⭐✓✔·\-→+*]\s+(.+)',      # Viñetas después de salto
        r'^[0-9]+\.\s+(.+)$',             # Listas numeradas
        r'\n[0-9]+\.\s+(.+)',             # Listas numeradas después de salto
        r'^[a-zA-Z]\)\s+(.+)$',           # Listas con letras a) b) c)
    ]
    
    # Intentar cada patrón
    for pattern in bullet_patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        if matches:
            # Limpiar y filtrar elementos válidos
            clean_items = []
            for item in matches:
                item = item.strip()
                if (len(item) > 10 and  # Mínimo 10 caracteres
                    not re.match(r'^[\d\s\.,\-]+$', item) and  # No solo números/puntuación
                    len(item.split()) >= 3):  # Al menos 3 palabras
                    clean_items.append(item)
            
            if clean_items:
                items = clean_items
                break
    
    # Si no hay viñetas, dividir por líneas significativas
    if not items:
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines:
            if (len(line) > 15 and
                not re.match(r'^[\d\s\.,\-]+$', line) and
                len(line.split()) >= 4 and
                line.lower() not in ['requisitos', 'conocimientos', 'funciones', 'beneficios']):
                items.append(line)
    
    # Eliminar duplicados manteniendo orden
    return list(dict.fromkeys(items))

# === RESTO DE FUNCIONES CON MEJORAS GENERALES ===

def is_job_post(text: str, description: str) -> Tuple[bool, Optional[str], int, bool]:
    """Determina si es oferta laboral con criterios generales mejorados"""
    
    text = normalize_text(text)
    description = normalize_text(description)
    combined_text = f"{text} {description}".lower()
    
    # Indicadores positivos generales
    job_indicators = {
        "práctica profesional": 25,
        "práctica laboral": 25,
        "vacante": 20,
        "pasantía": 20,
        "empleo": 15,
        "trabajo": 10,
        "puesto": 10,
        "empresa:": 15,
        "contacto:": 12,
        "requisitos:": 12,
        "conocimientos": 10,
        "funciones": 10,
        "ofrecemos": 12,
        "está ofreciendo": 15,
        "está buscando": 15,
        "se solicita": 12,
        "enviar hoja de vida": 15,
        "interesados enviar": 12,
    }
    
    # Indicadores negativos generales
    non_job_indicators = {
        "talleres": -20,
        "seminario": -20,
        "conferencia": -20,
        "evento": -15,
        "matrícula": -25,
        "ha finalizado": -30,
        "cupos agotados": -25,
        "convocatoria cerrada": -25,
    }
    
    score = 0
    
    # Calcular puntuación
    for term, weight in job_indicators.items():
        if term in combined_text:
            score += weight
    
    for term, weight in non_job_indicators.items():
        if term in combined_text:
            score += weight
    
    # Verificar si está expirada
    is_expired = any(pattern in combined_text for pattern in [
        "ha finalizado", "se acabó", "cupos agotados", "convocatoria cerrada"
    ])
    
    is_job = score >= 30
    
    # Determinar tipo
    job_type = "No identificado"
    if is_job:
        if "práctica profesional" in combined_text:
            job_type = "Práctica Profesional"
        elif "práctica laboral" in combined_text:
            job_type = "Práctica Laboral"
        elif "vacante" in combined_text:
            job_type = "Vacante"
        elif "pasantía" in combined_text:
            job_type = "Pasantía"
        else:
            job_type = "Oferta Laboral"
    
    return is_job, job_type, score, is_expired

def extract_job_data(image_text: str, post_description: str) -> Dict:
    """Extrae información con procesamiento general mejorado"""
    
    primary_text = normalize_text(post_description) if post_description else ""
    secondary_text = normalize_text(image_text) if image_text else ""
    
    # Estrategia inteligente de combinación
    if len(primary_text) < 100 and len(secondary_text) > 50:
        combined_text = primary_text + "\n\n" + secondary_text
    elif len(primary_text) > 50:
        combined_text = primary_text
    else:
        combined_text = secondary_text
    
    # Extraer información usando funciones mejoradas
    company_info = extract_company_info(combined_text)
    contact_info = extract_contact_info(combined_text)
    sections_info = extract_requirements_and_knowledge(combined_text)
    
    # Si no hay contacto en descripción, buscar en OCR
    if not (contact_info.get('name') or contact_info.get('phone')) and secondary_text:
        ocr_contact = extract_contact_info(secondary_text)
        contact_info.update({k: v for k, v in ocr_contact.items() if v})
    
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
    """Extrae título del puesto con patrones generales"""
    
    normalized_text = normalize_text(text).lower()
    
    patterns = [
        r"práctica\s+(?:profesional|laboral)\s+(?:como|en)\s+([^\n,.]+)",
        r"(?:puesto|cargo|vacante)\s+(?:de|para)\s+([^\n,.]+)",
        r"se\s+(?:busca|requiere|solicita)\s+([^\n,.]+)",
        r"\b(?:analista|ingeniero|desarrollador|especialista|gerente)\s+(?:de|en)\s+([^\n,.]+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, normalized_text)
        if match:
            title = match.group(1).strip()
            title = re.sub(r'^(?:un|una)\s+', '', title)
            return title.strip().title()
    
    return None

def extract_work_modality(text: str) -> Optional[str]:
    """Extrae modalidad de trabajo"""
    
    normalized_text = normalize_text(text).lower()
    
    if re.search(r"presencial|oficina", normalized_text):
        return "Presencial"
    elif re.search(r"remoto|virtual|casa", normalized_text):
        return "Remoto"
    elif re.search(r"híbrido|mixto", normalized_text):
        return "Híbrido"
    
    return None

def extract_duration(text: str) -> Optional[str]:
    """Extrae duración del trabajo"""
    
    normalized_text = normalize_text(text).lower()
    
    duration_patterns = [
        r"(\d+)\s+meses",
        r"(\d+)\s+años",
        r"duración:\s*([^\n]+)",
        r"período:\s*([^\n]+)",
    ]
    
    for pattern in duration_patterns:
        match = re.search(pattern, normalized_text)
        if match:
            return match.group(1).strip()
    
    return None

def extract_experience_education(text: str) -> Dict[str, Optional[str]]:
    """Extrae experiencia y educación requeridas"""
    
    normalized_text = normalize_text(text)
    
    result = {"experience": None, "education": None}
    
    # Experiencia
    exp_patterns = [
        r"experiencia\s+(?:mínima\s+)?(?:de\s+)?(\d+(?:-\d+)?|\d+\+)\s+(?:años?|meses?)",
        r"(\d+(?:-\d+)?|\d+\+)\s+(?:años?|meses?)\s+(?:de\s+experiencia|requeridos)",
    ]
    
    for pattern in exp_patterns:
        match = re.search(pattern, normalized_text, re.IGNORECASE)
        if match:
            exp_str = match.group(1) + (" años" if "año" in match.group(0).lower() else " meses")
            result["experience"] = exp_str
            break
    
    # Educación
    edu_patterns = [
        r"(?:estudiante|egresado)\s+(?:de|en)\s+([^\n,.;]+)",
        r"Facultad de\s+([^\n,.;]+)",
        r"(?:carrera|título|licenciatura)\s+(?:en|de)\s+([^\n,.;]+)",
    ]
    
    for pattern in edu_patterns:
        match = re.search(pattern, normalized_text, re.IGNORECASE)
        if match:
            edu = match.group(1).strip().title()
            result["education"] = re.sub(r'[.,;:]+$', '', edu)
            break
    
    return result

def extract_skills_and_technologies(text: str) -> Dict[str, List[str]]:
    """Extrae habilidades técnicas y tecnologías específicas"""

    normalized_text = normalize_text(text)
    
    result = {
        "programming_languages": [],
        "technologies": [],
        "soft_skills": []
    }
    
    # Patrones para lenguajes de programación
    programming_patterns = [
        r'\b(Python|Java|JavaScript|C\+\+|C#|PHP|Go|Rust|Swift|Kotlin)\b',
        r'\b(React|Angular|Vue|Node\.js|Django|Flask|Spring)\b'
    ]

    for pattern in programming_patterns:
        match = re.search(pattern, normalized_text)
        if match:
            programming = match.group(1).strip()
            programming = re.sub(r'^(?:un|una)\s+', '', programming)
            return tech.strip().programming()
    
    # Patrones para tecnologías
    tech_patterns = [
        r'\b(AWS|Azure|GCP|Docker|Kubernetes|Git)\b',
        r'\b(MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch)\b'
    ]
    
    for pattern in tech_patterns:
        match = re.search(pattern, normalized_text)
        if match:
            tech = match.group(1).strip()
            tech = re.sub(r'^(?:un|una)\s+', '', tech)
            return tech.strip().title()

    # Patrones para habilidades blandas
    soft_skills_patterns = [
        r'\b(comunicación|trabajo en equipo|liderazgo|adaptabilidad|resolución de problemas)\b',
        r'\b(empatía|creatividad|pensamiento crítico|gestión del tiempo)\b'
    ]

    for pattern in soft_skills_patterns:
        match = re.search(pattern, normalized_text)
        if match:
            soft_skills = match.group(1).strip()
            soft_skills = re.sub(r'^(?:un|una)\s+', '', soft_skills)
            return soft_skills.strip().title()

    return result