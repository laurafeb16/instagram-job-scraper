# -*- coding: utf-8 -*-
import re

def is_job_post(caption):
    """Determina si un post es una oferta de trabajo o práctica profesional.
    
    Args:
        caption (str): El texto del caption del post de Instagram
        
    Returns:
        tuple: (is_job, company) donde is_job es un booleano que indica si es oferta,
               y company es el nombre de la empresa si se encontró
    """
    if not caption:
        return False, None
    
    # Patrones de búsqueda para ofertas laborales
    job_patterns = [
        r"[Vv]acante(?:\s+[^.]*?)?ofrecida\s+por\s+['\"]?([^'\".,]+)['\"]?",
        r"[Pp]ráctica\s+laboral(?:\s+[^.]*?)?ofrecida\s+por\s+['\"]?([^'\".,]+)['\"]?",
        r"[Pp]ráctica\s+profesional(?:\s+[^.]*?)?ofrecida\s+por\s+['\"]?([^'\".,]+)['\"]?",
        r"[Oo]ferta\s+de\s+(?:trabajo|empleo|vacante)(?:\s+[^.]*?)?(?:en|por|para)\s+['\"]?([^'\".,]+)['\"]?",
        r"[Ss]e\s+busca(?:\s+[^.]*?)para(?:\s+[^.]*?)en\s+['\"]?([^'\".,]+)['\"]?"
    ]
    
    for pattern in job_patterns:
        match = re.search(pattern, caption)
        if match:
            company = match.group(1).strip() if match.groups() else "Desconocida"
            return True, company
    
    return False, None