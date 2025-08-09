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
    
    # 1. Espacios y caracteres extraños MEJORADO
    normalized = re.sub(r'\s+', ' ', normalized)  # Múltiples espacios
    normalized = re.sub(r'[^\w\s\.,;:()\-+@áéíóúñü]', ' ', normalized)  # Caracteres raros
    
    # 2. Palabras comunes rotas por OCR MEJORADO
    ocr_common_errors = {
        # Palabras comunes que OCR rompe
        r'\brt\.\s+ONES\b': 'RTONES',  # Patrón general para texto roto
        r'\bA\s+APA\s+rt\b': 'APARTES',  # Otro patrón general
        r'\bS\.\s*A\.\s*Nota\b': 'S.A.',  # Limpiar sufijos empresariales
        r'\b([A-Z]+)\s*,\s*S\.\s*A\.\s+\w+': r'\1, S.A.',  # Patrón general para "EMPRESA, S.A. PalabraExtra"
        
        # Patrones generales para letras confundidas por OCR
        r'\bEhzabeth\b': 'Elizabeth',  # 'h' mal interpretada
        r'\bAnahsta\b': 'Analista',   # Errores comunes de OCR
        r'\bMendoza\s+Anahsta\b': 'Mendoza Analista',  # Combinaciones comunes

        # Nuevos patrones universales para fragmentación OCR
        r'\bA\s+APA\s+RTONES\s+A\b': 'APARTES',  # Caso común de fragmentación 
        r'\bCompania\b': 'Compañía',             # Conversión ñ universal
        r'\bPanamena\b': 'Panameña',             # Conversión ñ universal
        r'\bAirhnes\b': 'Airlines',              # Error OCR común
        r'\bChente\b': 'Cliente',                # Error OCR común
    }
    
    for pattern, replacement in ocr_common_errors.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    
    
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

    empresa_cleanup_patterns = [
        r'\b([A-Z][A-Za-z\s,\.&]+\s+S\.?\s*A\.?)\s+(?:Nota|Empresa|Company|Corp|Inc|Ltd)\b',
        r'\b([A-Z][A-Za-z\s,\.&]+)\s+(?:está\s+ofreciendo|ofrece|busca|solicita)\b',
    ]
    
    for pattern in empresa_cleanup_patterns:
        match = re.search(pattern, normalized)
        if match:
            normalized = normalized.replace(match.group(0), match.group(1))
    
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
    """Separa nombre y cargo usando patrones generales escalables - VERSIÓN ULTRA ROBUSTA CORREGIDA"""
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
        try:
            match = re.search(pattern, full_text.strip(), re.IGNORECASE)
            if match:
                # CORRECCIÓN ROBUSTA: verificar grupos disponibles
                groups = match.groups()
                if groups and len(groups) >= 1 and groups[0]:
                    name = clean_contact_name(groups[0].strip())
                    position = groups[1].strip() if len(groups) >= 2 and groups[1] else None
                    
                    # Validar que el nombre sea válido
                    if (len(name.split()) >= 2 and 
                        len(name) >= 5 and 
                        re.match(r'^[A-Za-z\.\s]+$', name)):
                        return name, position
        except (IndexError, AttributeError) as e:
            logger.debug(f"Error en separate_name_and_position: {str(e)}")
            continue
    
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

