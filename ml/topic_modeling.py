# -*- coding: utf-8 -*-
"""
Modulo para modelado de temas y analisis de texto de ofertas de trabajo.
"""
from typing import List, Dict, Any, Optional, Tuple
import re
import string
import pandas as pd
import numpy as np
from collections import Counter

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans

class TopicModeler:
    """Clase para modelado de temas en ofertas de trabajo."""
    
    def __init__(self, n_topics: int = 5, lang: str = "es") -> None:
        """Inicializa el modelador de temas.
        
        Args:
            n_topics: Numero de temas a identificar
            lang: Idioma del texto a analizar ('es' o 'en')
        """
        self.n_topics = n_topics
        self.lang = lang
        
        # Configurar vectorizador y modelo LDA
        self.vectorizer = CountVectorizer(
            max_df=0.95,  # ignorar terminos que aparecen en >95% de documentos
            min_df=2,     # ignorar terminos que aparecen en <2 documentos
            stop_words=self._get_stopwords(),
            ngram_range=(1, 2)  # unigramas y bigramas
        )
        
        self.lda = LatentDirichletAllocation(
            n_components=n_topics, 
            random_state=42,
            learning_method='online',
            max_iter=10
        )
        
        self.kmeans = KMeans(
            n_clusters=n_topics,
            random_state=42,
            n_init=10
        )
        
        self.tech_terms = self._load_tech_terms()
    
    def _get_stopwords(self) -> List[str]:
        """Obtiene stopwords para el idioma configurado.
        
        Returns:
            Lista de stopwords
        """
        # Stopwords en espanol
        spanish_stopwords = [
            "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con", "contra",
            "cual", "cuando", "de", "del", "desde", "donde", "durante", "e", "el", "ella",
            "ellas", "ellos", "en", "entre", "era", "erais", "eran", "eras", "eres", "es",
            "esa", "esas", "ese", "eso", "esos", "esta", "estaba", "estabais", "estaban",
            "estabas", "estad", "estada", "estadas", "estado", "estados", "estamos", "estando",
            "estar", "estaremos", "estará", "estarán", "estarás", "estaré", "estaréis",
            "estaría", "estaríais", "estaríamos", "estarían", "estarías", "estas", "este",
            "estemos", "esto", "estos", "estoy", "estuve", "estuviera", "estuvierais",
            "estuvieran", "estuvieras", "estuvieron", "estuviese", "estuvieseis", "estuviesen",
            "estuvieses", "estuvimos", "estuviste", "estuvisteis", "estuviéramos",
            "estuviésemos", "estuvo", "está", "estábamos", "estáis", "están", "estás", "esté",
            "estéis", "estén", "estés", "fue", "fuera", "fuerais", "fueran", "fueras", "fueron",
            "fuese", "fueseis", "fuesen", "fueses", "fui", "fuimos", "fuiste", "fuisteis",
            "fuéramos", "fuésemos", "ha", "habida", "habidas", "habido", "habidos", "habiendo",
            "habremos", "habrá", "habrán", "habrás", "habré", "habréis", "habría", "habríais",
            "habríamos", "habrían", "habrías", "habéis", "había", "habíais", "habíamos",
            "habían", "habías", "han", "has", "hasta", "hay", "haya", "hayamos", "hayan",
            "hayas", "hayáis", "he", "hemos", "hube", "hubiera", "hubierais", "hubieran",
            "hubieras", "hubieron", "hubiese", "hubieseis", "hubiesen", "hubieses", "hubimos",
            "hubiste", "hubisteis", "hubiéramos", "hubiésemos", "hubo", "la", "las", "le",
            "les", "lo", "los", "me", "mi", "mis", "mucho", "muchos", "muy", "más", "mí", "mía",
            "mías", "mío", "míos", "nada", "ni", "no", "nos", "nosotras", "nosotros", "nuestra",
            "nuestras", "nuestro", "nuestros", "o", "os", "otra", "otras", "otro", "otros",
            "para", "pero", "poco", "por", "porque", "que", "quien", "quienes", "qué", "se",
            "sea", "seamos", "sean", "seas", "seremos", "será", "serán", "serás", "seré",
            "seréis", "sería", "seríais", "seríamos", "serían", "serías", "seáis", "sido",
            "siendo", "sin", "sobre", "sois", "somos", "son", "soy", "su", "sus", "suya",
            "suyas", "suyo", "suyos", "sí", "también", "tanto", "te", "tendremos", "tendrá",
            "tendrán", "tendrás", "tendré", "tendréis", "tendría", "tendríais", "tendríamos",
            "tendrían", "tendrías", "tened", "tenemos", "tenga", "tengamos", "tengan", "tengas",
            "tengo", "tengáis", "tenida", "tenidas", "tenido", "tenidos", "teniendo", "tenéis",
            "tenía", "teníais", "teníamos", "tenían", "tenías", "ti", "tiene", "tienen",
            "tienes", "todo", "todos", "tu", "tus", "tuve", "tuviera", "tuvierais", "tuvieran",
            "tuvieras", "tuvieron", "tuviese", "tuvieseis", "tuviesen", "tuvieses", "tuvimos",
            "tuviste", "tuvisteis", "tuviéramos", "tuviésemos", "tuvo", "tuya", "tuyas", "tuyo",
            "tuyos", "tú", "un", "una", "uno", "unos", "vosotras", "vosotros", "vuestra",
            "vuestras", "vuestro", "vuestros", "y", "ya", "yo", "él", "éramos"
        ]
        
        # Stopwords especificas del dominio de ofertas laborales
        domain_stopwords = [
            "empresa", "compania", "oferta", "trabajo", "empleo", "vacante", "puesto",
            "ofrecemos", "buscamos", "requisitos", "perfil", "experiencia", "conocimientos",
            "habilidades", "skills", "competencias", "beneficios", "condiciones", "salario",
            "sueldo", "interesados", "favor", "enviar", "cv", "curriculum", "vitae", "email",
            "correo", "oportunidad", "importante", "incorporacion", "inmediata", "urgente",
            "jornada", "completa", "parcial", "horario", "flexible", "remoto", "presencial",
            "hibrido", "contrato", "indefinido", "temporal", "proyecto", "buscando", "solicita",
            "requiere", "necesita", "precisa", "valora", "valoramos", "valorable", "imprescindible",
            "deseado", "junior", "senior", "años", "minimo", "maximo", "preferible", "ideal"
        ]
        
        if self.lang == "es":
            return spanish_stopwords + domain_stopwords
        else:
            # Para inglés usar las stopwords de sklearn
            return "english"
    
    def _load_tech_terms(self) -> Dict[str, List[str]]:
        """Carga un diccionario de términos técnicos por categoría.
        
        Returns:
            Diccionario con categorías y términos relacionados
        """
        return {
            "programming": [
                "python", "java", "javascript", "typescript", "c#", "c++", "go", "golang", "rust",
                "php", "ruby", "swift", "kotlin", "scala", "perl", "bash", "shell", "r", "matlab",
                "cobol", "fortran", "ada", "lisp", "haskell", "erlang", "clojure", "groovy",
                "objective-c", "vba", "assembly", "dart", "julia", "powershell", "elixir"
            ],
            "web": [
                "html", "css", "javascript", "js", "jquery", "bootstrap", "sass", "less",
                "angular", "react", "vue", "ember", "backbone", "svelte", "next.js", "nuxt",
                "gatsby", "express", "node", "django", "flask", "rails", "spring", "laravel",
                "symfony", "asp.net", "jsp", "php", "webgl", "canvas", "svg", "typescript",
                "webpack", "babel", "rest", "graphql", "soap", "ajax", "responsive"
            ],
            "database": [
                "sql", "mysql", "postgresql", "postgres", "oracle", "sqlserver", "mongodb",
                "nosql", "redis", "cassandra", "couchdb", "sqlite", "mariadb", "dynamodb",
                "firebase", "neo4j", "elasticsearch", "solr", "influxdb", "timescaledb"
            ],
            "cloud": [
                "aws", "azure", "gcp", "google cloud", "cloud computing", "serverless",
                "lambda", "ec2", "s3", "rds", "dynamodb", "cloud formation", "terraform",
                "kubernetes", "k8s", "docker", "containers", "openshift", "heroku", "digital ocean",
                "vercel", "netlify", "cloudflare", "microservices", "iaas", "paas", "saas"
            ],
            "data_science": [
                "machine learning", "ml", "deep learning", "dl", "data mining", "big data", 
                "data warehouse", "etl", "data lake", "hadoop", "spark", "pandas", "numpy", 
                "scipy", "scikit-learn", "tensorflow", "pytorch", "keras", "theano", "caffe",
                "r", "tableau", "power bi", "data studio", "qlik", "d3.js", "matplotlib",
                "seaborn", "plotly", "bokeh", "nltk", "spacy", "gensim", "transformers", "bert"
            ],
            "devops": [
                "ci/cd", "jenkins", "github actions", "gitlab ci", "travis", "circle ci", 
                "terraform", "ansible", "puppet", "chef", "kubernetes", "k8s", "docker", "containers",
                "prometheus", "grafana", "elk", "monitoring", "logging", "datadog", "new relic",
                "sre", "site reliability", "infrastructure as code", "iac", "security"
            ],
            "mobile": [
                "android", "ios", "swift", "kotlin", "objective-c", "flutter", "react native",
                "xamarin", "cordova", "ionic", "mobile development", "app development",
                "responsive", "pwa", "progressive web apps", "appcelerator", "titanium"
            ]
        }
    
    def preprocess_text(self, texts: List[str]) -> List[str]:
        """Preprocesa los textos para análisis.
        
        Args:
            texts: Lista de textos a preprocesar
            
        Returns:
            Lista de textos preprocesados
        """
        if not texts:
            return []
        
        processed_texts = []
        for text in texts:
            if not text:
                processed_texts.append("")
                continue
            
            # Convertir a minúsculas
            text = text.lower()
            
            # Eliminar URLs
            text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
            
            # Eliminar emails
            text = re.sub(r'\S+@\S+', ' ', text)
            
            # Eliminar puntuación (excepto # para hashtags y + para C++)
            punctuation = string.punctuation.replace('#', '').replace('+', '')
            text = ''.join([c if c not in punctuation else ' ' for c in text])
            
            # Eliminar números
            text = re.sub(r'\b\d+\b', ' ', text)
            
            # Eliminar espacios múltiples
            text = re.sub(r'\s+', ' ', text).strip()
            
            processed_texts.append(text)
        
        return processed_texts
    
    def fit(self, texts: List[str]) -> None:
        """Entrena el modelo con los textos proporcionados.
        
        Args:
            texts: Lista de textos para entrenamiento
        """
        if not texts or all(not text for text in texts):
            raise ValueError("No hay textos válidos para entrenar el modelo")
        
        # Preprocesar textos
        processed_texts = self.preprocess_text(texts)
        
        # Vectorizar
        self.dtm = self.vectorizer.fit_transform(processed_texts)
        
        # Entrenar LDA
        self.lda.fit(self.dtm)
        
        # Entrenar K-means para clustering
        self.tfidf_vectorizer = TfidfVectorizer(
            max_df=0.95,
            min_df=2,
            stop_words=self._get_stopwords()
        )
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(processed_texts)
        self.kmeans.fit(self.tfidf_matrix)
    
    def get_topics(self, n_terms: int = 10) -> List[Dict[str, Any]]:
        """Obtiene los términos más relevantes para cada tema.
        
        Args:
            n_terms: Número de términos a mostrar por tema
            
        Returns:
            Lista de temas con sus términos más relevantes
        """
        if not hasattr(self, 'vectorizer') or not hasattr(self, 'lda'):
            raise ValueError("El modelo no ha sido entrenado todavía. Ejecute fit() primero.")
        
        features = self.vectorizer.get_feature_names_out()
        topics = []
        
        for topic_idx, topic in enumerate(self.lda.components_):
            top_features_idx = topic.argsort()[:-n_terms - 1:-1]
            top_features = [features[i] for i in top_features_idx]
            topic_weight = topic.sum() / self.lda.components_.sum(axis=1).mean()
            
            topics.append({
                "id": topic_idx,
                "terms": top_features,
                "weight": float(topic_weight),
                "label": self._generate_topic_label(top_features)
            })
            
        return topics
    
    def classify_text(self, text: str) -> Dict[str, Any]:
        """Clasifica un texto en uno de los temas identificados.
        
        Args:
            text: Texto a clasificar
            
        Returns:
            Información del tema asignado
        """
        if not hasattr(self, 'vectorizer') or not hasattr(self, 'lda'):
            raise ValueError("El modelo no ha sido entrenado todavía. Ejecute fit() primero.")
        
        # Preprocesar texto
        processed_text = self.preprocess_text([text])[0]
        
        # Vectorizar
        text_vector = self.vectorizer.transform([processed_text])
        
        # Obtener distribución de temas
        topic_distribution = self.lda.transform(text_vector)[0]
        
        # Tema dominante
        dominant_topic = topic_distribution.argmax()
        
        # Obtener todos los temas
        topics = self.get_topics()
        
        return {
            "dominant_topic": dominant_topic,
            "topic_distribution": {i: float(score) for i, score in enumerate(topic_distribution)},
            "topic_terms": topics[dominant_topic]["terms"],
            "topic_label": topics[dominant_topic]["label"]
        }
    
    def cluster_texts(self, texts: List[str]) -> Dict[str, Any]:
        """Agrupa textos similares mediante clustering.
        
        Args:
            texts: Lista de textos a agrupar
            
        Returns:
            Información de los clusters identificados
        """
        if not hasattr(self, 'tfidf_vectorizer') or not hasattr(self, 'kmeans'):
            raise ValueError("El modelo no ha sido entrenado todavía. Ejecute fit() primero.")
        
        # Preprocesar textos
        processed_texts = self.preprocess_text(texts)
        
        # Vectorizar
        text_vectors = self.tfidf_vectorizer.transform(processed_texts)
        
        # Predecir clusters
        clusters = self.kmeans.predict(text_vectors)
        
        # Agrupar textos por cluster
        clustered_texts = {}
        for i, cluster_id in enumerate(clusters):
            cluster_id = int(cluster_id)
            if cluster_id not in clustered_texts:
                clustered_texts[cluster_id] = []
            clustered_texts[cluster_id].append(texts[i])
        
        return {
            "n_clusters": self.kmeans.n_clusters,
            "cluster_assignments": clusters.tolist(),
            "clustered_texts": clustered_texts
        }
    
    def _generate_topic_label(self, terms: List[str]) -> str:
        """Genera una etiqueta descriptiva para un tema basada en sus términos.
        
        Args:
            terms: Términos más relevantes del tema
            
        Returns:
            Etiqueta descriptiva del tema
        """
        # Buscar coincidencias con categorías técnicas
        category_matches = {}
        for category, category_terms in self.tech_terms.items():
            matches = sum(1 for term in terms if term in category_terms)
            if matches > 0:
                category_matches[category] = matches
        
        if category_matches:
            # Ordenar por número de coincidencias
            top_category = max(category_matches.items(), key=lambda x: x[1])[0]
            
            # Mapeo de categorías a etiquetas legibles
            category_labels = {
                "programming": "Desarrollo de Software",
                "web": "Desarrollo Web",
                "database": "Bases de Datos",
                "cloud": "Cloud Computing",
                "data_science": "Data Science",
                "devops": "DevOps/SRE",
                "mobile": "Desarrollo Móvil"
            }
            
            return category_labels.get(top_category, top_category.replace('_', ' ').title())
        
        # Si no hay coincidencias claras, usar los dos primeros términos
        return " & ".join(terms[:2]).title()


