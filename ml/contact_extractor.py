# -*- coding: utf-8 -*-
"""
Módulo para extraer información de contacto de ofertas laborales.
"""
import re
from typing import Dict, Optional, List, Any
import json

class ContactExtractor:
    """Extrae información de contacto de textos de ofertas laborales."""
    
    def __init__(self) -> None:
        """Inicializa el extractor de contacto."""
        # Patrones para extraer información de contacto
        self.patterns = {
            "name": [
                r"[Cc]ontacto:?\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
                r"(?:[Aa]tención|[Aa]ttn):\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
                r"(?:[Cc]on)?[Tt]actar\s+(?:a|con)?\s+([A-Z][a-z]+\s+[A-Z][a-z]+)"
            ],
            "position": [
                r"[Cc]ontacto:.*?\|\s*([^,\n]+)",
                r"[Cc]argo:?\s+([^,\n]+)",
                r"[Pp]uesto:?\s+([^,\n]+)"
            ],
            "email": [
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                r"[Cc]orreo:?\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                r"[Ee]mail:?\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
            ],
            "phone": [
                r"[Tt]eléfono:?\s+(\+?[0-9()\s-]{7,})",
                r"[Cc]el(?:ular)?:?\s+(\+?[0-9()\s-]{7,})",
                r"[Ll]lamar\s+(?:al|a)?\s+(\+?[0-9()\s-]{7,})"
            ],
            "website": [
                r"(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\.[a-zA-Z]{2,}(?:/\S*)?)",
                r"[Ss]itio\s+[Ww]eb:?\s+((?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/\S*)?)",
                r"[Pp]ágina:?\s+((?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/\S*)?)"
            ],
            "application_instructions": [
                r"[Ii]nteresados[^.]*enviar[^.]*a:?\s+([^.\n]+)",
                r"[Ee]nviar\s+(?:[Hh]oja\s+de\s+[Vv]ida|[Cc][Vv]|[Cc]urriculum)[^.]*a:?\s+([^.\n]+)",
                r"[Pp]ostular[^.]*a\s+través\s+de:?\s+([^.\n]+)"
            ]
        }
    
    def extract_contact_info(self, text: str) -> Dict[str, Any]:
        """Extrae información de contacto del texto.
        
        Args:
            text: Texto de la oferta laboral
            
        Returns:
            Diccionario con información de contacto
        """
        contact_info = {
            "name": None,
            "position": None,
            "email": None,
            "phone": None,
            "website": None,
            "application_instructions": None
        }
        
        # Buscar cada tipo de información
        for field, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    # Para email y website pueden haber múltiples
                    if field in ["email", "website"]:
                        contact_info[field] = matches
                        break
                    else:
                        contact_info[field] = matches[0].strip()
                        break
        
        # Limpiar y normalizar teléfonos
        if contact_info["phone"]:
            contact_info["phone"] = self._normalize_phone(contact_info["phone"])
        
        return contact_info
    
    def _normalize_phone(self, phone: str) -> str:
        """Normaliza un número de teléfono.
        
        Args:
            phone: Número de teléfono en formato variable
            
        Returns:
            Número de teléfono normalizado
        """
        # Eliminar caracteres no numéricos excepto + inicial
        if phone.startswith('+'):
            normalized = '+' + re.sub(r'[^\d]', '', phone[1:])
        else:
            normalized = re.sub(r'[^\d]', '', phone)
        
        return normalized

def extract_contact(text: str) -> Dict[str, Any]:
    """Función auxiliar para extraer información de contacto.
    
    Args:
        text: Texto de la oferta laboral
        
    Returns:
        Diccionario con información de contacto
    """
    extractor = ContactExtractor()
    return extractor.extract_contact_info(text)

# Prueba simple
if __name__ == "__main__":
    sample_text = '''
    Práctica profesional ofrecida por Empresa S.A.
    Contacto: Jane Doe | Directora de Recursos Humanos
    Teléfono: +(507) 652-9875
    Interesados enviar Hoja de Vida a: jdoe@empresasa.com
    '''
    
    contact_info = extract_contact(sample_text)
    print(json.dumps(contact_info, indent=2))
