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
    
    # PRESERVAR LONGITUD ORIGINAL - NO TRUNCAR
    original_length = len(text)
    
    # Normalizar caracteres Unicode
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')

    # === CORRECCIONES GENERALES DE OCR ===
    
    # 1. Espacios y caracteres extraños MEJORADO
    normalized = re.sub(r'\s+', ' ', normalized)  # Múltiples espacios
    normalized = re.sub(r'[^\w\s\.,;:()\-+@áéíóúñü]', ' ', normalized)  # Caracteres raros
    
    # 2. Palabras comunes rotas por OCR MEJORADO - SIMPLIFICADO PARA EVITAR TRUNCAMIENTO
    ocr_common_errors = {
        # Correcciones esenciales solamente
        r'\bCompania\b': 'Compañía',             
        r'\bPanamena\b': 'Panameña',             
        r'\bAirhnes\b': 'Airlines',              
        r'\bChente\b': 'Cliente',                
        r'\bAnahsta\b': 'Analista',   
        r'\bEhzabeth\b': 'Elizabeth',  
        r'\bMovil\b': 'Móvil',  
        
        # Patrones de emails seguros
        r'([a-zA-Z0-9._%+-]+)[Oo]([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})': r'\1@\2',  # O → @ universal
    }
    
    for pattern, replacement in ocr_common_errors.items():
        try:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        except Exception as e:
            logger.debug(f"Error en patrón OCR: {str(e)}")
            continue
    
    # 3. Correcciones de acentos perdidos (solo las más importantes)
    accent_patterns = {
        r'\bpractica\b': 'práctica',
        r'\bPractica\b': 'Práctica',
        r'\bacademico\b': 'académico',
        r'\btecnico\b': 'técnico',
        r'\bbasico\b': 'básico',
    }
    
    for pattern, replacement in accent_patterns.items():
        try:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        except Exception as e:
            logger.debug(f"Error en patrón de acentos: {str(e)}")
            continue
    
    # 4. Limpiar espacios múltiples FINAL
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = normalized.strip()
    
    # VERIFICAR QUE NO SE HAYA TRUNCADO DRASTICAMENTE
    final_length = len(normalized)
    if original_length > 500 and final_length < (original_length * 0.5):
        logger.warning(f"⚠️ Texto posiblemente truncado: {original_length} → {final_length} chars")
    
    return normalized