class SkillExtractor:
    """Clase para extraer habilidades técnicas de textos de ofertas laborales."""
    
    def __init__(self, lang: str = "es") -> None:
        """Inicializa el extractor de habilidades.
        
        Args:
            lang: Idioma del texto a analizar ('es' o 'en')
        """
        self.lang = lang
        self.skill_patterns = self._compile_skill_patterns()
        self.tech_skills = self._load_tech_skills()
    
    def _compile_skill_patterns(self) -> List[Tuple[str, re.Pattern]]:
        """Compila patrones regex para identificar secciones de habilidades.
        
        Returns:
            Lista de tuplas (nombre_sección, patrón_compilado)
        """
        patterns = []
        
        # Patrones en español
        if self.lang == "es":
            patterns.extend([
                ("requisitos", re.compile(r'(?:requisitos|requerimientos|skills requeridos|perfil requerido)[:.\-]?\s*([\s\S]+?)(?:\n\n|\n[A-Z]|$)', re.IGNORECASE)),
                ("habilidades", re.compile(r'(?:habilidades|competencias|conocimientos|skills|tecnologías)[:.\-]?\s*([\s\S]+?)(?:\n\n|\n[A-Z]|$)', re.IGNORECASE)),
                ("experiencia", re.compile(r'(?:experiencia|exp\.)[:.\-]?\s*([\s\S]+?)(?:\n\n|\n[A-Z]|$)', re.IGNORECASE)),
                ("valoramos", re.compile(r'(?:valoramos|se valora|valorable|deseable)[:.\-]?\s*([\s\S]+?)(?:\n\n|\n[A-Z]|$)', re.IGNORECASE)),
                ("imprescindible", re.compile(r'(?:imprescindible|requerido|obligatorio)[:.\-]?\s*([\s\S]+?)(?:\n\n|\n[A-Z]|$)', re.IGNORECASE))
            ])
        # Patrones en inglés
        else:
            patterns.extend([
                ("requirements", re.compile(r'(?:requirements|required skills|profile)[:.\-]?\s*([\s\S]+?)(?:\n\n|\n[A-Z]|$)', re.IGNORECASE)),
                ("skills", re.compile(r'(?:skills|competencies|knowledge|technologies)[:.\-]?\s*([\s\S]+?)(?:\n\n|\n[A-Z]|$)', re.IGNORECASE)),
                ("experience", re.compile(r'(?:experience|exp\.)[:.\-]?\s*([\s\S]+?)(?:\n\n|\n[A-Z]|$)', re.IGNORECASE)),
                ("valued", re.compile(r'(?:valued|we value|desirable|nice to have)[:.\-]?\s*([\s\S]+?)(?:\n\n|\n[A-Z]|$)', re.IGNORECASE)),
                ("mandatory", re.compile(r'(?:mandatory|required|must have)[:.\-]?\s*([\s\S]+?)(?:\n\n|\n[A-Z]|$)', re.IGNORECASE))
            ])
        
        return patterns
    
    def _load_tech_skills(self) -> Dict[str, List[str]]:
        """Carga un diccionario de habilidades técnicas por categoría.
        
        Returns:
            Diccionario con categorías y habilidades relacionadas
        """
        return {
            "programming_languages": [
                "python", "java", "javascript", "typescript", "c#", "c++", "go", "golang", "rust",
                "php", "ruby", "swift", "kotlin", "scala", "perl", "bash", "shell", "r", "matlab",
                "cobol", "fortran", "ada", "lisp", "haskell", "erlang", "clojure", "groovy",
                "objective-c", "vba", "assembly", "dart", "julia", "powershell", "elixir"
            ],
            "web_technologies": [
                "html", "css", "javascript", "jquery", "bootstrap", "sass", "less",
                "angular", "react", "vue", "ember", "backbone", "svelte", "next.js", "nuxt",
                "gatsby", "express", "node", "django", "flask", "rails", "spring", "laravel",
                "symfony", "asp.net", "jsp", "php", "webgl", "canvas", "svg", "typescript",
                "webpack", "babel", "rest", "graphql", "soap", "ajax", "responsive", "spa"
            ],
            "databases": [
                "sql", "mysql", "postgresql", "postgres", "oracle", "sqlserver", "mongodb",
                "nosql", "redis", "cassandra", "couchdb", "sqlite", "mariadb", "dynamodb",
                "firebase", "neo4j", "elasticsearch", "solr", "influxdb", "timescaledb"
            ],
            "cloud_platforms": [
                "aws", "azure", "gcp", "google cloud", "serverless", "lambda", "ec2", "s3",
                "rds", "cloud formation", "terraform", "kubernetes", "k8s", "docker", 
                "openshift", "heroku", "digital ocean", "vercel", "netlify", "cloudflare"
            ],
            "data_science": [
                "machine learning", "ml", "deep learning", "neural networks", "data mining", 
                "big data", "data warehouse", "etl", "data lake", "hadoop", "spark", "pandas", 
                "numpy", "scipy", "scikit-learn", "tensorflow", "pytorch", "keras", "theano", 
                "caffe", "tableau", "power bi", "data studio", "qlik", "d3.js", "matplotlib",
                "seaborn", "plotly", "bokeh", "nltk", "spacy", "gensim", "transformers", "bert"
            ],
            "devops": [
                "ci/cd", "jenkins", "github actions", "gitlab ci", "travis", "circle ci", 
                "terraform", "ansible", "puppet", "chef", "kubernetes", "k8s", "docker",
                "prometheus", "grafana", "elk", "monitoring", "logging", "datadog", "new relic"
            ],
            "mobile": [
                "android", "ios", "swift", "kotlin", "objective-c", "flutter", "react native",
                "xamarin", "cordova", "ionic", "mobile development", "pwa", "progressive web apps"
            ],
            "security": [
                "security", "cybersecurity", "infosec", "penetration testing", "pentest",
                "vulnerabilities", "firewall", "encryption", "oauth", "jwt", "authentication",
                "authorization", "idp", "identity provider", "sso", "single sign-on", "iam"
            ],
            "methodologies": [
                "agile", "scrum", "kanban", "lean", "waterfall", "tdd", "bdd", "xp", 
                "extreme programming", "devops", "itil", "sprint", "product owner", "scrum master"
            ],
            "soft_skills": [
                "teamwork", "communication", "leadership", "problem solving", "critical thinking",
                "creativity", "time management", "adaptability", "flexibility", "resilience",
                "trabajo en equipo", "comunicacion", "liderazgo", "resolucion de problemas"
            ]
        }
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """Extrae secciones relevantes del texto que pueden contener habilidades.
        
        Args:
            text: Texto de la oferta laboral
            
        Returns:
            Diccionario con secciones identificadas
        """
        if not text:
            return {}
        
        sections = {}
        
        for section_name, pattern in self.skill_patterns:
            matches = pattern.findall(text)
            if matches:
                sections[section_name] = matches[0].strip()
        
        return sections
    
    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extrae habilidades técnicas del texto.
        
        Args:
            text: Texto de la oferta laboral
            
        Returns:
            Diccionario con habilidades agrupadas por categoría
        """
        if not text:
            return {}
        
        # Convertir a minúsculas
        text = text.lower()
        
        # Extraer secciones relevantes
        sections = self.extract_sections(text)
        
        # Si no se encontraron secciones, usar todo el texto
        if not sections:
            sections = {"full_text": text}
        
        # Inicializar diccionario para las habilidades detectadas
        skills = {category: [] for category in self.tech_skills.keys()}
        
        # Buscar skills en cada sección o en todo el texto
        for section_text in sections.values():
            for category, category_skills in self.tech_skills.items():
                for skill in category_skills:
                    # Buscar la habilidad como palabra completa
                    if re.search(rf'\b{re.escape(skill)}\b', section_text):
                        skills[category].append(skill)
        
        # Eliminar duplicados y ordenar
        for category in skills:
            skills[category] = sorted(list(set(skills[category])))
        
        # Eliminar categorías vacías
        skills = {k: v for k, v in skills.items() if v}
        
        return skills
    
    def get_top_skills(self, text: str, limit: int = 10) -> List[str]:
        """Obtiene las principales habilidades técnicas del texto.
        
        Args:
            text: Texto de la oferta laboral
            limit: Número máximo de habilidades a devolver
            
        Returns:
            Lista de habilidades identificadas
        """
        # Extraer todas las habilidades
        skills_by_category = self.extract_skills(text)
        
        # Aplanar la lista de habilidades
        all_skills = []
        for skills in skills_by_category.values():
            all_skills.extend(skills)
        
        # Limitar y devolver resultado
        return sorted(list(set(all_skills)))[:limit]

def analyze_job_text(text: str) -> Dict[str, Any]:
    """Analiza un texto de oferta laboral y extrae información estructurada.
    
    Args:
        text: Texto de la oferta laboral
        
    Returns:
        Diccionario con análisis del texto
    """
    # Extraer habilidades
    skill_extractor = SkillExtractor()
    skills = skill_extractor.get_top_skills(text)
    skill_sections = skill_extractor.extract_sections(text)
    
    # Crear modelo de temas si hay suficiente texto
    topic_info = {}
    if len(text) > 100:
        try:
            # Crear y entrenar modelo con un solo texto
            # (en un caso real, sería mejor entrenar con múltiples textos)
            topic_modeler = TopicModeler(n_topics=1)
            topic_modeler.fit([text])
            topic_info = topic_modeler.get_topics(n_terms=5)[0]
        except (ValueError, IndexError):
            # Si hay un error, simplemente ignoramos el análisis de temas
            pass
    
    return {
        "skills": skills,
        "skill_sections": skill_sections,
        "topic": topic_info.get("terms", []) if topic_info else [],
        "topic_label": topic_info.get("label", "") if topic_info else ""
    }

def get_similar_jobs(jobs_data: List[Dict[str, Any]], target_job_index: int, 
                    n: int = 3) -> List[int]:
    """Encuentra ofertas similares a la oferta objetivo.
    
    Args:
        jobs_data: Lista de diccionarios con datos de ofertas
        target_job_index: Índice de la oferta objetivo
        n: Número de ofertas similares a retornar
        
    Returns:
        Lista de índices de ofertas similares
    """
    if not jobs_data or target_job_index >= len(jobs_data):
        return []
    
    # Extraer textos de las ofertas
    texts = [job.get("description", "") for job in jobs_data]
    
    # Inicializar vectorizador TF-IDF
    vectorizer = TfidfVectorizer(
        max_df=0.9, 
        min_df=2, 
        stop_words="english" if jobs_data[0].get("language") == "en" else "spanish"
    )
    
    # Generar matriz TF-IDF
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError:
        # Si hay un error (por ejemplo, todos los documentos son vacíos)
        return []
    
    # Calcular similitud coseno entre la oferta objetivo y todas las demás
    from sklearn.metrics.pairwise import cosine_similarity
    target_vector = tfidf_matrix[target_job_index:target_job_index+1]
    cosine_similarities = cosine_similarity(target_vector, tfidf_matrix).flatten()
    
    # Obtener índices de las ofertas más similares (excluyendo la oferta objetivo)
    similar_indices = cosine_similarities.argsort()[:-n-2:-1]
    similar_indices = [idx for idx in similar_indices if idx != target_job_index]
    
    return similar_indices[:n]
# Añadir estas herramientas al diccionario tech_skills
"power_automate": ["power automate", "power platform", "microsoft power platform", "flow", "microsoft flow", 
                  "robotic process automation", "rpa", "power automate desktop"],
"low_code": ["low code", "no code", "adonis", "outsystems", "mendix", "powerapps", 
             "appian", "process automation", "workflow automation", "automatización de procesos"],
"university": ["trabajo de graduación", "práctica profesional", "pasantía", "estudiante", 
               "tesis", "proyecto final", "utp", "universidad"]
