# -*- coding: utf-8 -*-
"""
Modulo para extraer informacion estructurada de ofertas de trabajo desde texto.
"""
import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class JobExtractor:
    """Clase para extraer informacion estructurada de ofertas de trabajo."""
    
    def __init__(self):
        """Inicializa el extractor de ofertas de trabajo."""
        # Definir patrones para extraccion de informacion
        self.patterns = {
            'company': [
                r'(?:empresa|compania|company):\s*(.+?)(?:\n|$)',
                r'(?:en|at)\s+([A-Z][A-Za-z\s&.-]+)(?:\n|\s+busca)',
                r'^([A-Z][A-Za-z\s&.-]+)\s+(?:busca|solicita|requiere)',
                r'[Vv]acante(?:\s+[^.]*?)?ofrecida\s+por\s+[\'"]?([^\'\".,]+)[\'"]?',
                r'[Pp]ractica\s+laboral(?:\s+[^.]*?)?ofrecida\s+por\s+[\'"]?([^\'\".,]+)[\'"]?',
                r'[Pp]ractica\s+profesional(?:\s+[^.]*?)?ofrecida\s+por\s+[\'"]?([^\'\".,]+)[\'"]?'
            ],
            'title': [
                r'(?:puesto|cargo|posicion|titulo|position|job):\s*(.+?)(?:\n|$)',
                r'(?:busca|solicita)\s+(.+?)(?:\n|para|con)',
                r'(?:se\s+busca|buscamos)\s+(.+?)(?:\n|$)',
                r'[Vv]acante(?:\s+de|:)?\s+(.+?)(?:\n|en|para|$)'
            ],
            'skills': [
                r'(?:skills|habilidades|competencias|conocimientos):\s*(.+?)(?:\n\n|$)',
                r'(?:requiere|necesita|debe\s+tener):\s*(.+?)(?:\n\n|$)',
                r'(?:experiencia\s+en|conocimiento\s+de):\s*(.+?)(?:\n\n|$)',
                r'(?:requisitos|requirements):\s*(.+?)(?:\n\n|$)'
            ],
            'benefits': [
                r'(?:beneficios|ofrecemos|benefits):\s*(.+?)(?:\n\n|$)',
                r'(?:salario|sueldo|salary):\s*(.+?)(?:\n|$)',
                r'(?:modalidad|horario|schedule):\s*(.+?)(?:\n|$)',
                r'(?:se\s+ofrece|ofrecemos|we\s+offer):\s*(.+?)(?:\n\n|$)'
            ],
            'deadline': [
                r'(?:hasta|deadline|fecha\s+limite|cierra):\s*(.+?)(?:\n|$)',
                r'(?:aplicar\s+antes\s+del|apply\s+before):\s*(.+?)(?:\n|$)',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:hasta\s+el|valid\s+until)\s+(\d{1,2}\s+de\s+[a-z]+(?:\s+de\s+\d{4})?)'
            ]
        }
        
        # Mapeo de areas tecnologicas
        self.tech_areas = {
            'data-science': [
                'data scientist', 'machine learning', 'ml', 'ai', 'artificial intelligence',
                'python', 'r', 'sql', 'pandas', 'numpy', 'scikit-learn', 'tensorflow',
                'pytorch', 'data analysis', 'analytics', 'big data', 'spark', 'hadoop'
            ],
            'web-dev': [
                'web developer', 'frontend', 'backend', 'fullstack', 'javascript', 'js',
                'react', 'angular', 'vue', 'node.js', 'html', 'css', 'php', 'laravel',
                'django', 'flask', 'ruby', 'rails', 'asp.net'
            ],
            'mobile': [
                'mobile', 'android', 'ios', 'swift', 'kotlin', 'java', 'react native',
                'flutter', 'xamarin', 'app developer', 'mobile developer'
            ],
            'systems': [
                'devops', 'sysadmin', 'system administrator', 'infrastructure', 'cloud',
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'linux', 'unix',
                'networking', 'server', 'database administrator', 'dba'
            ],
            'cyber': [
                'cybersecurity', 'security', 'penetration testing', 'ethical hacking',
                'information security', 'infosec', 'soc', 'incident response',
                'vulnerability', 'firewall', 'encryption'
            ]
        }
    
    def is_job_post(self, text: str) -> Tuple[bool, Optional[str]]:
        """Determina si un texto corresponde a una oferta de trabajo.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            Tuple[bool, Optional[str]]: (es_oferta, empresa)
        """
        if not text:
            return False, None
            
        # Patrones de busqueda para ofertas laborales
        job_patterns = [
            r"[Vv]acante(?:\s+[^.]*?)?ofrecida\s+por\s+[\'\"]?([^\'\".,]+)[\'\"]?",
            r"[Pp]ractica\s+laboral(?:\s+[^.]*?)?ofrecida\s+por\s+[\'\"]?([^\'\".,]+)[\'\"]?",
            r"[Pp]ractica\s+profesional(?:\s+[^.]*?)?ofrecida\s+por\s+[\'\"]?([^\'\".,]+)[\'\"]?",
            r"[Oo]ferta\s+de\s+(?:trabajo|empleo|vacante)(?:\s+[^.]*?)?(?:en|por|para)\s+[\'\"]?([^\'\".,]+)[\'\"]?",
            r"[Ss]e\s+busca(?:\s+[^.]*?)para(?:\s+[^.]*?)en\s+[\'\"]?([^\'\".,]+)[\'\"]?",
            r"[Vv]acante(?:\s+de|:)?\s+(.+?)(?:\n|en|para)",
            r"[Oo]ferta\s+laboral",
            r"[Oo]portunidad\s+de\s+(?:trabajo|empleo)",
            r"[Ee]mpleo\s+(?:disponible|vacante)"
        ]
        
        for pattern in job_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                company = match.group(1).strip() if match.groups() else "Desconocida"
                return True, company
        
        return False, None
    
    def extract_job_info(self, text: str, caption: str = "") -> Dict:
        """Extrae informacion estructurada de una oferta de trabajo.
        
        Args:
            text (str): Texto OCR de la imagen
            caption (str): Texto del caption del post
            
        Returns:
            Dict: Informacion estructurada de la oferta
        """
        combined_text = f"{caption}\n{text}".lower()
        
        extracted = {
            'company': self.extract_company(combined_text),
            'title': self.extract_title(combined_text),
            'area': self.classify_area(combined_text),
            'skills': self.extract_skills(combined_text),
            'benefits': self.extract_benefits(combined_text),
            'deadline': self.extract_deadline(combined_text),
            'is_open': self.determine_status(combined_text)
        }
        
        return extracted
    
    def extract_company(self, text: str) -> Optional[str]:
        """Extrae el nombre de la empresa usando patrones.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            Optional[str]: Nombre de la empresa o None
        """
        for pattern in self.patterns['company']:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                company = matches[0].strip().title()
                if len(company) > 2 and len(company) < 100:
                    return company
        return None
    
    def extract_title(self, text: str) -> Optional[str]:
        """Extrae el titulo del puesto usando patrones.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            Optional[str]: Titulo del puesto o None
        """
        for pattern in self.patterns['title']:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                title = matches[0].strip().title()
                if len(title) > 3 and len(title) < 150:
                    return title
        return None
    
    def extract_skills(self, text: str) -> List[str]:
        """Extrae lista de habilidades del texto.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            List[str]: Lista de habilidades
        """
        skills = set()
        
        # Buscar secciones explicitas de habilidades
        for pattern in self.patterns['skills']:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for match in matches:
                # Dividir por delimitadores comunes
                skill_list = re.split(r'[,;•\-\n]', match)
                for skill in skill_list:
                    clean_skill = skill.strip()
                    if len(clean_skill) > 2 and len(clean_skill) < 50:
                        skills.add(clean_skill.title())
        
        # Buscar habilidades tecnicas comunes en todo el texto
        tech_skills = [
            'Python', 'Java', 'JavaScript', 'React', 'Angular', 'Vue', 'Node.js',
            'SQL', 'MongoDB', 'PostgreSQL', 'AWS', 'Docker', 'Kubernetes',
            'Machine Learning', 'Data Science', 'AI', 'Blockchain', 'Cybersecurity'
        ]
        
        for skill in tech_skills:
            if skill.lower() in text.lower():
                skills.add(skill)
        
        return list(skills)[:10]  # Limitar a 10 habilidades
    
    def extract_benefits(self, text: str) -> List[str]:
        """Extrae beneficios/ventajas del texto.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            List[str]: Lista de beneficios
        """
        benefits = set()
        
        for pattern in self.patterns['benefits']:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for match in matches:
                benefit_list = re.split(r'[,;•\-\n]', match)
                for benefit in benefit_list:
                    clean_benefit = benefit.strip()
                    if len(clean_benefit) > 3 and len(clean_benefit) < 100:
                        benefits.add(clean_benefit.title())
        
        return list(benefits)[:8]  # Limitar a 8 beneficios
    
    def extract_deadline(self, text: str) -> Optional[str]:
        """Extrae fecha limite de aplicacion.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            Optional[str]: Fecha limite o None
        """
        for pattern in self.patterns['deadline']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                deadline = matches[0].strip()
                if len(deadline) > 3:
                    return deadline
        return None
    
    def classify_area(self, text: str) -> str:
        """Clasifica la oferta en areas tecnologicas segun su contenido.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            str: Area tecnologica
        """
        area_scores = {}
        
        for area, keywords in self.tech_areas.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    score += 1
            area_scores[area] = score
        
        if area_scores and max(area_scores.values()) > 0:
            return max(area_scores, key=area_scores.get)
        
        return 'general'  # Area por defecto
    
    def determine_status(self, text: str) -> bool:
        """Determina si la oferta sigue abierta.
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            bool: True si esta abierta, False si esta cerrada
        """
        closed_indicators = [
            'cerrado', 'closed', 'completado', 'filled', 'no longer', 
            'ya no', 'position filled', 'cubierto', 'vacante cubierta'
        ]
        
        for indicator in closed_indicators:
            if indicator in text.lower():
                return False
        
        return True  # Por defecto asumir que esta abierta

def extract_job_data(ocr_text: str, caption: str = "") -> Dict:
    """Funcion de conveniencia para extraccion de datos de ofertas.
    
    Args:
        ocr_text (str): Texto OCR extraido de la imagen
        caption (str): Texto del caption del post
        
    Returns:
        Dict: Informacion estructurada de la oferta
    """
    extractor = JobExtractor()
    return extractor.extract_job_info(ocr_text, caption)