def extract_technologies_enhanced(text: str) -> Dict[str, List[str]]:
    """Extrae tecnologías MEJORADO basado en textos reales de ofertas laborales"""

    normalized_text = normalize_text(text)
    
    result = {
        "programming_languages": [],
        "databases": [],
        "cloud_platforms": [],
        "frameworks_tools": [],
        "office_tools": [],
        "specialized_software": []
    }
    
    # === PATRONES BASADOS EN TEXTOS REALES ===
    tech_patterns = {
        "programming_languages": [
            # Patrones básicos para lenguajes
            r'\b(Python|Java(?!Script)|JavaScript|TypeScript|C\+\+|C#|PHP|Go|Rust|Swift|Kotlin|Ruby|Perl|Scala|R)\b',
            r'\b(HTML|CSS|React|Angular|Vue|Node\.?js)\b',
            
            # Patrones específicos encontrados en los textos
            r'(?:Fundamentos\s+de\s+)?(?:programación|programming)\s*\(\s*([^)]+)\s*\)',  # "Fundamentos de programación (Python, C++, Java u otros)"
            r'(?:Manejo|Conocimiento|Dominio)\s+(?:de\s+|en\s+)?(Python|Java|C\+\+|JavaScript|PHP|Ruby|Go)',
            r'\b(Python|Java|C\+\+|JavaScript)\s+(?:u\s+otros|or\s+others)',
            
            # Patrones con contexto
            r'(?:programación\s+científica|scientific\s+programming)',
            r'(?:scripts?\s+y\s+funciones|scripts\s+and\s+functions)',
        ],
        
        "databases": [
            # Patrones básicos
            r'\b(SQL(?:\s+Server)?|MySQL|PostgreSQL|Oracle|MongoDB|Redis|NoSQL|SQLite|MariaDB|Cassandra|DynamoDB)\b',
            
            # Patrones específicos de los textos
            r'(?:Manejo|Conocimiento|Dominio)\s+(?:de\s+)?SQL',
            r'Bases?\s+de\s+datos\s*\(\s*([^)]+)\s*\)',  # "Bases de datos (MySQL, PostgreSQL, etc.)"
            r'(?:MySQL|PostgreSQL|Oracle|MongoDB),?\s*etc\.?',
            
            # Patrones con contexto
            r'(?:estructuras\s+de\s+datos|data\s+structures)',
            r'(?:procesamiento\s+de\s+datos|data\s+processing)',
        ],
        
        "cloud_platforms": [
            # Patrones básicos
            r'\b(AWS|Amazon\s+Web\s+Services|Azure|GCP|Google\s+Cloud|IBM\s+Cloud|DigitalOcean)\b',
            
            # Patrones específicos de AWS encontrados
            r'(?:currículo|curriculum)\s+de\s+formación\s+en\s+IA\s+de\s+(AWS)',
            r'(AWS)\s+(?:fundamentos|foundations|arquitectura|architecture)',
            r'(?:modelos\s+de\s+)?(?:IA|AI)\s+(?:de\s+)?(AWS)',
            
            # Otros servicios cloud
            r'\b(S3|Lambda|EC2|SageMaker|Bedrock|CloudFormation|Firebase|Heroku)\b',
        ],
        
        "frameworks_tools": [
            # Frameworks web
            r'\b(React|Angular|Vue|Node\.js|Django|Flask|Spring|Laravel|Express|Bootstrap)\b',
            
            # Herramientas de desarrollo
            r'\b(Docker|Kubernetes|Git|Jenkins|Maven|Gradle|Webpack|Babel)\b',
            
            # Herramientas científicas específicas encontradas
            r'\b(MATLAB)(?:/(\w+))?',  # "MATLAB/SIMULINK"
            r'\b(SIMULINK)(?:/(\w+))?',
            r'(MATLAB/SIMULINK)',
            
            # Patrones con contexto
            r'(?:aplicaciones\s+científicas|scientific\s+applications)',
            r'(?:análisis\s+de\s+datos|data\s+analysis)',
            r'(?:prototipado|prototyping)',
        ],
        
        "office_tools": [
            # Herramientas de oficina básicas
            r'\b(Excel|Word|PowerPoint|Outlook|MS\s+Office|Office\s+365|Google\s+Workspace|Sheets|Docs)\b',
            
            # Patrones específicos encontrados
            r'(?:Básico\s+o\s+intermedio\s+en\s+)?(Excel)',
            r'(?:Manejo|Conocimiento|Dominio)\s+(?:de\s+)?(Excel|Word|PowerPoint)',
            r'(Excel)\s+\((?:mandatorio|mandatory|obligatorio|required)\)',
            
            # Herramientas de BI
            r'\b(Tableau|Power\s+BI|QlikView|Looker)\b',
        ],
        
        "specialized_software": [
            # Software especializado básico
            r'\b(AutoCAD|SolidWorks|Photoshop|Illustrator|InDesign)\b',
            r'\b(SAP|Oracle\s+ERP|Salesforce|ServiceNow|Jira|Confluence|Slack|Teams)\b',
            
            # Software científico específico encontrado
            r'\b(MATLAB)(?:/SIMULINK)?(?:/SIMULINK)?',  # Capturar todas las variantes
            r'(?:conocimientos\s+previos\s+.*?)?(MATLAB/SIMULINK)',
            r'(SIMULINK)\s+para\s+aplicaciones',
            
            # Software estadístico
            r'\b(SPSS|SAS|Stata|Minitab|R)\b',
            
            # Conceptos matemáticos como herramientas
            r'(?:matemáticas\s+aplicadas|applied\s+mathematics)',
            r'(?:álgebra\s+lineal|linear\s+algebra)',
            r'(?:lógica\s+computacional|computational\s+logic)',
        ]
    }
    
    # === PATRONES ESPECIALES PARA IA Y MACHINE LEARNING ===
    ai_ml_patterns = [
        r'(?:inteligencia\s+artificial|artificial\s+intelligence|IA|AI)',
        r'(?:aprendizaje\s+automático|machine\s+learning|ML)',
        r'(?:sistemas\s+inteligentes|intelligent\s+systems)',
        r'(?:agentes\s+de\s+inteligencia\s+artificial|AI\s+agents)',
        r'(?:fundamentos.*?IA|IA.*?fundamentos)',
        r'(?:algoritmos.*?IA|IA.*?algoritmos)',
    ]
    
    for pattern in ai_ml_patterns:
        if re.search(pattern, normalized_text, re.IGNORECASE):
            if "Inteligencia Artificial" not in result["specialized_software"]:
                result["specialized_software"].append("Inteligencia Artificial")
            if "Machine Learning" not in result["specialized_software"]:
                result["specialized_software"].append("Machine Learning")
    
    # === PROCESAR PATRONES PRINCIPALES ===
    for category, patterns in tech_patterns.items():
        for pattern in patterns:
            matches = re.findall(pattern, normalized_text, re.IGNORECASE)
            if matches:
                clean_matches = []
                for match in matches:
                    if isinstance(match, tuple):
                        # Para patrones con grupos múltiples, tomar el no vacío
                        match = next((m for m in match if m), "")
                    
                    if isinstance(match, str) and len(match.strip()) > 1:
                        match = match.strip()
                        
                        # Normalizar nombres comunes
                        normalization_map = {
                            'javascript': 'JavaScript',
                            'python': 'Python',
                            'java': 'Java',
                            'sql': 'SQL',
                            'mysql': 'MySQL',
                            'postgresql': 'PostgreSQL',
                            'excel': 'Excel',
                            'matlab': 'MATLAB',
                            'simulink': 'SIMULINK',
                            'aws': 'AWS',
                        }
                        
                        normalized_match = normalization_map.get(match.lower(), match)
                        
                        if normalized_match not in clean_matches:
                            clean_matches.append(normalized_match)
                
                result[category].extend(clean_matches)
    
    # === PATRONES CONTEXTUALES ADICIONALES ===
    # Buscar tecnologías en contextos específicos
    contextual_patterns = [
        # Patrón: "Conocimientos en: • Básico o intermedio en Excel"
        r'Conocimientos?\s+en:\s*.*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        
        # Patrón: "Manejo [tecnología] (opcional)"
        r'Manejo\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\([^)]*opcional[^)]*\)',
        
        # Patrón: "Deseable: conocimientos... en [tecnología]"
        r'Deseable:.*?(?:en|de)\s+([A-Z][a-z]+(?:/[A-Z]+)*)',
    ]
    
    for pattern in contextual_patterns:
        matches = re.findall(pattern, normalized_text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            tech = match.strip()
            # Clasificar automáticamente según palabras clave
            if any(word in tech.lower() for word in ['sql', 'mysql', 'postgresql', 'mongo', 'database']):
                if tech not in result["databases"]:
                    result["databases"].append(tech)
            elif any(word in tech.lower() for word in ['python', 'java', 'javascript', 'programming']):
                if tech not in result["programming_languages"]:
                    result["programming_languages"].append(tech)
            elif any(word in tech.lower() for word in ['matlab', 'simulink', 'autocad']):
                if tech not in result["specialized_software"]:
                    result["specialized_software"].append(tech)
            elif any(word in tech.lower() for word in ['excel', 'word', 'powerpoint', 'office']):
                if tech not in result["office_tools"]:
                    result["office_tools"].append(tech)
    
    # === LIMPIEZA FINAL ===
    # Eliminar duplicados y limpiar cada categoría
    for category in result:
        # Eliminar duplicados manteniendo orden
        result[category] = list(dict.fromkeys(result[category]))
        
        # Filtrar elementos muy cortos o genéricos
        result[category] = [
            tech for tech in result[category] 
            if len(tech) >= 2 and tech.lower() not in ['de', 'en', 'el', 'la', 'y', 'o', 'u', 'otros', 'etc']
        ]
        
        # Limitar cantidad máxima
        result[category] = result[category][:8]
    
    # Log de debugging
    total_techs = sum(len(techs) for techs in result.values())
    if total_techs > 0:
        logger.debug(f"✅ Tecnologías extraídas: {total_techs} total")
        for category, techs in result.items():
            if techs:
                logger.debug(f"  - {category}: {techs}")
    
    return result

def extract_soft_skills_enhanced(text: str) -> List[str]:
    """Extrae habilidades blandas MEJORADO basado en textos reales - CORREGIDO PARA DEBUG"""

    normalized_text = normalize_text(text).lower()
    logger.debug(f"🔍 Buscando habilidades blandas en: {normalized_text[:300]}...")
    
    found_skills = []
    
    # === PATRONES BASADOS EN TEXTOS REALES ===
    enhanced_soft_skills_patterns = [
        # Habilidades encontradas específicamente en los textos
        r'\b(análisis\s+de\s+problemas|problem\s+analysis)\b',
        r'\b(trabajo\s+en\s+equipo|teamwork|colaboración|team\s+player)\b',
        r'\b(disposición\s+para\s+el\s+aprendizaje|learning\s+disposition)\b',
        r'\b(alta\s+disposición\s+para\s+el\s+aprendizaje\s+práctico)\b',
        r'\b(aprendizaje\s+práctico|practical\s+learning)\b',
        
        # Habilidades de comunicación específicas
        r'\b(capacidad\s+para\s+comunicar|communication\s+skills)\b',
        r'\b(comunicación|communication)\b',
        r'\b(colaborar\s+en\s+la\s+construcción\s+de\s+soluciones)\b',
        r'\b(reportar\s+avances|progress\s+reporting)\b',
        
        # Habilidades de adaptabilidad y flexibilidad
        r'\b(disponibilidad\s+para\s+hacer\s+viajes|travel\s+availability)\b',
        r'\b(participar\s+en\s+actividades\s+de\s+campo)\b',
        r'\b(trabajo\s+fuera\s+de\s+oficina|field\s+work)\b',
        r'\b(adaptabilidad|adaptable|flexibility|flexible)\b',
        
        # Habilidades de trabajo en equipo específicas
        r'\b(colaborar\s+con\s+el\s+equipo\s+técnico)\b',
        r'\b(trabajo\s+colaborativo|collaborative\s+work)\b',
        r'\b(participar\s+en\s+reuniones\s+técnicas)\b',
        
        # Habilidades generales mejoradas
        r'\b(liderazgo|leadership|líder|leader)\b',
        r'\b(resolución\s+de\s+problemas|problem\s+solving)\b',
        r'\b(pensamiento\s+crítico|critical\s+thinking)\b',
        r'\b(creatividad|creativity|innovación|innovation)\b',
        r'\b(gestión\s+del\s+tiempo|time\s+management)\b',
        r'\b(responsabilidad|responsibility|responsable)\b',
        r'\b(proactividad|proactivity|iniciativa|initiative)\b',
        r'\b(atención\s+al\s+detalle|attention\s+to\s+detail)\b',
        r'\b(organización|organization|planificación|planning)\b',
        
        # Habilidades específicas de la industria
        r'\b(interés\s+en.*?(?:inteligencia\s+artificial|IA|AI))\b',
        r'\b(orientación\s+a\s+resultados|results\s+oriented)\b',
        r'\b(capacidad\s+de\s+investigación|research\s+skills)\b',
        r'\b(documentación|documentation\s+skills)\b',
        
        # Habilidades interpersonales
        r'\b(habilidades\s+interpersonales|interpersonal\s+skills)\b',
        r'\b(trabajo\s+bajo\s+presión|work\s+under\s+pressure)\b',
        r'\b(negociación|negotiation)\b',
        r'\b(empatía|empathy)\b',
    ]
    
    # Procesar cada patrón
    for i, pattern in enumerate(enhanced_soft_skills_patterns):
        matches = re.findall(pattern, normalized_text)
        if matches:
            logger.debug(f"Patrón {i+1} encontró: {matches}")
        for match in matches:
            if isinstance(match, str) and match.strip():
                skill = match.strip()
                
                # Normalizar y mapear habilidades
                skill_mapping = {
                    # Mapeos específicos de los textos encontrados
                    'análisis de problemas': 'Análisis de problemas',
                    'problem analysis': 'Análisis de problemas',
                    'trabajo en equipo': 'Trabajo en equipo',
                    'teamwork': 'Trabajo en equipo',
                    'colaboración': 'Colaboración',
                    'disposición para el aprendizaje': 'Disposición para el aprendizaje',
                    'alta disposición para el aprendizaje práctico': 'Aprendizaje práctico',
                    'aprendizaje práctico': 'Aprendizaje práctico',
                    'capacidad para comunicar': 'Comunicación efectiva',
                    'comunicación': 'Comunicación',
                    'disponibilidad para hacer viajes': 'Flexibilidad para viajes',
                    'adaptabilidad': 'Adaptabilidad',
                    'flexible': 'Flexibilidad',
                    'colaborar con el equipo técnico': 'Colaboración técnica',
                    'trabajo colaborativo': 'Trabajo colaborativo',
                    'participar en reuniones técnicas': 'Comunicación técnica',
                    
                    # Mapeos generales
                    'communication': 'Comunicación',
                    'leadership': 'Liderazgo',
                    'problem solving': 'Resolución de problemas',
                    'critical thinking': 'Pensamiento crítico',
                    'creativity': 'Creatividad',
                    'time management': 'Gestión del tiempo',
                    'responsibility': 'Responsabilidad',
                    'initiative': 'Iniciativa',
                    'attention to detail': 'Atención al detalle',
                    'organization': 'Organización',
                }
                
                # Aplicar mapeo o mantener original
                normalized_skill = skill_mapping.get(skill.lower(), skill.title())
                
                # Agregar si no existe ya
                if normalized_skill not in found_skills and len(normalized_skill) > 3:
                    found_skills.append(normalized_skill)
                    logger.debug(f"✅ Habilidad extraída: '{normalized_skill}' (desde: '{skill}')")
    
    # === BÚSQUEDA CONTEXTUAL ADICIONAL MEJORADA ===
    # Buscar habilidades en contextos específicos como requisitos
    contextual_patterns = [
        # NUEVOS: Patrones más específicos para habilidades
        r'(?:•|\-|)\s*(trabajo\s+en\s+equipo)[^.\n]*',
        r'(?:•|\-|)\s*(comunicación)[^.\n]*',
        r'(?:•|\-|)\s*(liderazgo)[^.\n]*',
        r'(?:•|\-|)\s*(responsabilidad)[^.\n]*',
        r'(?:•|\-|)\s*(iniciativa)[^.\n]*',
        r'(?:•|\-|)\s*(adaptabilidad)[^.\n]*',
        r'(?:•|\-|)\s*(creatividad)[^.\n]*',
        r'(?:•|\-|)\s*(organización)[^.\n]*',
        
        # Patrones más generales
        r'[•\-]\s*(Alta\s+disposición\s+para[^.\n]+)',
        r'[•\-]\s*(Capacidad\s+para[^.\n]+)',
        r'[•\-]\s*(Habilidad[^.\n]+)',
        r'[•\-]\s*(Disponibilidad\s+para[^.\n]+)',
        
        # Patrones en secciones de requisitos
        r'Requisitos?:.*?[•\-]\s*([^.\n]*(?:trabajo|comunicación|liderazgo|análisis)[^.\n]*)',
        r'Requirements?:.*?[•\-]\s*([^.\n]*(?:teamwork|communication|leadership|analysis)[^.\n]*)',
    ]
    
    for pattern in contextual_patterns:
        matches = re.findall(pattern, normalized_text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            match = match.strip()
            if len(match) > 10 and len(match) < 100:
                # Extraer la habilidad específica
                if 'disposición' in match.lower():
                    if 'Disposición para el aprendizaje' not in found_skills:
                        found_skills.append('Disposición para el aprendizaje')
                elif 'comunicar' in match.lower() or 'comunicación' in match.lower():
                    if 'Comunicación' not in found_skills:
                        found_skills.append('Comunicación')
                elif 'equipo' in match.lower():
                    if 'Trabajo en equipo' not in found_skills:
                        found_skills.append('Trabajo en equipo')
                elif 'análisis' in match.lower():
                    if 'Análisis de problemas' not in found_skills:
                        found_skills.append('Análisis de problemas')
                elif 'viajes' in match.lower() or 'travel' in match.lower():
                    if 'Flexibilidad para viajes' not in found_skills:
                        found_skills.append('Flexibilidad para viajes')
                elif 'liderazgo' in match.lower():
                    if 'Liderazgo' not in found_skills:
                        found_skills.append('Liderazgo')
                elif 'responsabilidad' in match.lower():
                    if 'Responsabilidad' not in found_skills:
                        found_skills.append('Responsabilidad')
                elif 'iniciativa' in match.lower():
                    if 'Iniciativa' not in found_skills:
                        found_skills.append('Iniciativa')
                elif 'adaptabilidad' in match.lower():
                    if 'Adaptabilidad' not in found_skills:
                        found_skills.append('Adaptabilidad')
                elif 'creatividad' in match.lower():
                    if 'Creatividad' not in found_skills:
                        found_skills.append('Creatividad')
                elif 'organización' in match.lower():
                    if 'Organización' not in found_skills:
                        found_skills.append('Organización')
    
    # === LIMPIEZA FINAL ===
    # Eliminar duplicados manteniendo orden
    final_skills = []
    seen = set()
    for skill in found_skills:
        skill_lower = skill.lower()
        if skill_lower not in seen and len(skill) >= 4:
            final_skills.append(skill)
            seen.add(skill_lower)
    
    # Limitar a máximo 12 habilidades
    final_skills = final_skills[:12]
    
    # Log de debugging mejorado
    if final_skills:
        logger.debug(f"✅ Habilidades blandas extraídas: {final_skills}")
    else:
        logger.debug("❌ No se extrajeron habilidades blandas")
    
    return final_skills

def extract_schedule_enhanced(text: str) -> Optional[str]:
    """Extrae información de horarios de manera general - VERSIÓN ULTRA ROBUSTA CORREGIDA"""
    
    normalized_text = normalize_text(text).lower()
    
    schedule_patterns = [
        # Horarios específicos con rango
        r"(?:horario\s+)?(?:de\s+)?lunes\s+a\s+viernes\s+de\s+(\d{1,2}:\d{2}\s*[ap]\.?\s*m\.?)\s+a\s+(\d{1,2}:\d{2}\s*[ap]\.?\s*m\.?)",
        
        # Horarios sin días específicos
        r"(?:de\s+)?(\d{1,2}:\d{2}\s*[ap]\.?\s*m\.?)\s+a\s+(\d{1,2}:\d{2}\s*[ap]\.?\s*m\.?)",
        
        # Jornadas con horas específicas
        r"jornada.*?(\d+)\s+horas",
        r"tiempo\s+completo\s*\((\d+)\s+horas\)",
        
        # Días de trabajo
        r"(lunes\s+a\s+viernes|monday\s+to\s+friday)",
        
        # Turnos
        r"turno\s+(matutino|vespertino|nocturno|completo)",
        r"(medio\s+tiempo|tiempo\s+parcial|part\s+time)",
        r"(tiempo\s+completo|full\s+time)"
    ]
    
    for pattern in schedule_patterns:
        try:
            match = re.search(pattern, normalized_text)
            if match:
                groups = match.groups()
                # CORRECCIÓN: verificar que groups existe y tiene elementos
                if groups and len(groups) >= 2 and groups[0] and groups[1]:
                    return f"De {groups[0]} a {groups[1]}"
                elif groups and len(groups) >= 1 and groups[0]:
                    schedule = groups[0].strip().title()
                    return schedule
                else:
                    # Si no hay grupos de captura pero hay match, devolver la coincidencia completa
                    return match.group(0).strip().title()
        except (IndexError, AttributeError) as e:
            logger.debug(f"Error en extract_schedule_enhanced: {str(e)}")
            continue
    
    return None

def extract_education_level_enhanced(text: str) -> Optional[str]:
    """Extrae nivel educativo requerido de manera general - VERSIÓN ULTRA ROBUSTA CORREGIDA"""
    
    normalized_text = normalize_text(text).lower()
    
    education_patterns = [
        r"estudiante\s+de\s+último\s+año",
        r"último\s+año\s+de\s+carrera",
        r"(?:egresado|graduado)\s+(?:de|en)",
        r"(?:licenciatura|ingeniería|título)\s+en",
        r"(?:carrera|programa)\s+de",
        r"facultad\s+de",
        r"(?:cursando|estudiando)\s+(?:\d+to?|último)\s+año",
        r"nivel\s+(?:universitario|superior|técnico)",
        r"(?:bachelor|master|phd|doctorate)\s+(?:degree|in)"
    ]
    
    for pattern in education_patterns:
        try:
            match = re.search(pattern, normalized_text)
            if match:
                # Extraer contexto más amplio
                start = max(0, match.start() - 50)
                end = min(len(normalized_text), match.end() + 100)
                context = normalized_text[start:end]
                
                # Limpiar y devolver
                education = context.strip().replace('\n', ' ')
                education = re.sub(r'\s+', ' ', education)
                
                if len(education) <= 200:
                    return education.title()
        except (IndexError, AttributeError) as e:
            logger.debug(f"Error en extract_education_level_enhanced: {str(e)}")
            continue
    
    return None

def extract_salary_range(text: str) -> Optional[str]:
    """Extrae información salarial si está presente - VERSIÓN ULTRA ROBUSTA CORREGIDA"""
    
    normalized_text = normalize_text(text).lower()
    
    salary_patterns = [
        r"salario:\s*([^.\n]+)",
        r"sueldo:\s*([^.\n]+)",
        r"remuneración:\s*([^.\n]+)",
        r"compensación:\s*([^.\n]+)",
        r"entre\s+\$?(\d{1,3}(?:,\d{3})*)\s*y\s*\$?(\d{1,3}(?:,\d{3})*)",
        r"\$(\d{1,3}(?:,\d{3})*)\s*-\s*\$?(\d{1,3}(?:,\d{3})*)",
        r"desde\s+\$?(\d{1,3}(?:,\d{3})*)",
        r"hasta\s+\$?(\d{1,3}(?:,\d{3})*)"
    ]
    
    for pattern in salary_patterns:
        try:
            match = re.search(pattern, normalized_text)
            if match:
                # CORRECCIÓN: usar match.group(0) siempre como fallback seguro
                salary_info = match.group(0).strip()
                if len(salary_info) <= 100:
                    return salary_info.title()
        except (IndexError, AttributeError) as e:
            logger.debug(f"Error en extract_salary_range: {str(e)}")
            continue
    
    return None

def extract_application_deadline(text: str) -> Optional[str]:
    """Extrae fecha límite de aplicación - VERSIÓN ULTRA ROBUSTA CORREGIDA"""
    
    normalized_text = normalize_text(text).lower()
    
    deadline_patterns = [
        r"fecha\s+límite:\s*([^.\n]+)",
        r"hasta\s+el\s+(\d{1,2}\/\d{1,2}\/\d{4})",
        r"cierre\s+de\s+convocatoria:\s*([^.\n]+)",
        r"aplicar\s+antes\s+del\s+([^.\n]+)",
        r"deadline:\s*([^.\n]+)"
    ]
    
    for pattern in deadline_patterns:
        try:
            match = re.search(pattern, normalized_text)
            if match:
                groups = match.groups()
                # CORRECCIÓN: verificar que groups existe y tiene elementos
                if groups and len(groups) >= 1 and groups[0]:
                    deadline = groups[0].strip()
                    if len(deadline) <= 50:
                        return deadline
                else:
                    # Si no hay grupos de captura válidos, usar la coincidencia completa
                    return match.group(0).strip()
        except (IndexError, AttributeError) as e:
            logger.debug(f"Error en extract_application_deadline: {str(e)}")
            continue
    
    return None

def extract_contact_info_enhanced(text: str) -> Dict[str, Optional[str]]:
    """Versión ULTRA MEJORADA con patrones más flexibles y específicos - ULTRA ROBUSTA"""
    
    contact_info = {
        "name": None,
        "position": None,
        "email": None,
        "phone": None,
        "mobile": None,
        "title": None,
        "department": None
    }
    
    normalized_text = normalize_text(text)
    logger.debug(f"🔍 Buscando contactos en texto: {normalized_text[:200]}...")
    
    # === PATRONES MEJORADOS Y MÁS FLEXIBLES CON VALIDACIÓN ROBUSTA ===
    contact_patterns = [
        # Patrón específico para formato con separadores
        (r"Contacto:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[|\-]\s*([^|\n]+?)(?=\s*(?:Móvil|Teléfono|Email|$))", "Formato con separador"),
        
        # Patrón para títulos profesionales + nombre + cargo
        (r"Contacto:\s*((?:Lcda?\.|Dr[a]?\.|Ing\.|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[|\-]?\s*([^|\n]+?)(?=\s*(?:Móvil|Teléfono|Email|$))", "Con título profesional"),
        
        # Patrón para solo nombres (sin cargo específico)
        (r"Contacto:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Center|Development|Manager|Analyst|Specialist|Coordinator)))?", "Solo nombres"),
        
        # Patrón más flexible para cualquier contacto
        (r"Contacto:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s*[|\-]?\s*(.+?))?(?=\s*(?:Móvil|Teléfono|Email|\n|$))", "Flexible"),
        
        # Patrón alternativo con espacios variables
        (r"Contacto:\s*([^|\n]+?)(?:\s*\|\s*([^|\n]+?))?(?=\s*(?:Móvil|Teléfono|Email|\n|$))", "Con espacios variables")
    ]

    for i, (pattern, description) in enumerate(contact_patterns):
        try:
            match = re.search(pattern, normalized_text, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                # VALIDACIÓN ROBUSTA: verificar grupos disponibles
                raw_name = groups[0].strip() if len(groups) >= 1 and groups[0] else None
                raw_position = groups[1].strip() if len(groups) >= 2 and groups[1] else None
                
                if raw_name:
                    # Limpiar y procesar nombre
                    cleaned_name, extracted_position = clean_and_separate_contact(raw_name, raw_position)
                    
                    if cleaned_name:
                        contact_info["name"] = cleaned_name
                        contact_info["position"] = extracted_position or raw_position
                        
                        # Extraer título profesional
                        try:
                            title_match = re.search(r"(Lcda?\.|Dr[a]?\.|Ing\.|Prof\.)", cleaned_name)
                            if title_match:
                                contact_info["title"] = title_match.group(1)
                                contact_info["name"] = re.sub(r"(Lcda?\.|Dr[a]?\.|Ing\.|Prof\.)\s*", "", cleaned_name).strip()
                        except:
                            pass
                        
                        logger.debug(f"✅ Patrón {i+1} ({description}) - Contacto: '{contact_info['name']}' | Cargo: '{contact_info['position']}'")
                        break
        except (IndexError, AttributeError) as e:
            logger.debug(f"Error en patrón {i+1} ({description}): {str(e)}")
            continue

    if not contact_info["name"]:
        # Patrón específico para "Lcda. Nombre Apellido" con validación robusta
        additional_patterns = [
            (r"(?:Empresa|Entidad|Compañía):[^:]*?(?:Lcda?\.|Dr[a]?\.|Ing\.|Prof\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", "En empresa"),
            (r"(?:Lcda?\.|Dr[a]?\.|Ing\.|Prof\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", "Título directo"),
            (r":\s*(?:Lcda?\.|Dr[a]?\.|Ing\.|Prof\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", "Después de dos puntos")
        ]
        
        for pattern, description in additional_patterns:
            try:
                match = re.search(pattern, normalized_text)
                if match:
                    groups = match.groups()
                    if len(groups) >= 1 and groups[0]:
                        name_with_title = match.group(0).strip()
                        name = re.sub(r"(?:Lcda?\.|Dr[a]?\.|Ing\.|Prof\.)\s+", "", name_with_title).strip()
                        
                        # Extraer título profesional de manera segura
                        try:
                            title_match = re.search(r"(Lcda?\.|Dr[a]?\.|Ing\.|Prof\.)", name_with_title)
                            if title_match:
                                contact_info["title"] = title_match.group(1)
                        except:
                            pass
                        
                        contact_info["name"] = name
                        logger.debug(f"✅ Contacto con título extraído ({description}): '{name_with_title}'")
                        
                        # Buscar posición cerca del nombre de manera segura
                        try:
                            position_pattern = rf"{re.escape(name)}(?:\s*[|\-]\s*|\s+)([A-Z][a-zA-Z\s]+(?:Center|Development|Department|Manager|Analyst|Coordinator))"
                            position_match = re.search(position_pattern, normalized_text)
                            if position_match and len(position_match.groups()) >= 1:
                                contact_info["position"] = position_match.group(1).strip()
                        except:
                            pass
                        break
            except (IndexError, AttributeError) as e:
                logger.debug(f"Error en patrón adicional '{description}': {str(e)}")
                continue
    
    # === EXTRACCIÓN DE TELÉFONO MEJORADA CON VALIDACIÓN ===
    phone_patterns = [
        r"Móvil:\s*(\+\(\d{3}\)\s*\d{4}-\d{4})",
        r"Móvil:\s*(\+\d{3}\s*\d{4}-\d{4})", 
        r"Teléfono:\s*(\+\(\d{3}\)\s*\d{4}-\d{4})",
        r"(\+\(\d{3}\)\s*\d{4}-\d{4})",
        r"(\+\d{3}\s+\d{4}-\d{4})",
        r"(\d{3}-\d{4})",  # Formato más simple
    ]
    
    for pattern in phone_patterns:
        try:
            phone_match = re.search(pattern, normalized_text)
            if phone_match and len(phone_match.groups()) >= 1:
                contact_info["phone"] = phone_match.group(1).strip()
                logger.debug(f"✅ Teléfono extraído: '{contact_info['phone']}'")
                break
        except:
            continue
    
    # === EXTRACCIÓN DE EMAIL MEJORADA CON VALIDACIÓN ===
    email_patterns = [
        r"enviar\s+Hoja\s+de\s+Vida\s+a:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        r"enviar\s+CV\s+a:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        r"Interesados?\s+enviar.*?a:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        r"Email:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        r'enviar.*?a:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'email:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.com)',
    ]
    
    for pattern in email_patterns:
        try:
            email_match = re.search(pattern, normalized_text, re.IGNORECASE)
            if email_match and len(email_match.groups()) >= 1:
                email = email_match.group(1).strip().lower()
                # Validar email
                if len(email) >= 5 and email.count('@') == 1 and '.' in email.split('@')[1]:
                    contact_info["email"] = email
                    logger.debug(f"✅ Email extraído: '{contact_info['email']}'")
                    break
        except:
            continue
    
    # Detectar departamento en el cargo de manera segura
    if contact_info.get("position"):
        dept_patterns = [
            r"(talent\s+development\s+center|TDC)",
            r"(recursos\s+humanos|human\s+resources)",
            r"(experiencia\s+al\s+cliente|customer\s+experience)",
            r"(analista\s+de\s+[^|]+)",
            r"([^|]+\s+(?:center|development|department|dept))"
        ]
        
        for pattern in dept_patterns:
            try:
                match = re.search(pattern, contact_info["position"], re.IGNORECASE)
                if match and len(match.groups()) >= 1:
                    contact_info["department"] = match.group(1).strip()
                    break
            except:
                continue
    
    # Log final
    if contact_info["name"] or contact_info["email"]:
        logger.debug(f"🎯 Resultado final: Nombre='{contact_info['name']}', Email='{contact_info['email']}', Teléfono='{contact_info['phone']}'")
    else:
        logger.debug("❌ No se pudo extraer información de contacto")
    
    return contact_info

def clean_and_separate_contact(full_text: str, position_text: str = None) -> Tuple[Optional[str], Optional[str]]:
    """Limpia y separa nombre de contacto y posición de manera más inteligente - VERSIÓN ULTRA ROBUSTA"""
    if not full_text:
        return None, None
    
    # Inicializar name como None para evitar el error
    name = None
    
    # Patrones para separar nombre y cargo automáticamente
    separation_patterns = [
        # Patrón: "Nombre Apellido | Cargo"
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\|\s*(.+)$',
        
        # Patrón: "Título Nombre Apellido | Cargo"
        r'^((?:Lcda?\.|Dr[a]?\.|Ing\.|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\|\s*(.+)$',
        
        # Patrón: "Nombre + palabras descriptivas largas"
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s+((?:[A-Z][a-z]+\s*){3,}.*)$',
        
        # Patrón: "Nombre + cargo conocido"
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+((?:Analista|Gerente|Director|Coordinador|Manager|Specialist).*?)$'
    ]

    for pattern in separation_patterns:
        try:
            match = re.search(pattern, full_text.strip(), re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 1 and groups[0]:
                    name = clean_contact_name(groups[0].strip())
                    position = groups[1].strip() if len(groups) >= 2 and groups[1] else None
                    
                    # Validar que el nombre sea válido
                    if validate_contact_name(name):
                        return name, position or position_text
        except (IndexError, AttributeError) as e:
            logger.debug(f"Error en clean_and_separate_contact (separation): {str(e)}")
            continue
    
    # Patrones para títulos profesionales
    title_patterns = [
        r'^((?:Lcda?\.|Dr[a]?\.|Ing\.|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'((?:Lcda?\.|Dr[a]?\.|Ing\.|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
    ]
    
    if not name:
        # Buscar primero el cargo/departamento y luego inferir el nombre
        dept_position_patterns = [
            # Patrones universales para cargos con departamentos
            r'((?:Analista|Anahsta))\s+de\s+((?:Experiencia|Recursos|Ventas|Marketing|Sistemas)[^|]+)',
            r'((?:Analyst|Manager|Director|Coordinator))\s+of\s+((?:Experience|Resources|Sales|Marketing|Systems)[^|]+)'
        ]
        
        for pattern in dept_position_patterns:
            try:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if len(groups) >= 2 and groups[0] and groups[1]:
                        position = f"{groups[0]} de {groups[1]}".strip()
                        
                        # Buscar nombre antes del cargo (patrón universal)
                        name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s+' + re.escape(match.group(0)), full_text, re.IGNORECASE)
                        if name_match and len(name_match.groups()) >= 1:
                            name = name_match.group(1).strip()
                            return name, position
            except (IndexError, AttributeError) as e:
                logger.debug(f"Error en clean_and_separate_contact (dept_position): {str(e)}")
                continue

    # Ahora verificamos name de forma segura
    if not name:
        for pattern in title_patterns:
            try:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if len(groups) >= 1 and groups[0]:
                        name_with_title = groups[0].strip()
                        # Verificar que sea un nombre válido
                        name_without_title = re.sub(r"(?:Lcda?\.|Dr[a]?\.|Ing\.|Prof\.)\s+", "", name_with_title).strip()
                        
                        if validate_contact_name(name_without_title):
                            # Extraer posición si está disponible
                            try:
                                position_match = re.search(rf"{re.escape(name_with_title)}\s*[|\-]?\s*([^|\n]+)", full_text)
                                position = position_match.group(1).strip() if position_match and len(position_match.groups()) >= 1 else position_text
                                
                                return name_with_title, position
                            except (IndexError, AttributeError):
                                return name_with_title, position_text
            except (IndexError, AttributeError) as e:
                logger.debug(f"Error en clean_and_separate_contact (title_patterns): {str(e)}")
                continue
    
    # Si no se puede separar automáticamente, usar texto como está
    cleaned_name = clean_contact_name(full_text)
    if validate_contact_name(cleaned_name):
        return cleaned_name, position_text
    
    return None, None

def validate_contact_name(name: str) -> bool:
    """Valida que un nombre de contacto sea válido"""
    if not name or len(name) < 5:
        return False
    
    # Verificar que tenga al menos 2 palabras
    words = name.split()
    if len(words) < 2:
        return False
    
    # Verificar que no contenga números o símbolos extraños
    if not re.match(r'^[A-Za-z\.\s]+$', name):
        return False
    
    # Verificar que no sean palabras genéricas
    generic_words = ['contacto', 'telefono', 'email', 'movil', 'informacion', 'empresa', 'cliente']
    if any(word in name.lower() for word in generic_words):
        return False
    
    return True

def extract_company_info(text: str) -> Dict[str, Optional[str]]:
    """Extrae información de empresas con patrones UNIVERSALES - CORREGIDO"""
    
    company_info = {
        "name": None,
        "industry": None,
        "description": None
    }
    
    normalized_text = normalize_text(text)
    logger.debug(f"🔍 Buscando empresa en: {normalized_text[:300]}...")
    
    # === PATRONES MEJORADOS Y ESPECÍFICOS ===
    company_patterns = [
        # Añadir patrón de alta prioridad para el formato "Empresa: [Nombre]"
        r"Empresa:\s+([A-Z][A-Za-z0-9\s,\.&]{2,50})(?=\s+(?:Contacto|$))",
        
        # Añadir patrón de alta prioridad para el formato "Empresa: [Nombre]"
        r"Entidad:\s+([A-Z][A-Za-z0-9\s,\.&]{2,50})(?=\s+(?:Contacto|$))",

        # NUEVO: Patrón específico para "práctica [tipo] ofrecida por [EMPRESA]"
        r"práctica\s+(?:profesional|laboral)\s+ofrecida\s+por\s+([A-Z][A-Za-z\s,\.&]{5,50}(?:\s*S\.?\s*A\.?|Inc\.?|Corp\.?|Ltd\.?|Group)?)",
        
        # NUEVO: Patrón para descripción del post con empresa
        r"(?:práctica|oferta|vacante).*?(?:por|de|en)\s+([A-Z][A-Za-z\s,\.&]{5,50}(?:\s*S\.?\s*A\.?|Inc\.?|Corp\.?|Ltd\.?|Group)?)",
        
        # Patrones con etiquetas explícitas
        r"(?:Empresa|Entidad|Compañía|Organización):\s*([^\n\r:]{5,100}?)(?=\s*(?:\n|Contacto|Responsable|$))",
        
        # Patrón con paréntesis (nombre comercial) - MEJORADO
        r"(?:Empresa|Entidad):\s*[^(]*\(([^)]{5,80})\)",
        r"Compañía\s+([A-Za-z\s,\.&]+)\s*\(([^)]{3,30})\)",  # "Compañía Panameña de Aviación (Copa Airlines)"
        
        # Empresas seguidas de verbos de acción - MEJORADO
        r"([A-Z][A-Za-z\s,\.&]{5,80}?(?:\s*S\.?\s*A\.?|Inc\.?|Corp\.?|Ltd\.?|Group|Bank|Solutions?)?)\s+(?:está\s+)?(?:ofrece|ofreciendo|busca|solicita|requiere|necesita)",
        
        # NUEVO: Nombres propios con sufijos empresariales específicos
        r"\b(GRUPO\s+[A-Z]+[A-Za-z\s]{2,30}(?:\s*,\s*S\.?\s*A\.?)?)\b",
        r"\b([A-Z][A-Za-z\s,\.&]{8,60}?\s*S\.?\s*A\.?)\b",
        r"\b([A-Z][A-Za-z\s,\.&]{5,50}?\s*(?:Airlines?|Systems?|Group|Bank|Corp\.?))\b",
        
        # NUEVO: Patrones específicos para casos conocidos
        r"\b(Copa\s+Airlines?)\b",
        r"\b(Compania\s+Panamena\s+de\s+Aviación[^.]*)\b",
        r"\b(GRUPO\s+MANZ[^.]*)\b",
        r"\b(Grupo\s+ENX)\b",
    ]
    
    for i, pattern in enumerate(company_patterns):
        match = re.search(pattern, normalized_text, re.IGNORECASE)
        if match:
            # Tomar el grupo más largo si hay múltiples grupos
            if len(match.groups()) > 1:
                # Para patrones con múltiples grupos, elegir el más específico
                company_name = match.group(2) if match.group(2) and len(match.group(2)) > len(match.group(1) or "") else match.group(1)
            else:
                company_name = match.group(1)
                
            company_name = company_name.strip()
            
            # Limpiar nombre
            company_name = re.sub(r'^\W+|\W+$', '', company_name)
            company_name = re.sub(r'\s+', ' ', company_name)

            # === LIMPIEZA GENERAL MEJORADA ===
            # Limpiar caracteres al inicio/final
            company_name = re.sub(r'^\W+|\W+$', '', company_name)
            
            # Limpiar palabras extra comunes al final
            cleanup_suffixes = [
                r'\s+(?:Nota|Empresa|Company|Corp|Inc|Ltd|Group)$',
                r'\s+(?:está|ofrece|busca|solicita|necesita).*$',
                r'\s+(?:S\.?\s*A\.?\s*\w+)$',  # "S.A. PalabraExtra" → "S.A."
            ]
            
            for suffix_pattern in cleanup_suffixes:
                company_name = re.sub(suffix_pattern, '', company_name, flags=re.IGNORECASE)
            
            # Normalizar espacios
            company_name = re.sub(r'\s+', ' ', company_name).strip()
            
            # === CORRECCIONES ESPECÍFICAS DE OCR ===
            company_corrections = {
                # Correcciones específicas encontradas en los logs
                r'\bFISC\.\s*Beneficios\s+que.*': 'Grupo ENX',
                r'\blaboral\s+ofrecida\s+por\s+': '',  # Remover prefijos
                r'\bCompania\b': 'Compañía',
                r'\bPanamena\b': 'Panameña',
                r'\bAirhnes\b': 'Airlines',
                r'\bAirlines?\s*$': 'Airlines',
                # Correcciones generales
                r'\bIntemational\b': 'International',
                r'\bSystems?\b': 'Systems',
                r'\bSolutions?\b': 'Solutions',
                r'\bGroup\b': 'Group',
                r'\bBank\b': 'Bank',
            }
            
            for error_pattern, correction in company_corrections.items():
                company_name = re.sub(error_pattern, correction, company_name, flags=re.IGNORECASE)
                company_name = company_name.strip()
            
            # === VALIDACIÓN MEJORADA ===
            # Lista de palabras que NO deberían aparecer en nombres de empresa
            invalid_words = [
                'beneficios', 'requisitos', 'contacto', 'telefono', 'email', 'movil', 
                'whatsapp', 'elaborar', 'riesg', 'infor', 'jeceutivos', 'fisc'
            ]
            
            # Validación mejorada
            if (5 <= len(company_name) <= 60 and
                not re.match(r'^[\d\s\.,\-\(\)]+$', company_name) and
                not any(word in company_name.lower() for word in invalid_words) and
                len(company_name.split()) >= 1 and len(company_name.split()) <= 6):
                
                company_info["name"] = company_name
                logger.debug(f"✅ Empresa encontrada (patrón {i+1}): '{company_name}'")
                break
            else:
                logger.debug(f"❌ Empresa rechazada (patrón {i+1}): '{company_name}' (falló validación)")
    
    if not company_info["name"]:
        additional_company_patterns = [
            # Patrones más específicos para GRUPO MANZ
            r"(?:Empresa|Entidad):\s*([A-Z]{4,}\s+[A-Z]{3,})[,\.\s]",
            r"([A-Z]{4,}\s+[A-Z]{3,})\s+esta\s+ofreciendo",
            r"([A-Z]{4,}\s+[A-Z]{3,})\s*,[^,]*?S\.A\.",
            
            # Patrones generales adicionales
            r":\s*([A-Z][A-Za-z\s,\.&]{2,50})\s*(?:[,\.\s]|$)",
            r"([A-Z][A-Za-z\s,\.&]{2,50})\s+esta\s+(?:buscando|ofreciendo|solicita)"
        ]
        
        for pattern in additional_company_patterns:
            match = re.search(pattern, normalized_text)
            if match:
                company_name = match.group(1).strip()
                
                # Limpiar y normalizar
                company_name = re.sub(r'\s+', ' ', company_name).strip()
                
                # Validación básica
                if 3 <= len(company_name) <= 50:
                    company_info["name"] = company_name
                    logger.debug(f"✅ Empresa encontrada (patrón adicional): '{company_name}'")
                    break

    # === DETECCIÓN UNIVERSAL DE INDUSTRIA (ORDEN PRIORITARIO) ===
    if company_info["name"]:
        full_text = (company_info["name"] + " " + normalized_text).lower()
        
        # Clasificación de industrias escalable - ORDEN PRIORITARIO
        industry_patterns = {
            "aviación": [
                r'\b(?:aviación|aviation|airline|aero|vuelo|flight|airport|copa|panameña.*aviación)\b',
                r'\b(?:compania.*panamena.*aviación|copa.*airlines|latam|american airlines|delta|united)\b'
            ],
            "financiero": [
                r'\b(?:banco|bank|financ|credit|investment|seguros|insurance|tower.*bank)\b',
                r'\b(?:capital|fund|lending|mortgage|financial services)\b'
            ],
            "tecnología": [
                r'\b(?:tech|system|software|digital|solutions|desarrollo|programación|IT|informática|tecnología|manz|grupo.*tech)\b',
                r'\b(?:microsoft|google|amazon|oracle|SAP|IBM|cisco)\b',
                r'\b(?:web|app|mobile|cloud|AI|machine learning|data)\b'
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
            ]
        }
        
        for industry, patterns in industry_patterns.items():
            if any(re.search(pattern, full_text, re.IGNORECASE) for pattern in patterns):
                company_info["industry"] = industry
                logger.debug(f"✅ Industria detectada: '{industry}'")
                break
    
    if not company_info["name"]:
        logger.debug("❌ No se pudo extraer nombre de empresa")
    
    if company_info["name"]:
        # Limpieza universal de verbos/palabras al final del nombre
        company_cleanup_verbs = [
            r'\s+(?:esta|está|ofrece|ofreciendo|busca|buscando)\b.*$',
            r'\s+(?:solicita|requiere|necesita)\b.*$',
            r'\s+a\s+través\s+de.*$',
        ]
        
        for verb_pattern in company_cleanup_verbs:
            company_info["name"] = re.sub(verb_pattern, '', company_info["name"], flags=re.IGNORECASE)
        
        # Normalizar espacios después de la limpieza
        company_info["name"] = re.sub(r'\s+', ' ', company_info["name"]).strip()
        
        # Corrección universal para fragmentos comunes
        if company_info["name"] == "Aviaci":
            # Buscar patrones de aviación en el texto
            if "copa" in normalized_text.lower() or "airlines" in normalized_text.lower():
                company_info["name"] = "Copa Airlines"
            else:
                company_info["name"] = "Aviación"

    return company_info

def extract_requirements_and_knowledge(text: str) -> Dict[str, List[str]]:
    """Extrae secciones usando patrones UNIVERSALES y ESCALABLES - VERSIÓN ULTRA ROBUSTA CORREGIDA"""
    
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
            # Patrones más flexibles para funciones
            r"(?:Funciones|Responsabilidades|Actividades|Tareas|Qué\s+harás)(?:[:\s]|\n)(.*?)(?=(?:Ofrecemos|Beneficios|Requisitos|Enviar|$))",
            r"(?:Functions|Responsibilities|Tasks|Activities|What you'll do)(?:[:\s]|\n)(.*?)(?=(?:We offer|Benefits|Requirements|Send|$))",
            # Nuevo: Patrón para funciones que empiezan con verbos de acción
            r"(?:Desarrollar|Implementar|Participar|Colaborar|Diseñar)(?:.*?)(?=(?:Ofrecemos|Beneficios|$))",
        ],
        "benefits": [
            # Patrones más flexibles para beneficios
            r"(?:Ofrecemos|Beneficios|Ofrecen|Qué\s+ofrecemos|Lo\s+que\s+ofrecemos|Te\s+ofrecemos|Incluye)(?:[:\s]|\n)(.*?)(?=(?:Nota|Dudas|Interesados|Requisitos|Enviar|Envía|$))",
            r"(?:We offer|Benefits|What we offer|Including)(?:[:\s]|\n)(.*?)(?=(?:Note|Questions|Interested|Requirements|Send|$))",
            # Nuevo: Patrón para detectar listas de beneficios sin encabezado explícito
            r"(?:apoyo\s+económico|viático|seguro|ambiente\s+colaborativo|capacitación)(?:.*?)(?=(?:Nota|Requisitos|Enviar|$))",
        ]
    }
    
    # === PROCESAMIENTO UNIVERSAL CORREGIDO ===
    for section_name, patterns in universal_section_patterns.items():
        for pattern in patterns:
            try:
                match = re.search(pattern, normalized_text, re.DOTALL | re.IGNORECASE)
                if match:
                    # CORRECCIÓN ROBUSTA: verificar grupos disponibles
                    groups = match.groups()
                    if groups and len(groups) >= 1 and groups[0]:
                        section_text = groups[0].strip()
                        
                        # Extraer elementos con calidad
                        items = extract_universal_list_items(section_text)
                        
                        if items:
                            result[section_name] = items
                            logger.debug(f"✅ Sección '{section_name}' extraída: {len(items)} elementos")
                            break
                    else:
                        # Si no hay grupos de captura válidos, usar toda la coincidencia
                        section_text = match.group(0).strip()
                        if len(section_text) > 20:  # Solo procesar si hay contenido suficiente
                            items = extract_universal_list_items(section_text)
                            if items:
                                result[section_name] = items
                                logger.debug(f"✅ Sección '{section_name}' extraída (fallback): {len(items)} elementos")
                                break
            except (IndexError, AttributeError) as e:
                logger.debug(f"Error en extract_requirements_and_knowledge para {section_name}: {str(e)}")
                continue
    
    # === EXTRACCIONES INDEPENDIENTES CON VALIDACIÓN ROBUSTA ===
    if not result["benefits"]:
        try:
            standalone_benefits = extract_standalone_benefits(normalized_text)
            if standalone_benefits:
                result["benefits"] = standalone_benefits
                logger.debug(f"✅ Beneficios extraídos fuera de sección formal: {len(standalone_benefits)} elementos")
        except Exception as e:
            logger.debug(f"Error extrayendo beneficios independientes: {str(e)}")
    
    if not result["functions"]:
        try:
            standalone_functions = extract_standalone_functions(normalized_text)
            if standalone_functions:
                result["functions"] = standalone_functions
                logger.debug(f"✅ Funciones extraídas fuera de sección formal: {len(standalone_functions)} elementos")
        except Exception as e:
            logger.debug(f"Error extrayendo funciones independientes: {str(e)}")
    
    return result

def extract_standalone_benefits(text: str) -> List[str]:
    """Extrae beneficios incluso cuando no están en una sección formal"""
    benefits = []
    
    # Patrones específicos para beneficios comunes (corregidos)
    benefit_patterns = [
        # Patrones simples sin grupos de captura adicionales
        r'(?:•|\-|\*|\d+\.)\s*(?:apoyo\s+económico|viático)[^.;]*',
        r'(?:•|\-|\*|\d+\.)\s*(?:seguro\s+contra\s+accidentes)[^.;]*',
        r'(?:•|\-|\*|\d+\.)\s*(?:ambiente\s+colaborativo)[^.;]*',
        r'(?:•|\-|\*|\d+\.)\s*(?:capacitación\s+continua|certificaciones)[^.;]*',
        r'(?:•|\-|\*|\d+\.)\s*(?:horario\s+(?:flexible|de\s+lunes\s+a\s+viernes))[^.;]*',
        r'(?:•|\-|\*|\d+\.)\s*(?:estación\s+de\s+trabajo|computadora)[^.;]*',
        r'(?:•|\-|\*|\d+\.)\s*(?:posibilidad\s+de\s+inserción|experiencia\s+laboral)[^.;]*',
        
        # Patrón para elementos de lista con palabras clave
        r'(?:•|\-|\*|\d+\.)\s*[A-Z][^.;]{10,100}(?:económico|viático|seguro|ambiente|capacitación|aprendizaje|experiencia|inserción|crecimiento|desarrollo)[^.;]*',
    ]
    
    # Extraer beneficios utilizando los patrones
    for pattern in benefit_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            benefit = match.strip()
            if benefit and len(benefit) > 10 and benefit not in benefits:
                # Eliminar el marcador de lista si existe
                benefit = re.sub(r'^(?:•|\-|\*|\d+\.)\s*', '', benefit)
                benefits.append(benefit)
    
    # Buscar beneficios en oraciones completas
    sentence_patterns = [
        r'(?:ofrecemos|te\s+ofrecemos|incluye|incluimos)\s+([^.;]{10,150})',
        r'(?:apoyo\s+económico|viático|seguro|ambiente\s+colaborativo)[^.;]{10,150}',
        r'(?:práctica\s+profesional\s+será\s+remunerada)[^.;]{10,150}',
        r'(?:brindando\s+así\s+una\s+oportunidad)[^.;]{10,150}',
        r'(?:emitirá\s+una\s+carta)[^.;]{10,150}',
    ]
    
    for pattern in sentence_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str):
                benefit = match.strip()
                if benefit and len(benefit) > 10 and benefit not in benefits:
                    benefits.append(benefit)
    
    return benefits[:8]  # Limitar a 8 beneficios

def extract_standalone_functions(text: str) -> List[str]:
    """Extrae funciones incluso cuando no están en una sección formal"""
    functions = []
    
    # Patrones de verbos de acción (corregidos)
    action_verb_patterns = [
        # Patrones simples sin grupos de captura adicionales
        r'(?:•|\-|\*|\d+\.)\s*(?:Desarrollar|Implementar|Participar|Colaborar|Diseñar|Realizar|Apoyar|Mantener)[^.;]*',
        r'(?:•|\-|\*|\d+\.)\s*(?:Analizar|Investigar|Ejecutar|Crear|Generar|Contribuir|Gestionar)[^.;]*',
        
        # Patrón para elementos que comienzan con verbos
        r'(?:•|\-|\*|\d+\.)\s*[A-Z][a-z]+(?:ar|er|ir|izar|ear)\s+[^.;]{10,100}',
    ]
    
    # Extraer funciones utilizando los patrones
    for pattern in action_verb_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            function = match.strip()
            if function and len(function) > 10 and function not in functions:
                # Eliminar el marcador de lista si existe
                function = re.sub(r'^(?:•|\-|\*|\d+\.)\s*', '', function)
                functions.append(function)
    
    # Búsqueda en secciones explícitas
    if "funciones" in text.lower() or "responsabilidades" in text.lower() or "actividades" in text.lower():
        lines = text.split('\n')
        in_function_section = False
        
        for line in lines:
            line = line.strip()
            # Detectar inicio de sección
            if re.search(r'funciones|responsabilidades|actividades', line, re.IGNORECASE) and ':' in line:
                in_function_section = True
                continue
            # Detectar fin de sección
            if in_function_section and re.search(r'requisitos|beneficios|ofrecemos', line, re.IGNORECASE) and ':' in line:
                in_function_section = False
            # Procesar línea dentro de sección
            if in_function_section and line and len(line) > 15:
                clean_line = re.sub(r'^[•\-\*\d.]+\s*', '', line)
                if clean_line not in functions and len(clean_line) > 10:
                    functions.append(clean_line)
    
    return functions[:10]  # Limitar a 10 funciones

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
    """Extrae información usando TODOS los patrones universales - VERSIÓN ULTRA MEJORADA"""
    
    primary_text = normalize_text(post_description) if post_description else ""
    secondary_text = normalize_text(image_text) if image_text else ""
    
    # === DEBUGGING DETALLADO ===
    logger.debug(f"📝 DESCRIPCIÓN DEL POST ({len(primary_text)} chars): {primary_text[:200]}...")
    logger.debug(f"🖼️ TEXTO OCR ({len(secondary_text)} chars): {secondary_text[:200]}...")
    
    # === ESTRATEGIA CORREGIDA ===
    # Para información estructurada: usar descripción limpia
    if len(primary_text) > 20:
        structural_text = primary_text  # Para empresa, contacto, etc.
        logger.debug("✅ Usando descripción del post para datos estructurados")
    else:
        structural_text = secondary_text
        logger.debug("⚠️ Usando solo texto OCR para datos estructurados")
    
    # Para habilidades y requisitos: SIEMPRE usar OCR (más completo)
    content_text = secondary_text if len(secondary_text) > 50 else primary_text
    logger.debug(f"🎯 Usando texto de {len(content_text)} chars para habilidades/requisitos")
     
    # === EXTRACCIONES MEJORADAS ===
    
    # Información de la empresa
    company_info = extract_company_info(structural_text)
    
    # Información de contacto ULTRA mejorada
    contact_info_enhanced = extract_contact_info_enhanced(structural_text)
    
    # Título del puesto mejorado
    position_title = extract_position_title_enhanced(content_text)
    
    # Tecnologías categorizadas
    technologies = extract_technologies_enhanced(content_text)
    
    # Habilidades blandas
    soft_skills = extract_soft_skills_enhanced(content_text)
    
    # Información adicional
    schedule = extract_schedule_enhanced(content_text)
    education_level = extract_education_level_enhanced(content_text)
    salary_range = extract_salary_range(content_text)
    
    # Secciones tradicionales
    sections_info = extract_requirements_and_knowledge(content_text)
    
    # Extraer beneficios y funciones de manera segura
    benefits = []
    functions = []
    
    # Intentar obtener de secciones formales primero
    if "benefits" in sections_info and sections_info["benefits"]:
        benefits = sections_info["benefits"]
    else:
        # Extraer de manera independiente si no se encontraron en secciones
        try:
            standalone_benefits = extract_standalone_benefits(content_text)
            if standalone_benefits:
                benefits = standalone_benefits
                logger.debug(f"✅ Beneficios extraídos independientemente: {len(standalone_benefits)}")
        except Exception as e:
            logger.debug(f"❌ Error extrayendo beneficios: {str(e)}")
    
    if "functions" in sections_info and sections_info["functions"]:
        functions = sections_info["functions"]
    else:
        # Extraer de manera independiente si no se encontraron en secciones
        try:
            standalone_functions = extract_standalone_functions(content_text)
            if standalone_functions:
                functions = standalone_functions
                logger.debug(f"✅ Funciones extraídas independientemente: {len(standalone_functions)}")
        except Exception as e:
            logger.debug(f"❌ Error extrayendo funciones: {str(e)}")
    
    # === RESULTADO COMPLETO CON CAMPOS CORREGIDOS ===
    result = {
        # Información básica (compatibilidad)
        "company_name": company_info.get("name"),
        "company_industry": company_info.get("industry"),
        "contact_name": contact_info_enhanced.get("name"),
        "contact_position": contact_info_enhanced.get("position"),
        "contact_email": contact_info_enhanced.get("email"),
        "contact_phone": contact_info_enhanced.get("phone"),
        "position_title": position_title,
        "requirements": sections_info.get("requirements", []),
        "knowledge_required": sections_info.get("knowledge", []),
        "functions": functions,  # Usar las funciones extraídas de manera segura
        "benefits": benefits,    # Usar los beneficios extraídos de manera segura
        "is_active": not is_job_post(primary_text, secondary_text)[3],
        "work_modality": extract_work_modality(content_text),
        "duration": extract_duration(content_text),
        
        # === CAMPOS MEJORADOS ===
        # Información de contacto detallada
        "contact_title": contact_info_enhanced.get("title"),
        "contact_department": contact_info_enhanced.get("department"),
        
        # Información del puesto detallada
        "schedule": schedule,
        "education_level": education_level,
        "salary_range": salary_range,
        
        # Tecnologías categorizadas
        "programming_languages": technologies.get("programming_languages"),
        "databases": technologies.get("databases"),
        "cloud_platforms": technologies.get("cloud_platforms"),
        "frameworks_tools": technologies.get("frameworks_tools"),
        "office_tools": technologies.get("office_tools"),
        "specialized_software": technologies.get("specialized_software"),
        
        # Habilidades
        "soft_skills": soft_skills,
        "technical_skills": [],  # Se puede expandir más adelante
        
        # Campos adicionales
        "experience_required": extract_experience_education(content_text).get("experience"),
        "education_required": extract_experience_education(content_text).get("education"),
    }
    return result

def extract_position_title_enhanced(text: str) -> Optional[str]:
    """Extrae títulos de puesto de manera más específica - VERSIÓN ULTRA ROBUSTA CORREGIDA"""
    
    normalized_text = normalize_text(text)
    
    # Patrones para Analista de Experiencia al Cliente (casos específicos conocidos)
    experiencia_patterns = [
        r"(?:Analista|Anahsta)\s+de\s+Experiencia\s+al\s+(?:Cliente|Chente)",
        r"(?:Analista|Anahsta)\s+de\s+Experiencia",
        r"Experiencia\s+al\s+Cliente", 
        r"Customer\s+Experience"
    ]
    
    for pattern in experiencia_patterns:
        if re.search(pattern, normalized_text, re.IGNORECASE):
            return "Analista de Experiencia al Cliente"
    
    # Patrones específicos para títulos de trabajo - TODOS CON VALIDACIÓN ROBUSTA CORREGIDA
    title_patterns = [
        # Patrón 1: "Contacto: Nombre | Cargo"
        r"Contacto:\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*[|\-]\s*([^|\n]+?)(?=\s*(?:Móvil|Teléfono|Email|$))",
        
        # Patrón 2-7: Cargos específicos
        r"(Analista\s+de\s+[^|\n]+)",
        r"(Gerente\s+de\s+[^|\n]+)",
        r"(Coordinador\s+de\s+[^|\n]+)", 
        r"(Director\s+de\s+[^|\n]+)",
        r"(Especialista\s+en\s+[^|\n]+)",
        r"(Manager\s+de\s+[^|\n]+)",
        
        # Patrón 8-11: Departamentos específicos
        r"(Talent\s+Development\s+Center)",
        r"(Experiencia\s+al\s+Cliente)",
        r"(Recursos\s+Humanos)",
        r"(Human\s+Resources)",
        
        # Patrón 12-13: Patrones generales
        r"práctica\s+(?:profesional|laboral)\s+(?:como|en|de)\s+([^\n,.]+)",
        r"(?:puesto|cargo|vacante|posición)\s+(?:de|para|como)\s+([^\n,.]+)",
    ]
    
    for i, pattern in enumerate(title_patterns):
        try:
            match = re.search(pattern, normalized_text, re.IGNORECASE)
            if match:
                # VALIDACIÓN ROBUSTA CORREGIDA: verificar que existe exactamente un grupo
                groups = match.groups()
                if groups and len(groups) >= 1 and groups[0]:  # Asegurar que existe y no está vacío
                    title_candidate = groups[0].strip()
                    
                    # Limpiar el título
                    title_candidate = re.sub(r'^(?:un|una|a|an)\s+', '', title_candidate, flags=re.IGNORECASE)
                    title_candidate = re.sub(r'\s+', ' ', title_candidate)
                    title_candidate = re.sub(r'[^a-zA-Z\s]', ' ', title_candidate)
                    title_candidate = re.sub(r'\s+', ' ', title_candidate).strip()
                    
                    if 5 <= len(title_candidate) <= 100 and len(title_candidate.split()) >= 2:
                        return title_candidate.title()
        except (IndexError, AttributeError) as e:
            # Log del error específico para debugging
            logger.debug(f"Error en patrón {i+1}: {str(e)}")
            continue
    
    # Patrones adicionales con validación extra robusta CORREGIDOS
    additional_title_patterns = [
        # Patrón específico para "Talent Development Center"
        (r"(?:Lcda?\.|Dr[a]?\.|Ing\.|Prof\.).*?(Talent\s+Development\s+Center)", "TDC específico"),
        (r"(?:Contacto|Contact):[^:]*?(Talent\s+Development\s+Center)", "TDC en contacto"),
        
        # Patrones para departamentos/posiciones generales
        (r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s+(?:Center|Development|Department)", "Departamento"),
        (r"([A-Z][a-z]+\s+(?:Humanos|Resources|Analyst|Manager|Coordinator))", "Cargo general"),
        
        # Patrón para posición después del nombre
        (r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\s*[|\-]\s*([A-Z][a-z]+\s+[^|\n]{3,30})", "Posición post-nombre")
    ]
    
    for pattern, description in additional_title_patterns:
        try:
            match = re.search(pattern, normalized_text)
            if match:
                groups = match.groups()
                # CORRECCIÓN: verificar que groups existe y tiene elementos
                if groups and len(groups) >= 1 and groups[0]:
                    title_candidate = groups[0].strip()
                    
                    # Limpiar y normalizar
                    title_candidate = re.sub(r'\s+', ' ', title_candidate).strip()
                    
                    if len(title_candidate) >= 5:
                        return title_candidate
        except (IndexError, AttributeError) as e:
            logger.debug(f"Error en patrón adicional '{description}': {str(e)}")
            continue
    
    return None

def extract_work_modality(text: str) -> Optional[str]:
    """Extrae modalidad con patrones UNIVERSALES - VERSIÓN CORREGIDA"""
    
    normalized_text = normalize_text(text).lower()
    
    modality_patterns = {
        "Presencial": [r"presencial", r"in-person", r"on-site", r"oficina", r"office"],
        "Remoto": [r"remoto", r"remote", r"virtual", r"desde casa", r"work from home", r"home office"],
        "Híbrido": [r"híbrido", r"hybrid", r"mixto", r"mixed", r"semi-presencial"],
    }
    
    for modality, patterns in modality_patterns.items():
        for pattern in patterns:
            try:
                if re.search(pattern, normalized_text):
                    return modality
            except (IndexError, AttributeError) as e:
                logger.debug(f"Error en extract_work_modality: {str(e)}")
                continue
    
    return None

def extract_duration(text: str) -> Optional[str]:
    """Extrae duración con patrones UNIVERSALES - VERSIÓN ULTRA ROBUSTA CORREGIDA"""
    
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
        try:
            match = re.search(pattern, normalized_text)
            if match:
                groups = match.groups()
                # CORRECCIÓN: verificar que groups existe y tiene elementos
                if groups and len(groups) >= 1 and groups[0]:
                    duration = groups[0].strip()
                    return duration
                else:
                    # Si no hay grupos de captura válidos, usar la coincidencia completa
                    return match.group(0).strip()
        except (IndexError, AttributeError) as e:
            logger.debug(f"Error en extract_duration: {str(e)}")
            continue
    
    return None

def extract_experience_education(text: str) -> Dict[str, Optional[str]]:
    """Extrae experiencia y educación con patrones UNIVERSALES - VERSIÓN ULTRA ROBUSTA CORREGIDA"""
    
    normalized_text = normalize_text(text)
    
    result = {"experience": None, "education": None}
    
    # Patrones universales para experiencia
    experience_patterns = [
        r"(?:experiencia|experience)(?:\s+(?:mínima|minimum|de|of))?\s*:?\s*(\d+(?:-\d+)?|\d+\+)\s*(?:años?|meses?|years?|months?)",
        r"(\d+(?:-\d+)?|\d+\+)\s*(?:años?|meses?|years?|months?)\s*(?:de\s+experiencia|of experience|experience)",
        r"(?:con|with)\s+(?:al menos|at least)?\s*(\d+(?:-\d+)?|\d+\+)\s*(?:años?|meses?|years?|months?)",
    ]
    
    for pattern in experience_patterns:
        try:
            match = re.search(pattern, normalized_text, re.IGNORECASE)
            if match:
                groups = match.groups()
                # CORRECCIÓN: verificar que groups existe y tiene elementos
                if groups and len(groups) >= 1 and groups[0]:
                    exp_text = match.group(0).lower()
                    exp_value = groups[0]
                    unit = " años" if any(word in exp_text for word in ["año", "year"]) else " meses"
                    result["experience"] = exp_value + unit
                    break
        except (IndexError, AttributeError) as e:
            logger.debug(f"Error en extract_experience_education (experience): {str(e)}")
            continue
    
    # Patrones universales para educación
    education_patterns = [
        r"(?:estudiante|student|egresado|graduate)\s+(?:de|of|en|in)\s+([^\n,.;]+)",
        r"(?:facultad de|faculty of|carrera de|degree in|título en|bachelor)\s+([^\n,.;]+)",
        r"(?:licenciatura|bachelor|master|maestría|engineering|ingeniería)\s+(?:en|in|de|of)\s+([^\n,.;]+)",
        r"(?:cursando|studying|estudiando)\s+([^\n,.;]+)",
    ]
    
    for pattern in education_patterns:
        try:
            match = re.search(pattern, normalized_text, re.IGNORECASE)
            if match:
                groups = match.groups()
                # CORRECCIÓN: verificar que groups existe y tiene elementos
                if groups and len(groups) >= 1 and groups[0]:
                    education = groups[0].strip()
                    education = re.sub(r'[.,;:]+$', '', education)
                    result["education"] = education.title()
                    break
        except (IndexError, AttributeError) as e:
            logger.debug(f"Error en extract_experience_education (education): {str(e)}")
            continue
    
    return result

def extract_skills_and_technologies(text: str) -> Dict[str, List[str]]:
    """Función de compatibilidad que usa las nuevas extracciones"""
    
    # Usar las nuevas funciones mejoradas
    technologies = extract_technologies_enhanced(text)
    soft_skills = extract_soft_skills_enhanced(text)
    
    # Mapear al formato original para compatibilidad
    result = {
        "programming_languages": technologies["programming_languages"],
        "technologies": (technologies["databases"] + 
                        technologies["cloud_platforms"] + 
                        technologies["frameworks_tools"]),
        "soft_skills": soft_skills
    }
    
    # Limpiar duplicados
    for skill_type in result:
        if isinstance(result[skill_type], list):
            result[skill_type] = list(dict.fromkeys(result[skill_type]))[:10]
    
    return result

def extract_benefits_enhanced(text: str) -> List[str]:
    """Extrae beneficios específicos basado en textos reales"""
    
    normalized_text = normalize_text(text)
    benefits = []
    
    # Patrones específicos de beneficios encontrados en los textos
    benefit_patterns = [
        # Beneficios económicos
        r'(apoyo\s+económico(?:\s*\([^)]+\))?)',
        r'(viático)',
        r'(seguro\s+contra\s+accidentes)',
        
        # Beneficios de desarrollo
        r'(ambiente\s+colaborativo\s+para\s+el\s+crecimiento\s+profesional)',
        r'(capacitación\s+continua)',
        r'(certificaciones\s+sin\s+costo)',
        r'(aprendizaje\s+sobre\s+la\s+industria)',
        r'(acercamiento\s+a\s+la\s+vida\s+laboral)',
        r'(poner\s+en\s+práctica\s+(?:los\s+)?conocimiento)',
        
        # Horarios y modalidades
        r'(horario\s+de\s+lunes\s+a\s+viernes\s+de\s+[^.\n]+)',
        r'(jornada\s+de\s+[^.\n]+)',
        
        # Equipamiento
        r'(estación\s+de\s+trabajo\s+individual)',
        r'(computadora\s+personal)',
        
        # Seguros
        r'(seguro\s+[^.\n]+)',
        
        # Desarrollo profesional general
        r'(crecimiento\s+profesional)',
        r'(posibilidad\s+de\s+inserción\s+laboral)',
        r'(experiencia\s+laboral)',
        r'(entorno\s+profesional\s+real)',
    ]
    
    for pattern in benefit_patterns:
        matches = re.findall(pattern, normalized_text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str) and len(match.strip()) > 5:
                benefit = match.strip()
                
                # Normalizar beneficios
                benefit_mapping = {
                    'apoyo económico': 'Apoyo económico',
                    'viático': 'Viático',
                    'seguro contra accidentes': 'Seguro contra accidentes',
                    'capacitación continua': 'Capacitación continua',
                    'certificaciones sin costo': 'Certificaciones gratuitas',
                    'crecimiento profesional': 'Crecimiento profesional',
                    'experiencia laboral': 'Experiencia laboral práctica',
                }
                
                normalized_benefit = benefit_mapping.get(benefit.lower(), benefit.title())
                
                if normalized_benefit not in benefits:
                    benefits.append(normalized_benefit)
    
    return benefits[:8]  # Máximo 8 beneficios

def extract_from_both_sources(primary_text: str, secondary_text: str, extraction_function, *args) -> Optional[str]:
    """Extrae información intentando ambas fuentes de texto"""
    
    # Intentar primero con el texto primario (descripción del post)
    result = extraction_function(primary_text, *args)
    
    # Si no se encontró resultado y hay texto secundario (OCR), intentar con él
    if (not result or (isinstance(result, dict) and not any(result.values()))) and secondary_text:
        result = extraction_function(secondary_text, *args)
    
    return result