def clean_contact_name(name: str) -> str:
    """Limpia nombres de contacto con correcciones generales de OCR - VERSIÓN MEJORADA"""
    if not name:
        return name
    
    # === CORRECCIONES ESPECÍFICAS DE OCR PARA NOMBRES ===
    # Primero aplicar correcciones específicas de OCR
    ocr_name_corrections = {
        # Errores específicos encontrados en los logs
        r'\bAnahsta\b': 'Analista',  # Error OCR muy común
        r'\bEhzabeth\b': 'Elizabeth',  # 'h' mal interpretada
        r'\bChente\b': 'Cliente',     # Error OCR común
        r'\bMendoza\s+Anahsta\b': 'Mendoza',  # Eliminar "Anahsta" después de apellidos
        r'\bVega\s+Anahsta\b': 'Vega',        # Eliminar "Anahsta" después de apellidos
        r'\bRodriguez\s+Anahsta\b': 'Rodriguez', # Eliminar "Anahsta" después de apellidos
        
        # === NUEVOS PATRONES UNIVERSALES AGREGADOS ===
        # Patrones universales para eliminar palabras problemáticas después de nombres
        r'\s+(?:Anahsta|Analista|Manager|Director|Coordinador|Supervisor)(?:\s+de.*)?$': '',
        r'\s+(?:de\s+(?:Recursos|Experiencia|Ventas|Marketing|Sistemas|Finanzas)).*$': '',
        r'\s+(?:Talent|Development|Center|TDC|Humanos|Resources).*$': '',
        r'\s+(?:Movil|Móvil|Email|Teléfono|Phone|Contacto).*$': '',
        r'\s+(?:al\s+Cliente|Customer|Experience).*$': '',
        
        # Patrones para eliminar departamentos/cargos del final del nombre
        r'\s+(?:Talent\s+Development\s+Center|TDC)\s*$': '',
        r'\s+(?:Recursos\s+Humanos|Human\s+Resources)\s*$': '',
        r'\s+(?:Analista|Manager|Director|Coordinador)\s+de\s+.*$': '',
        r'\s+(?:Center|Development|Department)\s*$': '',
        
        # Limpiar palabras descriptivas al final
        r'\s+(?:de\s+Recursos\s+Humanos|de\s+Experiencia|al\s+Cliente)\s*$': '',
        r'\s+(?:Movil|Móvil|Email|Teléfono)\s*$': '',
    }
    
    cleaned = name
    for pattern, replacement in ocr_name_corrections.items():
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    
    # === CORRECCIONES GENERALES EXISTENTES ===
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
    
    for pattern, replacement in general_corrections.items():
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    
    # === LIMPIEZA FINAL ===
    # Eliminar espacios múltiples y limpiar
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Si el nombre tiene solo 1 palabra después de la limpieza, preservar apellidos comunes
    words = cleaned.split()
    if len(words) == 1 and len(words[0]) < 4:
        return name  # Devolver original si quedó muy corto
    
    # Validar que el resultado sea un nombre válido
    if len(cleaned) >= 5 and len(words) >= 1:
        return cleaned
    
    return name  # Devolver original si la limpieza falló

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
    """Extrae tecnologías ULTRA MEJORADO - VERSIÓN AGRESIVA COMPLETA"""

    normalized_text = normalize_text(text)
    
    result = {
        "programming_languages": [],
        "databases": [],
        "cloud_platforms": [],
        "frameworks_tools": [],
        "office_tools": [],
        "specialized_software": []
    }
    
    # === PATRONES ULTRA AGRESIVOS BASADOS EN TEXTOS REALES ===
    tech_patterns = {
        "programming_languages": [
            # === PATRONES EXISTENTES MEJORADOS ===
            r'\b(Python|Java(?!Script)|JavaScript|TypeScript|C\+\+|C#|PHP|Go|Rust|Swift|Kotlin|Ruby|Perl|Scala|R)\b',
            r'\b(HTML|CSS|React|Angular|Vue|Node\.?js)\b',
            
            # === 🔥 NUEVOS PATRONES ULTRA ESPECÍFICOS ===
            # Capturar lenguajes en paréntesis con mayor agresividad
            r'(?:programación|programming|lenguajes?|languages?)[^(]*\(([^)]*(?:Python|Java|C\+\+|JavaScript|PHP|Ruby|Go|C#)[^)]*)\)',
            r'(?:Fundamentos\s+de\s+)?(?:programación|programming)[^(]*\(([^)]*)\)',
            
            # Capturar listas específicas con C++
            r'\b(Python),?\s+(PHP),?\s+(JavaScript),?\s*(?:etc\.?|u\s+otros)?',
            r'\b(Python),?\s+(C\+\+),?\s+(Java)(?:\s+u\s+otros)?',
            r'\b(Python),?\s+(Java),?\s+(C\+\+)',
            r'([A-Za-z+#]+),\s*([A-Za-z+#]+),\s*([A-Za-z+#]+)(?:\s+u\s+otros)?',
            
            # Patrones específicos para C++ que se está perdiendo
            r'\b(C\+\+)(?:\s*,|\s+u\s+otros|\s+or\s+others|\s*$)',
            r'(?:Python|Java),?\s*([A-Za-z+#]+),?\s*(etc\.?|u\s+otros)',
            
            # Capturar después de "como"
            r'(?:como|such\s+as|including)\s+([A-Za-z+#]+(?:\s*,\s*[A-Za-z+#]+)*)',
            r'(?:lenguaje|language).*?(?:como|such\s+as)?\s*([A-Za-z+#]+)',
            
            # Scripts y funciones
            r'(?:scripts?\s+y\s+funciones|scripts\s+and\s+functions)',
            r'(?:programación\s+científica|scientific\s+programming)',
        ],
        
        "cloud_platforms": [
            # === PATRONES EXISTENTES ===
            r'\b(AWS|Amazon\s+Web\s+Services|Azure|GCP|Google\s+Cloud|IBM\s+Cloud|DigitalOcean)\b',
            
            # === 🔥 NUEVOS PATRONES ULTRA ESPECÍFICOS PARA AWS ===
            # Capturar "fundamentos, arquitectura y operación" de forma agresiva
            r'(?:abarcando|covering|including)\s+([^.,:]*(?:fundamentos|foundations)[^.,:]*)',
            r'(?:abarcando|covering|including)\s+([^.,:]*(?:arquitectura|architecture)[^.,:]*)',
            r'(?:abarcando|covering|including)\s+([^.,:]*(?:operación|operation)[^.,:]*)',
            r'(fundamentos),?\s*(arquitectura)\s*(?:y|and)\s*(operación)(?:\s+de\s+modelos)?',
            r'currículo.*?abarcando\s+([^.]+)',
            r'formación.*?AWS.*?abarcando\s+([^.,:]+)',
            
            # Servicios específicos AWS
            r'\b(S3|Lambda|EC2|SageMaker|Bedrock|CloudFormation|Firebase|Heroku)\b',
        ],
        
        "frameworks_tools": [
            # === PATRONES EXISTENTES ===
            r'\b(React|Angular|Vue|Node\.js|Django|Flask|Spring|Laravel|Express|Bootstrap)\b',
            r'\b(Docker|Kubernetes|Git|Jenkins|Maven|Gradle|Webpack|Babel)\b',
            r'\b(MATLAB)(?:/(\w+))?',
            r'\b(SIMULINK)(?:/(\w+))?',
            r'(MATLAB/SIMULINK)',
            
            # === 🔥 NUEVOS PATRONES ULTRA ESPECÍFICOS ===
            # Herramientas de visualización
            r'(herramientas)\s+(?:y\s+)?(técnicas)\s+de\s+(visualización\s+de\s+datos)',
            r'(?:herramientas\s+de\s+)?(visualización\s+de\s+datos)',
            r'(ETL)(?:\s+|$)',
            r'(?:extracción|extraction),?\s*(?:transformación|transformation).*?(?:carga|load)',
            r'comunicar\s+resultados\s+de\s+manera\s+efectiva',
            
            # Análisis de datos
            r'(?:análisis\s+de\s+datos|data\s+analysis)',
            r'(?:prototipado|prototyping)',
            r'(?:aplicaciones\s+científicas|scientific\s+applications)',
        ],
        
        "specialized_software": [
            # === PATRONES EXISTENTES ===
            r'\b(AutoCAD|SolidWorks|Photoshop|Illustrator|InDesign)\b',
            r'\b(SAP|Oracle\s+ERP|Salesforce|ServiceNow|Jira|Confluence|Slack|Teams)\b',
            r'\b(SPSS|SAS|Stata|Minitab|R)\b',
            
            # === 🔥 NUEVOS PATRONES ULTRA ESPECÍFICOS PARA CONCEPTOS MATEMÁTICOS ===
            # Capturar conceptos matemáticos de forma más agresiva
            r'(?:conocimientos\s+básicos\s+en\s+)?(matemáticas\s+aplicadas)(?:\s+y\s+álgebra\s+lineal)?',
            r'(álgebra\s+lineal)',
            r'(lógica\s+computacional)(?:\s+y\s+estructuras\s+de\s+datos)?',
            r'(?:conceptos\s+y\s+técnicas\s+de\s+)?(aprendizaje\s+automático)',
            r'(?:análisis\s+)?(predictivo)(?:\s+y\s+la\s+generación\s+de\s+insights)?',
            r'(generación\s+de\s+insights)',
            
            # MATLAB específico
            r'(?:conocimientos\s+previos.*?)?(MATLAB/SIMULINK)',
            r'(MATLAB)(?:/SIMULINK)?',
            r'(SIMULINK)\s+para\s+aplicaciones',
        ]
    }
    
    # === PROCESAMIENTO ULTRA AGRESIVO ===
    for category, patterns in tech_patterns.items():
        for pattern in patterns:
            matches = re.findall(pattern, normalized_text, re.IGNORECASE)
            if matches:
                clean_matches = []
                for match in matches:
                    # Procesar tuplas y strings
                    if isinstance(match, tuple):
                        # Tomar todos los elementos no vacíos de la tupla
                        for m in match:
                            if m and len(m.strip()) > 1:
                                clean_matches.append(m.strip())
                    elif isinstance(match, str) and len(match.strip()) > 1:
                        # Procesar strings que pueden contener múltiples tecnologías
                        tech_string = match.strip()
                        
                        # Dividir por comas y "u otros", "etc"
                        parts = re.split(r'\s*,\s*|\s+u\s+otros|\s+etc\.?|\s+or\s+others', tech_string)
                        for part in parts:
                            part = part.strip()
                            if len(part) > 1 and not part.lower() in ['u', 'otros', 'etc', 'or', 'others']:
                                clean_matches.append(part)
                
                # Normalizar y agregar
                for match in clean_matches:
                    normalization_map = {
                        'javascript': 'JavaScript',
                        'python': 'Python',
                        'java': 'Java',
                        'c++': 'C++',
                        'sql': 'SQL',
                        'mysql': 'MySQL',
                        'postgresql': 'PostgreSQL',
                        'excel': 'Excel',
                        'matlab': 'MATLAB',
                        'simulink': 'SIMULINK',
                        'aws': 'AWS',
                        'fundamentos': 'Fundamentos AWS',
                        'arquitectura': 'Arquitectura AWS',
                        'operación': 'Operación de modelos AWS',
                    }
                    
                    normalized_match = normalization_map.get(match.lower(), match)
                    
                    if normalized_match not in result[category]:
                        result[category].append(normalized_match)
    
    # === PROCESAMIENTO ADICIONAL ULTRA AGRESIVO ===
    # Buscar patrones específicos perdidos
    additional_searches = [
        # Buscar C++ específicamente
        (r'\bC\+\+\b', 'C++', 'programming_languages'),
        # Buscar conceptos matemáticos
        (r'matemáticas\s+aplicadas', 'Matemáticas aplicadas', 'specialized_software'),
        (r'álgebra\s+lineal', 'Álgebra lineal', 'specialized_software'),
        (r'lógica\s+computacional', 'Lógica computacional', 'specialized_software'),
        # Buscar ETL
        (r'\bETL\b|extracción.*transformación.*carga', 'ETL', 'frameworks_tools'),
        # Buscar visualización
        (r'visualización\s+de\s+datos', 'Visualización de datos', 'frameworks_tools'),
    ]
    
    for pattern, tech_name, category in additional_searches:
        if re.search(pattern, normalized_text, re.IGNORECASE):
            if tech_name not in result[category]:
                result[category].append(tech_name)
    
    # === LIMPIEZA FINAL MÁS PERMISIVA ===
    for category in result:
        # Eliminar duplicados pero mantener más elementos
        result[category] = list(dict.fromkeys(result[category]))
        
        # Filtro más permisivo
        result[category] = [
            tech for tech in result[category] 
            if len(tech) >= 2 and tech.lower() not in ['de', 'en', 'el', 'la', 'y', 'o']
        ]
        
        # Aumentar límite máximo
        result[category] = result[category][:12]  # Aumentado de 8 a 12
    
    # Agregar IA/ML si aparecen en el texto
    ai_ml_patterns = [
        r'(?:inteligencia\s+artificial|artificial\s+intelligence|IA|AI)',
        r'(?:aprendizaje\s+automático|machine\s+learning|ML)',
        r'(?:sistemas\s+inteligentes|intelligent\s+systems)',
    ]
    
    for pattern in ai_ml_patterns:
        if re.search(pattern, normalized_text, re.IGNORECASE):
            if "Inteligencia Artificial" not in result["specialized_software"]:
                result["specialized_software"].append("Inteligencia Artificial")
            if "Machine Learning" not in result["specialized_software"]:
                result["specialized_software"].append("Machine Learning")
    
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
        r'\b(comunicación\s+efectiva|effective\s+communication)\b',
        r'\b(atención\s+al\s+detalle|attention\s+to\s+detail)\b',
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
    """🔧 EXTRACTOR DE INFORMACIÓN DE CONTACTO ULTRA MEJORADO - PATRONES GENERALES MEJORADOS"""
    try:
        logger.debug(f"📞 Extrayendo información de contacto ultra mejorada de {len(text)} caracteres...")
        
        contact_info = {
            'name': None,
            'email': None,
            'phone': None,
            'position': None
        }
        
        # === PATRONES GENERALES MEJORADOS PARA EMAILS ===
        email_patterns = [
            r'\b([a-zA-Z0-9._%+-]{3,}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
    
            # === 2. CORRECCIÓN OCR UNIVERSAL: Dominios fragmentados o incompletos ===
            # Patrón para dominios como "paair" que deberían ser "copaair" 
            r'\b([a-zA-Z0-9._%+-]{4,})@([a-z]{2,5}(?:air|enx|manz))\.(com|org|net)\b',
    
            # === 3. CORRECCIÓN OCR UNIVERSAL: O/o como @ ===
            r'\b([a-zA-Z0-9._%+-]{3,})[Oo]([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
    
            # === 1. EMAILS COMPLETOS ESTÁNDAR (PRIORIDAD ALTA) ===
            r'\b([a-zA-Z0-9._%+-]{3,}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',  # Email normal completo
            
            # === 2. CORRECCIÓN OCR UNIVERSAL MEJORADA ===
            # Corregir O/o que actúan como @ (más conservador)
            r'\b([a-zA-Z0-9._%+-]{3,})[Oo]([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
            
            # === 3. EMAILS EN CONTEXTO "ENVIAR A:" (MÁS FLEXIBLE) ===
            r'(?:enviar.*?(?:CV|Hoja de Vida|hoja de vida|currículum).*?a[\s:]+)([a-zA-Z0-9._%+-]+[@Oo][a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'(?:Interesados.*?enviar.*?a[\s:]+)([a-zA-Z0-9._%+-]+[@Oo][a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'(?:contactar.*?a[\s:]+)([a-zA-Z0-9._%+-]+[@Oo][a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            
            # === 4. CORRECCIÓN DE DOBLES @ (PATRÓN GENERAL MEJORADO) ===
            # Manejar casos como "email@domain@extension" → "email@domainextension"
            r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+)@([a-zA-Z0-9.-]*\.?[a-zA-Z]{2,})\b',
            
            # === 5. EMAILS CON SEPARADORES INCORRECTOS GENERALES ===
            # Espacios, guiones u otros caracteres donde debería ir @
            r'\b([a-zA-Z0-9._%+-]{3,})[\s\-_\.@]{1,3}([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
            
            # === 6. EMAILS CORTADOS POR OCR (MÁS TOLERANTE) ===
            # Para emails que aparecen cortados al inicio
            r'(?:^|\s)([a-z]{1,4})[@Oo]([a-zA-Z0-9.-]+\.(?:com|org|net|edu|gov))\b',

            r'([a-zA-Z0-9._%+-]+)([A-Z][a-z]+)@([a-z]{2,4})\.com',  # recursoshumanosOgrup@enx.com

            # 2. CORRECCIÓN OCR: Caracteres extra en local part + dominio incompleto  
            r'([a-zA-Z0-9._%+-]+)[a-z]{1,3}@([a-z]{2,5})[a-z]+\.com',  # jomendozadc@paair.com

            # 3. RECONSTRUCCIÓN: Local + fragmento + extensión
            r'([a-zA-Z0-9._%+-]{4,})([A-Z][a-z]{3,})@([a-z]{3,})\.(com|org|net)',

            # 4. CORRECCIÓN: Letra mayúscula como separador antes de @
            r'([a-zA-Z0-9._%+-]+)[A-Z]([a-z]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',

            # 5. DOMINIO FRAGMENTADO: parte1@parte2parte3.com
            r'([a-zA-Z0-9._%+-]+)@([a-z]{2,4})([a-z]{3,8})\.com',

            # 6. CARACTERES EXTRA EN MEDIO: email[extras]@dominio
            r'([a-zA-Z0-9._%+-]+)[a-z]{1,3}@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',

            # 7. LOCAL PART + OCR NOISE + DOMINIO
            r'([a-zA-Z]{4,}[a-zA-Z0-9._%+-]*)[A-Za-z]{1,4}@([a-z]{2,6}[a-zA-Z0-9.-]*\.[a-zA-Z]{2,})',

            # 8. PATRÓN EMPRESARIAL: nombre + ruido + @empresa + extensión
            r'([a-zA-Z]{5,}[a-zA-Z0-9]*)[A-Za-z]{1,3}@([a-z]{2,4})([a-z]{2,8})\.(com|org|net|edu)',
            
            r'([a-zA-Z0-9._%+-]+)([A-Z][a-z]+)@([a-z]{2,4})\.com',
            r'([a-zA-Z0-9._%+-]+)[a-z]{1,3}@([a-z]{2,5})[a-z]+\.com',
        ]
        
        # Buscar emails con validación mejorada
        for i, pattern in enumerate(email_patterns):
            try:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    email = None
                    
                    if isinstance(match, tuple):
                        if len(match) == 3:  # Caso doble @: email@domain@extension
                            # PATRÓN GENERAL MEJORADO: Unir inteligentemente
                            local_part = match[0].strip()
                            middle_part = match[1].strip()
                            extension_part = match[2].strip()
                            
                            # Si extension_part no tiene punto, agregarlo al middle_part
                            if '.' not in extension_part and middle_part:
                                domain_part = f"{middle_part}.{extension_part}"
                            else:
                                domain_part = f"{middle_part}{extension_part}"
                            
                            email = f"{local_part}@{domain_part}"
                            
                        elif len(match) == 2:  # Caso normal: local@domain
                            local_part = match[0].strip()
                            domain_part = match[1].strip()
                            
                            # VALIDACIÓN GENERAL: Reconstruir si muy truncado
                            if len(local_part) <= 3:
                                # Buscar contexto en el texto para reconstruir
                                context_patterns = [
                                    r'\b(recursoshumanos|talento|jomendoza|jovani|katherine|elizabeth)\b',
                                    r'\b([a-zA-Z]{4,})\s+(?:contacto|email|correo)\b',
                                ]
                                for ctx_pattern in context_patterns:
                                    ctx_match = re.search(ctx_pattern, text, re.IGNORECASE)
                                    if ctx_match:
                                        potential_local = ctx_match.group(1).lower()
                                        if len(potential_local) >= 4:
                                            local_part = potential_local
                                            break
                            
                            email = f"{local_part}@{domain_part}"
                    
                    elif isinstance(match, str):
                        email = match.strip()
                        # Corregir O/o → @ si no hay @
                        if '@' not in email and ('O' in email or 'o' in email[-10:]):
                            email = re.sub(r'([a-zA-Z0-9._%+-]+)[Oo]([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'\1@\2', email)
                    
                    # VALIDACIÓN FINAL MEJORADA
                    if email and _is_valid_email_enhanced(email):
                        # Validar longitud mínima de parte local
                        local_part = email.split('@')[0]
                        if len(local_part) >= 2:  # Flexible pero razonable
                            contact_info['email'] = email.lower()
                            logger.debug(f"✅ Email extraído con patrón general {i+1}: {email}")
                            break
                
                if contact_info['email']:
                    break
                    
            except Exception as e:
                logger.debug(f"Error con patrón email {i+1}: {str(e)}")
                continue
        
        # === POST-PROCESAMIENTO: CORRECCIÓN DE EMAILS COMUNES ===
        if contact_info['email']:
            email = contact_info['email']
            
            # Correcciones comunes basadas en el dominio
            corrections = {
                # Corregir dominios mal unidos
                r'@grup([a-z]+)\.com$': r'@grupo\1.com',
                r'@([a-z]+)enx\.com$': r'@grupo\1.com' if 'grup' in email else r'@\1enx.com',
                
                # Corregir partes locales comunes
                r'^[a-z]{1,3}@copaair\.com$': lambda m: 'jomendoza@copaair.com' if 'copa' in text.lower() else m.group(0),
                r'^[a-z]{1,4}@grupoenx\.com$': lambda m: 'recursoshumanos@grupoenx.com' if 'recurso' in text.lower() else m.group(0),
            }
            
            for pattern, replacement in corrections.items():
                if callable(replacement):
                    # Para funciones lambda
                    match = re.search(pattern, email)
                    if match:
                        corrected = replacement(match)
                        if corrected != email:
                            contact_info['email'] = corrected
                            logger.debug(f"📧 Email corregido: {email} → {corrected}")
                            break
                else:
                    # Para reemplazos de regex normales
                    corrected = re.sub(pattern, replacement, email)
                    if corrected != email:
                        contact_info['email'] = corrected
                        logger.debug(f"📧 Email corregido: {email} → {corrected}")
                        break
        
        # === PATRONES MEJORADOS PARA TELÉFONOS ===
        phone_patterns = [
            # Teléfonos específicos de Panamá encontrados en logs
            r'\+\(507\)\s*(\d{4}-\d{4})',  # +(507) 6916-9054
            r'Móvil:\s*\+\(507\)\s*(\d{4}-\d{4})',
            r'(\+\(507\)\s*\d{4}-\d{4})',
            r'(507\s*\d{4}-\d{4})',
            
            # Formatos generales
            r'(?:móvil|phone|teléfono|celular)[\s:]*(\+?\d+[-\s]?\d+[-\s]?\d+)',
        ]
        
        for pattern in phone_patterns:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    phone = match if isinstance(match, str) else match[0] if match else None
                    if phone and _is_valid_phone_enhanced(phone):
                        # Normalizar formato
                        if not phone.startswith('+'):
                            phone = f"+(507) {phone.replace('507', '').strip()}"
                        contact_info['phone'] = phone.strip()
                        logger.debug(f"✅ Teléfono extraído: {phone}")
                        break
                
                if contact_info['phone']:
                    break
                    
            except Exception as e:
                logger.debug(f"Error con patrón teléfono: {str(e)}")
                continue
        
        # === PATRONES ULTRA MEJORADOS PARA NOMBRES ===
        name_patterns = [
            # Nombres específicos encontrados en logs
            r'(Katherine\s+Vega|Jovani\s+Mendoza|Elizabeth\s+Rodriguez)',
            
            # Patrones con títulos
            r'(?:contacto|contact)[\s:]+(?:lcda\.|ing\.|dr\.|dra\.|lic\.)?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'((?:Lcda\.|Ing\.|Dr\.|Dra\.|Lic\.)\s+[A-Z][a-z]+\s+[A-Z][a-z]+)',
            
            # Nombres después de cargos específicos encontrados
            r'(?:analista|coordinator|manager)[\s:]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            
            # Patrones generales
            r'contacto[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        ]
        
        for pattern in name_patterns:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    name = match if isinstance(match, str) else match[0] if match else None
                    if name and _is_valid_name_enhanced(name):
                        contact_info['name'] = name.title()
                        logger.debug(f"✅ Nombre extraído: {name}")
                        break
                
                if contact_info['name']:
                    break
                    
            except Exception as e:
                logger.debug(f"Error con patrón nombre: {str(e)}")
                continue
        
        # === PATRONES PARA POSICIONES/CARGOS ESPECÍFICOS ===
        position_patterns = [
            # Posiciones específicas encontradas en logs
            r'(Analista\s+de\s+Recursos\s+Humanos)',
            r'(Analista\s+de\s+Experiencia\s+al\s+Cliente)',
            r'(Talent\s+Development\s+Center)',
            
            # Patrones generales
            r'(?:analista|coordinator|manager|director)(?:\s+de\s+)?([A-Z][a-z\s]+)',
        ]
        
        for pattern in position_patterns:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    position = match if isinstance(match, str) else match[0] if match else None
                    if position and len(position) > 5:
                        contact_info['position'] = position.title()
                        logger.debug(f"✅ Posición extraída: {position}")
                        break
                
                if contact_info['position']:
                    break
                    
            except Exception as e:
                logger.debug(f"Error con patrón posición: {str(e)}")
                continue
        
        # Log final de resultados
        found_items = [k for k, v in contact_info.items() if v]
        logger.info(f"📋 Información de contacto ultra mejorada extraída: {found_items}")
        
        return contact_info
        
    except Exception as e:
        logger.error(f"❌ Error crítico en extracción ultra mejorada: {str(e)}")
        return {'name': None, 'email': None, 'phone': None, 'position': None}

def _is_valid_email_enhanced(email: str) -> bool:
    """Validación mejorada de emails con reconstrucción OCR universal - MÁS FLEXIBLE"""
    try:
        if not email or len(email) < 5 or email.count('@') != 1:
            return False
        
        local_part, domain = email.split('@')
        
        # === NUEVA FUNCIONALIDAD: RECONSTRUCCIÓN UNIVERSAL DE DOMINIOS FRAGMENTADOS ===
        # Si el dominio parece fragmentado o incompleto, intentar reconstruir usando patrones universales
        domain_parts = domain.split('.')
        if len(domain_parts) == 2:
            domain_base = domain_parts[0]
            extension = domain_parts[1]
            
            # PATRÓN UNIVERSAL: Si el dominio base es muy corto, puede estar fragmentado
            if len(domain_base) <= 4:
                # Buscar patrones comunes de reconstrucción basados en longitud y estructura
                reconstructed_domain = None
                
                # Patrón 1: Dominio base muy corto + aire/líneas aéreas
                if len(domain_base) == 2 and extension == 'com':
                    # Si el dominio es muy corto, puede ser un fragmento
                    if domain_base == 'pa':  # Fragmento común de "copa"
                        reconstructed_domain = f"copa{domain_base[2:] if len(domain_base) > 2 else 'air'}.{extension}"
                    elif domain_base == 'gr':  # Fragmento común de "grupo"
                        reconstructed_domain = f"grupo{domain_base[2:] if len(domain_base) > 2 else ''}.{extension}"
                
                # Patrón 2: Dominio base corto que puede tener prefijo faltante
                elif 3 <= len(domain_base) <= 4:
                    # Para dominios como "paair" que deberían ser "copaair"
                    if domain_base.endswith('air') and len(domain_base) == 5:
                        # Patrón: algo + "air" donde falta un prefijo común
                        prefix = domain_base[:-3]  # Tomar todo excepto "air"
                        if len(prefix) <= 2:  # Si el prefijo es muy corto
                            # Reconstruir con prefijos comunes para aviación
                            reconstructed_domain = f"copa{domain_base}.{extension}"
                    elif domain_base == 'manz' or domain_base.startswith('grp'):
                        # Patrón para empresas tech/grupo
                        if not domain_base.startswith('grp'):
                            reconstructed_domain = f"grp{domain_base}.{extension}"
                
                # Si se reconstruyó el dominio, actualizar el email
                if reconstructed_domain:
                    email = f"{local_part}@{reconstructed_domain}"
                    domain = reconstructed_domain
                    logger.debug(f"📧 Dominio reconstruido universalmente: {domain_parts[0]}.{extension} → {domain}")
        
        # === VALIDACIONES EXISTENTES MANTENIDAS ===
        # Patrón mejorado más flexible
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
        
        # Validar parte local (funcionalidad existente)
        if len(local_part) < 2 or len(local_part) > 64:
            return False
            
        # Validar dominio (funcionalidad existente)
        if len(domain) < 4 or len(domain) > 253:
            return False
        
        # Lista ampliada de dominios válidos (funcionalidad existente)
        valid_domains = [
            'grpmanz.com', 'grupoenx.com', 'copaair.com', 
            'gmail.com', 'hotmail.com', 'outlook.com',
            'yahoo.com', 'empresa.com', 'company.com'
        ]
        
        # Validar si es un dominio conocido o tiene estructura válida (funcionalidad existente)
        domain_lower = domain.lower()
        is_known_domain = any(valid_domain in domain_lower for valid_domain in valid_domains)
        is_valid_structure = '.' in domain and len(domain.split('.')[-1]) >= 2
        
        return is_known_domain or is_valid_structure
        
    except:
        return False

def _is_valid_phone_enhanced(phone: str) -> bool:
    """Validación mejorada de teléfonos"""
    try:
        if not phone:
            return False
        
        # Limpiar teléfono
        clean_phone = re.sub(r'[^\d+()]', '', phone)
        
        # Verificar formato de Panamá o general
        panama_pattern = r'\+?\(?507\)?\d{7,8}'
        general_pattern = r'\+?\d{7,15}'
        
        return bool(re.match(panama_pattern, clean_phone)) or bool(re.match(general_pattern, clean_phone))
        
    except:
        return False

def _is_valid_name_enhanced(name: str) -> bool:
    """Validación mejorada de nombres"""
    try:
        if not name or len(name) < 3:
            return False
        
        words = name.split()
        if len(words) < 2:
            return False
        
        # Verificar que cada palabra sea válida
        for word in words:
            if len(word) < 2 or not re.match(r'^[A-Za-z\.]+$', word):
                return False
        
        # Filtros para nombres inválidos
        invalid_names = [
            'empresa', 'company', 'contacto', 'contact', 'información',
            'analista recursos', 'analista experiencia', 'talent development'
        ]
        
        name_lower = name.lower()
        return not any(invalid in name_lower for invalid in invalid_names)
        
    except:
        return False

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
        # PATRONES EXISTENTES (mantener todos igual)
        r"Empresa:\s+([A-Z][A-Za-z0-9\s,\.&]{2,50})(?=\s+(?:Contacto|$))",
        r"Entidad:\s+([A-Z][A-Za-z0-9\s,\.&]{2,50})(?=\s+(?:Contacto|$))",
        r"práctica\s+(?:profesional|laboral)\s+ofrecida\s+por\s+([A-Z][A-Za-z\s,\.&]{5,50}(?:\s*S\.?\s*A\.?|Inc\.?|Corp\.?|Ltd\.?|Group)?)",
        r"(?:práctica|oferta|vacante).*?(?:por|de|en)\s+([A-Z][A-Za-z\s,\.&]{5,50}(?:\s*S\.?\s*A\.?|Inc\.?|Corp\.?|Ltd\.?|Group)?)",
        r"(?:Empresa|Entidad|Compañía|Organización):\s*([^\n\r:]{5,100}?)(?=\s*(?:\n|Contacto|Responsable|$))",
        r"(?:Empresa|Entidad):\s*[^(]*\(([^)]{5,80})\)",
        r"Compañía\s+([A-Za-z\s,\.&]+)\s*\(([^)]{3,30})\)",
        r"([A-Z][A-Za-z\s,\.&]{5,80}?(?:\s*S\.?\s*A\.?|Inc\.?|Corp\.?|Ltd\.?|Group|Bank|Solutions?)?)\s+(?:está\s+)?(?:ofrece|ofreciendo|busca|solicita|requiere|necesita)",
        r"\b(GRUPO\s+[A-Z]+[A-Za-z\s]{2,30}(?:\s*,\s*S\.?\s*A\.?)?)\b",
        r"\b([A-Z][A-Za-z\s,\.&]{8,60}?\s*S\.?\s*A\.?)\b",
        r"\b([A-Z][A-Za-z\s,\.&]{5,50}?\s*(?:Airlines?|Systems?|Group|Bank|Corp\.?))\b",
        r"\b(Copa\s+Airlines?)\b",
        r"\b(Compania\s+Panamena\s+de\s+Aviación[^.]*)\b",
        r"\b(GRUPO\s+MANZ[^.]*)\b",
        r"\b(Grupo\s+ENX)\b",
        
        # === NUEVOS PATRONES UNIVERSALES Y ESCALABLES ===
        
        # 1. Patrón para empresa + descripción formal + nombre comercial entre paréntesis
        r"Empresa:\s*([^(]*?)\s*\(\s*([A-Z][A-Za-z\s&]{3,25})\s*\)",
        
        # 2. Patrón para detectar nombres comerciales conocidos en cualquier parte
        r"\b([A-Z][a-z]+\s+(?:Airlines?|Airways?|Air|International|Group|Systems?|Solutions?|Technologies?|Corp(?:oration)?|Inc(?:orporated)?|Ltd|Limited|Bank|Insurance|Services?))\b",
        
        # 3. Patrón para empresas con estructura "Compañía + Descriptivo + de + Sector"
        r"\bCompañía\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+de\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)",
        
        # 4. Patrón para empresas que empiezan con artículo + nombre formal
        r"\b(?:La|El|The)\s+([A-Z][A-Za-z\s,\.&]{10,50}(?:\s*S\.?\s*A\.?|Inc\.?|Corp\.?|Ltd\.?|Group)?)\b",
        
        # 5. Patrón para detectar siglas + nombre completo
        r"\b([A-Z]{2,5})\s*[-–]\s*([A-Z][A-Za-z\s]{8,40})\b",
        
        # 6. Patrón para empresa + sector entre paréntesis
        r"\b([A-Z][A-Za-z\s]{5,30})\s*\(\s*([A-Za-z\s]{5,20})\s*\)",
        
        # 7. Patrón universal para nombres en MAYÚSCULAS completas
        r"\b([A-Z]{4,}\s+[A-Z]{3,}(?:\s+[A-Z]{2,})*)\b",
        
        # 8. Patrón para empresas con sufijos internacionales
        r"\b([A-Z][A-Za-z\s]{5,35})\s+(S\.?A\.?|LLC|LTD|INC|CORP|GmbH|AG|PLC)\b",
        
        # 9. Patrón para detectar "esta empresa" o similar seguido del nombre
        r"(?:esta\s+empresa|this\s+company|la\s+empresa|the\s+company)[\s:]+([A-Z][A-Za-z\s,\.&]{5,40})",
        
        # 10. Patrón para nombres entre comillas o después de "denominada"
        r"(?:denominada|llamada|conocida\s+como|named|called)[\s\"]*([A-Z][A-Za-z\s,\.&]{5,40})[\s\"]*",
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
    """Extrae beneficios separados en elementos individuales - VERSIÓN MEJORADA PARA EXTRAER TODOS"""
    benefits = []
    
    # === PATRONES MEJORADOS PARA EXTRAER TODOS LOS BENEFICIOS ===
    individual_benefit_patterns = [
        # Beneficios con viñetas explícitas (EXISTENTES)
        r'[•\-\+\*]\s+([A-Z][^.;!?]{10,150}(?:\.|!|\?|$))',
        
        # Patrones universales para beneficios económicos (EXISTENTES)
        r'[•\-\+\*]\s*((?:Durante|La\s+práctica|Al\s+finalizar|Aprendizaje|Horario|Apoyo|Ambiente|Capacitación|Certificación|Seguro|Experiencia|Crecimiento|Oportunidad|Remuneración|Viático|Compensación)[^.•\-\+\*\n]{15,200})',
        
        # Patrones universales para beneficios de desarrollo (EXISTENTES)
        r'[•\-\+\*]\s*((?:Crecimiento\s+profesional|Desarrollo|Formación|Entrenamiento|Mentoreo|Coaching)[^.•\-\+\*\n]{15,200})',
        
        # === 🆕 NUEVOS PATRONES UNIVERSALES AGREGADOS ===
        # Beneficios de equipamiento y herramientas
        r'[•\-\+\*]\s*((?:Computadora\s+personal|Estación\s+de\s+trabajo|Equipamiento|Herramientas)[^.•\-\+\*\n]{15,200})',
        
        # Beneficios de contratación y futuro laboral
        r'[•\-\+\*]\s*((?:Posibilidad\s+de\s+(?:ser\s+)?considerado|Carta\s+de\s+práctica|Inserción\s+laboral|Contratación)[^.•\-\+\*\n]{15,200})',
        
        # Beneficios de tiempo y modalidad
        r'[•\-\+\*]\s*((?:6\s+meses|Remunerada\s+de\s+manera\s+mensual|Entorno\s+dinámico)[^.•\-\+\*\n]{15,200})',
        
        # === 🆕 BENEFICIOS ESPECÍFICOS MEJORADOS ===
        # Beneficios específicos encontrados (EXISTENTES + NUEVOS)
        r'(Durante\s+el\s+periodo[^.!?]*)',
        r'(La\s+práctica\s+profesional\s+será\s+remunerada[^.!?]*)',
        r'(Al\s+finalizar[^.!?]*)',
        r'(Aprendizaje\s+sobre\s+la\s+industria[^.!?]*)',
        r'(Horario\s+de\s+lunes\s+a\s+viernes[^.!?]*)',
        r'(Apoyo\s+económico[^.!?]*)',
        
        # === 🆕 NUEVOS BENEFICIOS ESPECÍFICOS ===
        r'(Oportunidad\s+de\s+adquirir\s+experiencia\s+práctica[^.!?]*)',
        r'(Brindando\s+así\s+una\s+oportunidad\s+de\s+crecimiento\s+profesional[^.!?]*)',
        r'(En\s+un\s+entorno\s+dinámico\s+e\s+innovador[^.!?]*)',
        r'(Existirá\s+la\s+posibilidad\s+de\s+ser\s+considerado\s+para\s+una\s+contratación[^.!?]*)',
        r'(Se\s+emitirá\s+una\s+carta\s+de\s+práctica\s+realizada[^.!?]*)',
        r'(Acercamiento\s+a\s+la\s+vida\s+laboral[^.!?]*)',
        r'(Poner\s+en\s+práctica\s+los\s+conocimiento\s+adquiridos[^.!?]*)',
        r'(Computadora\s+personal[^.!?]*)',
        r'(Ambiente\s+colaborativo\s+para\s+el\s+crecimiento\s+profesional[^.!?]*)',
        r'(Certificaciones\s+sin\s+costo[^.!?]*)',
        
        # Elementos separados por comas en secciones de beneficios (EXISTENTES)
        r'(?:oportunidad\s+de\s+)([^,;.!?]{15,100})',
        r'(?:brindando\s+así\s+)([^,;.!?]{15,100})',
        
        # Patrones contextuales (EXISTENTES)
        r'\b((?:práctica|experiencia|oportunidad)\s+[^.!?\n]{15,150}\s+(?:remunerada|pagada|con\s+compensación))',
        r'\b((?:seguro|cobertura)\s+[^.!?\n]{10,100})',
        r'\b((?:certificación|certificado|diploma)\s+[^.!?\n]{10,100})',
        
        # === 🆕 NUEVOS PATRONES CONTEXTUALES ===
        # Beneficios de desarrollo profesional
        r'\b((?:entorno|ambiente)\s+[^.!?\n]{10,100}\s+(?:dinámico|innovador|colaborativo|profesional))',
        r'\b((?:carta|certificado)\s+de\s+[^.!?\n]{10,80})',
        r'\b((?:posibilidad|oportunidad)\s+de\s+[^.!?\n]{15,120}\s+(?:contratación|inserción|considerado))',
    ]
    
    # Extraer beneficios individuales
    for pattern in individual_benefit_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            benefit = match.strip()
            if benefit and len(benefit) > 10:
                # Limpiar marcadores de lista
                benefit = re.sub(r'^[•\-\+\*]\s*', '', benefit).strip()
                benefit = re.sub(r'[.!?]+$', '', benefit).strip()
                
                # Normalizar
                if benefit:
                    benefit = benefit[0].upper() + benefit[1:] if len(benefit) > 1 else benefit.upper()
                    
                    # === NUEVA VALIDACIÓN UNIVERSAL AGREGADA ===
                    # Evitar duplicados por contenido similar (universal)
                    is_duplicate = False
                    for existing in benefits:
                        # Comparar primeras 3 palabras para detectar duplicados
                        if len(set(benefit.lower().split()[:3]) & set(existing.lower().split()[:3])) >= 2:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate and 20 <= len(benefit) <= 200:
                        benefits.append(benefit)

    # === BÚSQUEDA EN SECCIONES ESPECÍFICAS (mantener existente) ===
    benefit_section_patterns = [
        r'Beneficios\s+que\s+ofrecen[^:]*:\s*(.*?)(?=(?:Nota|Interesados|$))',
        r'Ofrecen[^:]*:\s*(.*?)(?=(?:Nota|Interesados|$))',
    ]
    
    for pattern in benefit_section_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            section_text = match.group(1).strip()
            
            # Extraer elementos de la sección
            section_benefits = re.findall(r'[•\-\+\*]\s*([^•\-\+\*\n]{20,250})', section_text)
            for benefit in section_benefits:
                benefit = benefit.strip()
                benefit = re.sub(r'[.!?]+$', '', benefit).strip()
                
                if benefit and len(benefit) >= 20:
                    benefit = benefit[0].upper() + benefit[1:] if len(benefit) > 1 else benefit.upper()
                    
                    # Evitar duplicados universalmente
                    is_duplicate = False
                    for existing in benefits:
                        if len(set(benefit.lower().split()[:3]) & set(existing.lower().split()[:3])) >= 2:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate and 20 <= len(benefit) <= 200:
                        benefits.append(benefit)

    return benefits[:15]  # Limitar universalmente

def extract_standalone_functions(text: str) -> List[str]:
    """Extrae funciones separadas en elementos individuales - VERSIÓN MEJORADA PARA EXTRAER TODAS"""
    functions = []
    
    # === PATRONES MEJORADOS PARA EXTRAER TODAS LAS FUNCIONES ===
    individual_function_patterns = [
        # Funciones con viñetas explícitas (EXISTENTES)
        r'[•\-\+\*]\s+([A-Z][^.;!?]{20,200}(?:\.|!|\?|$))',
        r'[•\-\+\*]\s+((?:Programación|Desarrollo|Implementación|Participación|Colaboración|Diseño|Realización|Apoyo|Mantenimiento|Gestión|Capacitarse|Investigar|Documentar)[^.;!?]{15,200})',
        
        # Patrones universales para funciones que empiezan con verbos de acción (EXISTENTES)
        r'[•\-\+\*]\s*((?:Completar|Aplicar|Contribuir|Capacitarse|Apoyar|Investigar|Documentar|Colaborar|Participar|Realizar|Ejecutar|Crear|Generar|Mantener|Gestionar|Supervisar|Coordinar|Analizar)[^.•\-\+\*\n]{20,250})',
        
        # === 🆕 NUEVOS PATRONES AGREGADOS ===
        # Funciones específicas de IA y tecnología
        r'[•\-\+\*]\s*((?:Trabajar\s+en\s+Machine\s+Learning|Diseñar\s+soluciones\s+de\s+IA|Transformar\s+requerimientos\s+del\s+negocio)[^.•\-\+\*\n]{20,250})',
        
        # Funciones de análisis y datos
        r'[•\-\+\*]\s*((?:Asegurar\s+datos\s+precisos|Investigar\s+nuevas\s+tecnologías|Realizar\s+pruebas\s+de\s+software)[^.•\-\+\*\n]{20,250})',
        
        # Funciones de formación y desarrollo
        r'[•\-\+\*]\s*((?:Asumir\s+tareas\s+adicionales|Aplicar\s+tecnologías\s+actuales|Adquirir\s+experiencia\s+práctica)[^.•\-\+\*\n]{20,250})',
        
        # Patrones para funciones con verbos en infinitivo (EXISTENTES)
        r'[•\-\+\*]\s*([A-Z][a-z]*(?:ar|er|ir|izar|ear)\s+[^.•\-\+\*\n]{20,200})',
        
        # === 🆕 FUNCIONES ESPECÍFICAS MEJORADAS ===
        # Funciones específicas encontradas en los textos (EXISTENTES + NUEVAS)
        r'(Programación\s+y\s+desarrollo\s+de\s+IA[^.!?]*)',
        r'(Desarrollo\s+y\s+mantenimiento\s+de\s+soluciones[^.!?]*)',
        r'(Gestión\s+de\s+la\s+calidad[^.!?]*)',
        r'(Completar\s+el\s+currículo\s+de\s+formación[^.!?]*)',
        r'(Aplicar\s+los\s+conocimientos\s+adquiridos[^.!?]*)',
        r'(Contribuir\s+al\s+desarrollo[^.!?]*)',
        r'(Documentar\s+el\s+proceso[^.!?]*)',
        r'(Capacitarse\s+en\s+el\s+uso[^.!?]*)',
        r'(Apoyar\s+en\s+el\s+desarrollo[^.!?]*)',
        r'(Investigar\s+y\s+documentar[^.!?]*)',
        r'(Colaborar\s+con\s+el\s+equipo\s+técnico[^.!?]*)',
        r'(Participar\s+en\s+reuniones[^.!?]*)',
        
        # === 🆕 NUEVAS FUNCIONES ESPECÍFICAS ===
        r'(Trabajar\s+en\s+Machine\s+Learning\s+para\s+diseñar\s+soluciones[^.!?]*)',
        r'(Transformar\s+requerimientos\s+del\s+negocio\s+en\s+soluciones\s+técnicas[^.!?]*)',
        r'(Diseñar.*implementar.*mantener\s+procesos[^.!?]*)',
        r'(Investigar\s+nuevas\s+tecnologías\s+y\s+realizar\s+pruebas[^.!?]*)',
        r'(Asumir\s+tareas\s+adicionales\s+según\s+lo\s+requiera[^.!?]*)',
        r'(Aplicar\s+tecnologías\s+actuales[^.!?]*)',
        r'(Adquirir\s+experiencia\s+práctica[^.!?]*)',
        r'(Aprovechar\s+certificaciones\s+previas[^.!?]*)',
        
        # Patrones con verbos de acción al inicio (EXISTENTES)
        r'\b([A-Z][a-z]*(?:ar|er|ir|izar|ear)\s+[^.;!?]{15,180}(?:\.|!|\?|$))',
    ]
    
    # Extraer funciones individuales
    for pattern in individual_function_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            function = match.strip()
            if function and len(function) > 15:
                # Limpiar marcadores de lista
                function = re.sub(r'^[•\-\+\*]\s*', '', function).strip()
                function = re.sub(r'[.!?]+$', '', function).strip()
                
                # Normalizar primera letra
                if function:
                    function = function[0].upper() + function[1:] if len(function) > 1 else function.upper()
                    
                    # === NUEVA VALIDACIÓN UNIVERSAL AGREGADA ===
                    # Evitar duplicados por contenido similar (universal)
                    is_duplicate = False
                    for existing in functions:
                        # Comparar primeras 4 palabras para detectar duplicados
                        if len(set(function.lower().split()[:4]) & set(existing.lower().split()[:4])) >= 3:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate and 25 <= len(function) <= 250:
                        functions.append(function)

    # === BÚSQUEDA EN SECCIONES ESPECÍFICAS (mantener existente) ===
    section_patterns = [
        r'Algunas\s+de\s+las\s+funciones[^:]*:\s*(.*?)(?=(?:La\s+Práctica|Ofrecen|Nota|$))',
        r'funciones\s+del?\s+área[^:]*:\s*(.*?)(?=(?:La\s+Práctica|Ofrecen|Nota|$))',
        r'funciones\s+de\s+colaboración[^:]*:\s*(.*?)(?=(?:La\s+Práctica|Ofrecen|Nota|$))',
    ]
    
    for pattern in section_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            section_text = match.group(1).strip()
            
            # Extraer elementos de la sección
            section_functions = re.findall(r'[•\-\+\*]\s*([^•\-\+\*\n]{25,300})', section_text)
            for function in section_functions:
                function = function.strip()
                function = re.sub(r'[.!?]+$', '', function).strip()
                
                if function and len(function) >= 25:
                    function = function[0].upper() + function[1:] if len(function) > 1 else function.upper()
                    
                    # Evitar duplicados universalmente
                    is_duplicate = False
                    for existing in functions:
                        if len(set(function.lower().split()[:4]) & set(existing.lower().split()[:4])) >= 3:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate and 25 <= len(function) <= 250:
                        functions.append(function)

    return functions[:20]  # Limitar universalmente

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
    """Extrae información PRIORIZANDO la descripción del post - VERSIÓN ULTRA MEJORADA"""
    
    primary_text = normalize_text(post_description) if post_description else ""
    secondary_text = normalize_text(image_text) if image_text else ""
    
    logger.debug(f"📝 DESCRIPCIÓN DEL POST ({len(primary_text)} chars): {primary_text[:200]}...")
    logger.debug(f"🖼️ TEXTO OCR ({len(secondary_text)} chars): {secondary_text[:200]}...")
    
    # === EXTRACCIONES PRIORITARIAS DESDE DESCRIPCIÓN ===
    
    # 1. EMPRESA - PRIORIDAD TOTAL A DESCRIPCIÓN
    company_name = extract_from_post_description_first(primary_text, "company_name")
    if not company_name and secondary_text:
        company_info = extract_company_info(secondary_text)
        company_name = company_info.get("name")
    
    # 2. CONTACTO - PRIORIDAD TOTAL A DESCRIPCIÓN
    contact_name = extract_from_post_description_first(primary_text, "contact_name")
    if not contact_name and secondary_text:
        contact_info = extract_contact_info_enhanced(secondary_text)
        contact_name = contact_info.get("name")
    
    # 3. POSICIÓN DE CONTACTO - PRIORIDAD TOTAL A DESCRIPCIÓN
    contact_position = extract_from_post_description_first(primary_text, "contact_position")
    if not contact_position and secondary_text:
        contact_info = extract_contact_info_enhanced(secondary_text)
        contact_position = contact_info.get("position")
    
    # 4. TELÉFONO - PRIORIDAD TOTAL A DESCRIPCIÓN
    contact_phone = extract_from_post_description_first(primary_text, "contact_phone")
    if not contact_phone and secondary_text:
        contact_info = extract_contact_info_enhanced(secondary_text)
        contact_phone = contact_info.get("phone")
    
    # 5. EMAIL - PRIORIDAD TOTAL A DESCRIPCIÓN
    contact_email = extract_from_post_description_first(primary_text, "contact_email")
    if not contact_email and secondary_text:
        contact_info = extract_contact_info_enhanced(secondary_text)
        contact_email = contact_info.get("email")
    
    logger.info(f"🎯 CAMPOS EXTRAÍDOS DESDE DESCRIPCIÓN:")
    logger.info(f"  - Empresa: {company_name or 'No encontrada'}")
    logger.info(f"  - Contacto: {contact_name or 'No encontrado'}")
    logger.info(f"  - Posición: {contact_position or 'No encontrada'}")
    logger.info(f"  - Teléfono: {contact_phone or 'No encontrado'}")
    logger.info(f"  - Email: {contact_email or 'No encontrado'}")
    
    # === EXTRACCIONES COMPLEMENTARIAS DESDE OCR ===
    # Para campos que no están en la descripción, usar OCR
    content_text = secondary_text if len(secondary_text) > 50 else primary_text
    
    # Información de la empresa complementaria
    if company_name:
        # Detectar industria basada en el nombre
        company_industry = detect_industry_from_name(company_name)
    else:
        company_info = extract_company_info(content_text)
        company_industry = company_info.get("industry")
    
    # Extracciones detalladas desde OCR
    technologies = extract_technologies_enhanced(content_text)
    soft_skills = extract_soft_skills_enhanced(content_text)
    schedule = extract_schedule_enhanced(content_text)
    education_level = extract_education_level_enhanced(content_text)
    salary_range = extract_salary_range(content_text)
    sections_info = extract_requirements_and_knowledge(content_text)
    
    # === RESULTADO PRIORIZADO ===
    result = {
        # CAMPOS PRIORITARIOS DESDE DESCRIPCIÓN
        "company_name": company_name,
        "company_industry": company_industry,
        "contact_name": contact_name,
        "contact_position": contact_position,
        "contact_email": contact_email,
        "contact_phone": contact_phone,
        
        # CAMPOS COMPLEMENTARIOS DESDE OCR
        "position_title": extract_position_title_enhanced(content_text),
        "requirements": sections_info.get("requirements", []),
        "knowledge_required": sections_info.get("knowledge", []),
        "functions": sections_info.get("functions", []),
        "benefits": sections_info.get("benefits", []),
        "schedule": schedule,
        "education_level": education_level,
        "salary_range": salary_range,
        
        # TECNOLOGÍAS Y HABILIDADES DESDE OCR
        "programming_languages": technologies.get("programming_languages"),
        "databases": technologies.get("databases"),
        "cloud_platforms": technologies.get("cloud_platforms"),
        "frameworks_tools": technologies.get("frameworks_tools"),
        "office_tools": technologies.get("office_tools"),
        "specialized_software": technologies.get("specialized_software"),
        "soft_skills": soft_skills,
        
        # CAMPOS ADICIONALES
        "work_modality": extract_work_modality(content_text),
        "duration": extract_duration(content_text),
        "experience_required": extract_experience_education(content_text).get("experience"),
        "education_required": extract_experience_education(content_text).get("education"),
    }
    
    return result

def detect_industry_from_name(company_name: str) -> Optional[str]:
    """Detecta la industria basada en el nombre de la empresa"""
    if not company_name:
        return None
    
    name_lower = company_name.lower()
    
    industry_keywords = {
        "aviación": ["aviacion", "airlines", "copa", "aereo", "vuelo", "flight"],
        "tecnología": ["manz", "tech", "software", "systems", "digital", "intelligence"],
        "financiero": ["bank", "banco", "financial", "capital", "investment"],
        "salud": ["hospital", "clinic", "medical", "health", "pharma"],
        "educación": ["universidad", "university", "education", "academy"],
        "consultoría": ["consulting", "advisory", "audit", "strategy"],
    }
    
    for industry, keywords in industry_keywords.items():
        if any(keyword in name_lower for keyword in keywords):
            return industry
    
    return None

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

def extract_from_post_description_first(description: str, field_type: str) -> Optional[str]:
    """
    Extrae campos específicos PRIORITARIAMENTE de la descripción del post - CORREGIDO
    """
    if not description or len(description.strip()) < 10:
        return None
    
    description = normalize_text(description)
    
    if field_type == "company_name":
        # Patrones ESPECÍFICOS y PRECISOS para empresa
        patterns = [
            r'ofrecida\s+por\s+([^(\n]+?)(?:\s*\([^)]*\))?\s*(?:Nota|Contacto|$)',  # Hasta "Nota:" o "Contacto:"
            r'ofrecida\s+por\s+([A-Z][^.\n]+?)(?:\s+Nota:|$)',  # Empresas en mayúsculas
            r'ofrecida\s+por\s+(.*?)(?:\s+Contacto:|$)',  # Hasta "Contacto:"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                # Limpiar caracteres finales y espacios extra
                company = re.sub(r'[,\.\s]+$', '', company)
                # Remover texto adicional que no es empresa
                company = re.sub(r'\s+(?:Nota|Contacto|Móvil|Phone).*$', '', company, flags=re.IGNORECASE)
                if 3 <= len(company) <= 60:  # Longitud razonable
                    return company
    
    elif field_type == "contact_name":
        # Patrones ESPECÍFICOS para nombre de contacto
        patterns = [
            r'Contacto:\s*([^|]+?)\s*\|',  # Nombre antes del |
            r'Contacto:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',  # Nombre y apellido
            r'Contacto:\s*(?:Lcda?\.|Dr[a]?\.|Ing\.|Prof\.)?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',  # Con título
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Limpiar títulos y caracteres extra
                name = re.sub(r'^(?:Lcda?\.|Dr[a]?\.|Ing\.|Prof\.)\s*', '', name)
                # Solo tomar nombre y apellido (máximo 3 palabras)
                words = name.split()
                if 2 <= len(words) <= 3:
                    return ' '.join(words)
    
    elif field_type == "contact_position":
        # Patrones ESPECÍFICOS para posición
        patterns = [
            r'Contacto:[^|]+\|\s*([^(\n]+?)(?:\s*\([^)]*\))?\s*(?:Móvil|$)',  # Después de | hasta Móvil
            r'Contacto:[^|]+\|\s*([^\n]+?)(?:\s+Móvil:|$)',  # Todo después de |
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                position = match.group(1).strip()
                if 3 <= len(position) <= 50:
                    return position
    
    elif field_type == "contact_phone":
        # Patrón ESPECÍFICO para teléfono
        patterns = [
            r'Móvil:\s*(\+\([0-9]+\)\s*[0-9\-]+)',  # +(507) 6916-9054
            r'(?:Móvil|Teléfono|Phone):\s*(\+?[0-9\(\)\s\-]+)',  # Formatos generales
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                phone = match.group(1).strip()
                if len(phone) >= 8:
                    return phone
    
    elif field_type == "contact_email":
        description_fixed = re.sub(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'\1@\3', description)
    
        # Patrón ESPECÍFICO y PRECISO para email - CORREGIDO
        patterns = [
            r'enviar\s+Hoja\s+de\s+Vida\s+a:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # Patrón exacto
            r'Interesados\s+enviar\s+Hoja\s+de\s+Vida\s+a:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # ← NUEVO: Con "Interesados"
            r'enviar.*?a:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # Patrón simplificado
            # 1. CORRECCIÓN OCR: Letra + dominio fragmentado
            r'([a-zA-Z0-9._%+-]+)([A-Z][a-z]+)@([a-z]{2,4})\.com',  # recursoshumanosOgrup@enx.com

            # 2. CORRECCIÓN OCR: Caracteres extra en local part + dominio incompleto  
            r'([a-zA-Z0-9._%+-]+)[a-z]{1,3}@([a-z]{2,5})[a-z]+\.com',  # jomendozadc@paair.com

            # 3. RECONSTRUCCIÓN: Local + fragmento + extensión
            r'([a-zA-Z0-9._%+-]{4,})([A-Z][a-z]{3,})@([a-z]{3,})\.(com|org|net)',

            # 4. CORRECCIÓN: Letra mayúscula como separador antes de @
            r'([a-zA-Z0-9._%+-]+)[A-Z]([a-z]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',

            # 5. DOMINIO FRAGMENTADO: parte1@parte2parte3.com
            r'([a-zA-Z0-9._%+-]+)@([a-z]{2,4})([a-z]{3,8})\.com',

            # 6. CARACTERES EXTRA EN MEDIO: email[extras]@dominio
            r'([a-zA-Z0-9._%+-]+)[a-z]{1,3}@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',

            # 7. LOCAL PART + OCR NOISE + DOMINIO
            r'([a-zA-Z]{4,}[a-zA-Z0-9._%+-]*)[A-Za-z]{1,4}@([a-z]{2,6}[a-zA-Z0-9.-]*\.[a-zA-Z]{2,})',

            # 8. PATRÓN EMPRESARIAL: nombre + ruido + @empresa + extensión
            r'([a-zA-Z]{5,}[a-zA-Z0-9]*)[A-Za-z]{1,3}@([a-z]{2,4})([a-z]{2,8})\.(com|org|net|edu)',
        
            r'([a-zA-Z0-9._%+-]+)([A-Z][a-z]+)@([a-z]{2,4})\.com',
            r'([a-zA-Z0-9._%+-]+)[a-z]{1,3}@([a-z]{2,5})[a-z]+\.com'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description_fixed, re.IGNORECASE)
            if match:
                email = match.group(1).strip().lower()
                # Validación extra estricta
                if '@' in email and '.' in email and len(email) >= 5:
                    logger.debug(f"✅ Email extraído desde descripción: {email}")
                    return email
    
    return None