from backend.job_extractor import JobExtractor

def test_manually():
    print("Probando extractor de ofertas laborales...")
    extractor = JobExtractor()
    
    test_text = '''
    Vacante ofrecida por Microsoft
    Puesto: Desarrollador Python
    Requisitos: Python, Django, React
    Beneficios: Trabajo remoto, Seguro medico
    '''
    
    is_job, company = extractor.is_job_post(test_text)
    print(f"Es oferta de trabajo: {is_job}")
    print(f"Empresa: {company}")
    
    info = extractor.extract_job_info(test_text)
    print(f"Titulo: {info['title']}")
    print(f"Habilidades: {info['skills']}")
    print(f"Area: {info['area']}")
    
    return 0

if __name__ == "__main__":
    test_manually()
